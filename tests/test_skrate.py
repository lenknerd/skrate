"""Tests for the main skrate application."""
import datetime
import itertools
import json
import logging
import os
import random
from typing import Any, Generator, List

import pytest
from flask.ctx import AppContext
from flask.testing import FlaskClient

import context
from skrate import game_logic, models, server, tricks

# Test database fully separate from production
_TEST_DB_URI = "postgresql://skrate_test_user:skrate_test_password@localhost:5432/skrate_test_db"


@pytest.fixture
def client(monkeypatch: Any) -> Generator[FlaskClient, None, None]:
    """Client test fixture for flask app testing - fake client, test database.
    
    Args:
        monkeypatch: monkeypatch object passed around by pytest

    """
    monkeypatch.setattr(server, "_SQLALCHEMY_DATABASE_URI", _TEST_DB_URI)
    monkeypatch.setattr(server, "_TESTING", True)
    monkeypatch.setattr(server, "_LOG_LEVEL", logging.WARN)

    server.init_app(False)  # test with debug mode off (False)

    # In the test database, drop and re-create tables for clean state
    models.drop_db_tables(server.app)
    models.create_db_tables(server.app)

    # And upload trick definitions
    tricks.update_tricks_table(server.app)

    # Return client for test runs
    with server.app.test_client() as client:
        yield client

    # Finally wipe tables again to leave in clean state
    models.drop_db_tables(server.app)


@pytest.fixture
def fix_rand_uniform_sequence(monkeypatch: Any) -> List[float]:
    """Instead of random.uniform returning between vals, always return above const

    Args:
        monkeypatch: monkeypatch object passed around by pytest

    """
    # Holder for fixed sequence of randoms for testing, cycle back to start at end
    _vals_sequence = [0.0]
    _i = 0

    def fix_rand_value(lo_bound: float, up_bound: float) -> float:
        """Patch function that returns some random (pull from def sequence)

        Args:
            lo_bound: lower bound from which to choose rand
            up_bound: upper bound from which to choose rand

        """
        # In this patch test function for determinism, just return lower bound
        nonlocal _i, _vals_sequence
        v_return = _vals_sequence[_i]
        _i = (_i + 1) % len(_vals_sequence)
        return v_return

    monkeypatch.setattr(random, "uniform", fix_rand_value)
    # Return this so the test function can modify the sequence if needed
    return _vals_sequence


def _game_turn(trick_id: int, landed: bool, user_name: str, game_id: int,
               client: FlaskClient, server_app_context: AppContext) -> None:
    """Have a player try a trick as part of a game.

    Args:
        trick_id: id of the trick
        landed: whether or not they landed the trick
        user_name: attempting player
        game_id: what game this is a part of
        client: test client
        server_app_context: test server context

    """
    user_att = models.Attempt(trick_id=trick_id,
                              game_id=game_id,
                              user=user_name,
                              landed=landed,
                              time_of_attempt=datetime.datetime.utcnow())
    models.db.session.add(user_att)
    models.db.session.commit()


class TestSkrate:

    def test_init_and_bail(self, client: FlaskClient) -> None:
        """Test a successful attempt leads to incrememnt on tricks stats.

        Args:
            client: the test fixture client

        """
        test_user = "johndoe"
        test_trick_name = "Kickflip"
        with server.app.app_context():
            test_trick_id = models.Trick.query \
                    .filter_by(name=test_trick_name).one().id

        # Log in and check initial load page, plus session
        rv = client.get("/%s" % test_user)
        assert rv.status_code == 200
        assert server.session["user"] == test_user
        html_str = str(rv.data)
        assert "trick%s" % test_trick_id in html_str  # should be this many ids
        assert "Heelflip Bigspin" in html_str  # just one of the later ones

        # Attempt a trick, miss it, see that stat changes when update view
        rv = client.get("/attempt/%s/false/false" % test_trick_id)
        assert rv.status_code == 200

        rv_data = rv.get_json()
        assert rv_data["update_game"] == False  # because we're not in a game
        assert rv_data["update_all_tricks"] == False
        assert rv_data["update_tricks"] == [test_trick_id]

        rv = client.get("/get_single_trick_stats/%s" % test_trick_id)
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert "Attempts: 1 " in html_str
        assert "Lands: 0<" in html_str

        # Ensure it's in the database (bit redundant but good at least once)
        db_atts = models.Attempt.query.all()
        assert len(db_atts) == 1
        assert db_atts[0].user == test_user
        assert db_atts[0].trick.id == test_trick_id
        assert db_atts[0].trick.name == test_trick_name

    def test_land(self, client: FlaskClient) -> None:
        """Test landing a trick.

        Args:
            client: the client test fixture

        """
        test_user = "janedoe"
        test_trick_name = "Ollie"
        with server.app.app_context():
            test_trick_id = models.Trick.query \
                    .filter_by(name=test_trick_name).one().id

        rv = client.get("/%s" % test_user)

        # Attempt a trick, make it, see the stat changes when update view
        rv = client.get("/attempt/%s/true/false" % test_trick_id)
        assert rv.status_code == 200

        rv_data = rv.get_json()
        assert rv_data["update_game"] == False  # because we're not in a game
        assert rv_data["update_all_tricks"] == False
        assert rv_data["update_tricks"] == [test_trick_id]

        rv = client.get("/get_single_trick_stats/%s" % test_trick_id)
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert "Attempts: 1 " in html_str
        assert "Lands: 1<" in html_str

        # Ensure it's in the database (bit redundant but good at least once)
        db_atts = models.Attempt.query.all()
        assert len(db_atts) == 1
        assert db_atts[0].user == test_user
        assert db_atts[0].trick.id == test_trick_id
        assert db_atts[0].trick.name == test_trick_name

    def test_game_logic(self, client: FlaskClient) -> None:
        """Test game logic where opponent wins, just back-end logic not view

        Args:
            client: the client test fixture

        """
        test_user = "janedoe"
        n_wins_first = 3
        n_drops_next = 5
        test_tricks = []  # List[models.Trick]
        with server.app.app_context() as server_context:
            # Just some trick id's to use
            test_tricks = models.Trick.query.limit(n_wins_first + n_drops_next + 1)

            # Declare game object
            game = models.Game(attempts=[], user=test_user)
            models.db.session.add(game)
            models.db.session.commit()

            # Use lands first 3, opp misses all, should be opp: SKA
            for trick in test_tricks[0:n_wins_first]:
                # Note these call model functions not client turns, because client attempt
                # would also automatically choose oppoenent response, we want to test that
                _game_turn(trick.id, True, test_user, game.id, client, server_context)
                _game_turn(trick.id, False, "past_" + test_user, game.id, client, server_context)

            models.db.session.add(game)
            models.db.session.commit()  # re-sync attempts
            game_state = models.get_game_state(game.attempts, test_user)
            assert game_state.user_score == 0
            assert game_state.opponent_score == n_wins_first

            # Now if both miss one, expect no score change. Use last trick ID
            _game_turn(test_tricks[-1].id, False, test_user, game.id, client, server_context)
            _game_turn(test_tricks[-1].id, False, "past_" + test_user, game.id, client, server_context)

            # Now if both land one, expect no score change. Use last trick ID
            _game_turn(test_tricks[-1].id, True, test_user, game.id, client, server_context)
            _game_turn(test_tricks[-1].id, True, "past_" + test_user, game.id, client, server_context)

            models.db.session.add(game)
            models.db.session.commit()  # re-sync attempts
            game_state = models.get_game_state(game.attempts, test_user)
            assert game_state.user_score == 0
            assert game_state.opponent_score == n_wins_first

            # A one-off repeat should count as fail, turn over priority to opponent
            _game_turn(test_tricks[0].id, False, test_user, game.id, client, server_context)

            # Now opponent lands the next n_drops_next (5, enough to win)
            for trick in test_tricks[n_wins_first:n_wins_first + n_drops_next]:
                _game_turn(trick.id, True, "past_" + test_user, game.id, client, server_context)
                _game_turn(trick.id, False, test_user, game.id, client, server_context)

            models.db.session.add(game)
            models.db.session.commit()  # re-sync attempts
            game_state = models.get_game_state(game.attempts, test_user)
            assert game_state.user_score == n_drops_next
            assert game_state.opponent_score == n_wins_first
            assert game_state.status_feed[-1].msg_text == "[Turn 20]: Past you wins!"

    def test_trick_choice(self, client: FlaskClient, fix_rand_uniform_sequence: Any) -> None:
        """Test function to choose most likely trick for user.
        
        Args:
            client: the test client
            fix_rand_uniform: test fixture for value returned instead of uniform rand

        """
        # Always take the most likely next trick, don't randomize
        fix_rand_uniform_sequence[0] = 1.0

        test_user = "janedoe"
        test_trick_name = "Ollie"
        with server.app.app_context() as server_app:
            test_trick_id = models.Trick.query \
                    .filter_by(name=test_trick_name).one().id

        rv = client.get("/%s" % test_user)

        # Land a trick twice (needs to be more than once ago to consider)
        for i in range(2):
            rv = client.get("/attempt/%s/true/false" % test_trick_id)

        # Check that it's now most likely trick, no tricks prohibited
        best_trick = game_logic.game_trick_choice(server.app, test_user, [], models.db)
        assert best_trick == test_trick_id

    def test_client_game(self, client: FlaskClient, fix_rand_uniform_sequence: Any) -> None:
        """Test game progress from end-to-end client standpoint.

        Args:
            client: the test client

        """
        # Always take the most likely next trick, don't randomize
        fix_rand_uniform_sequence[0] = 1.0

        test_user = "janedoe"
        with server.app.app_context() as server_app:
            test_tricks = models.Trick.query.all()

        rv = client.get("/%s" % test_user)

        # First land a trick twice before starting game, to init success rate for one
        for i in range(2):
            rv = client.get("/attempt/%s/true/false" % test_tricks[0].id)
            assert rv.status_code == 200

        # Start a game
        rv = client.get("/start_game")
        assert rv.status_code == 200

        # Check if we get the current game based on id, no attempts yet
        game_id = server.session["game_id"]
        game = models.Game.query.filter_by(id=game_id).one()
        assert len(game.attempts) == 0

        rv_data = rv.get_json()
        assert rv_data["update_game"] == True
        assert rv_data["update_all_tricks"] == False
        assert len(rv_data["update_tricks"]) == 0

        # Now test that game update window includes the start instruction message
        rv = client.get("/get_latest_game_view")
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert "Starting game!" in html_str

        # Land a trick, confirm that the response includes instruction to update game window
        rv = client.get("/attempt/%s/true/false" % test_tricks[0].id)
        assert rv.status_code == 200
        rv_data = rv.get_json()
        assert rv_data["update_game"] == True

        # Opponent should have responded with a land since init'd odds to 1 on this
        rv = client.get("/get_latest_game_view")
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert "Past you matched the challenge." in html_str

        # Now attempt a new trick not seen before by opponent and land it
        rv = client.get("/attempt/%s/true/false" % test_tricks[1].id)
        assert rv.status_code == 200
        rv_data = rv.get_json()
        assert rv_data["update_game"] == True

        # See that opponent now responded with a miss, never saw this trick before
        rv = client.get("/get_latest_game_view")
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert "Missed challenge! Past you " in html_str

