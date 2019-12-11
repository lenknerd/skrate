"""Tests for the main skrate application."""
import datetime
import itertools
import json
import logging
import os
from typing import Any

import pytest
from flask.testing import FlaskClient

import context
from skrate import server
from skrate import models
from skrate import tricks


# Test database fully separate from production
_TEST_DB_URI = "postgresql://skrate_test_user:skrate_test_password@localhost:5432/skrate_test_db"


@pytest.fixture
def client(monkeypatch: Any) -> FlaskClient:
    """Client test fixture for flask app testing - fake client, test database."""

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
        assert rv_data["update_tricks"] == [str(test_trick_id)]

        rv = client.get("/get_single_trick_view/%s" % test_trick_id)
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert test_trick_name in html_str
        assert "Attempts: 1 " in html_str
        assert "Lands: 0 " in html_str

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
        assert rv_data["update_tricks"] == [str(test_trick_id)]

        rv = client.get("/get_single_trick_view/%s" % test_trick_id)
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert test_trick_name in html_str
        assert "Attempts: 1 " in html_str
        assert "Lands: 1 " in html_str

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
        with server.app.app_context():
            # Just some trick id's to use
            test_tricks = models.Trick.query.limit(n_wins_first + n_drops_next + 1)

            # Declare game object
            game = models.Game(attempts=[], complete=False, user=test_user)
            models.db.session.add(game)
            models.db.session.commit()

            # Use lands first 3, opp misses all, should be opp: SKA
            for trick in test_tricks[0:n_wins_first]:
                user_att = models.Attempt(trick_id=trick.id,
                                          game_id=game.id,
                                          user=test_user,
                                          landed=True,
                                          time_of_attempt=datetime.datetime.utcnow())
                models.db.session.add(user_att)

                oppo_att = models.Attempt(trick_id=trick.id,
                                          game_id=game.id,
                                          user="past_" + test_user,
                                          landed=False,
                                          time_of_attempt=datetime.datetime.utcnow())
                models.db.session.add(oppo_att)

                models.db.session.commit()

            models.db.session.add(game)
            models.db.session.commit()  # re-sync attempts
            game_state = models.get_game_state(game.attempts, test_user)
            assert game_state.user_score == 0
            assert game_state.opponent_score == n_wins_first

            # Check that now if both land one, no score change. Use last trick ID
            user_att = models.Attempt(trick_id=test_tricks[-1].id,
                                      game_id=game.id,
                                      user=test_user,
                                      landed=True,
                                      time_of_attempt=datetime.datetime.utcnow())
            models.db.session.add(user_att)

            oppo_att = models.Attempt(trick_id=test_tricks[-1].id,
                                      game_id=game.id,
                                      user="past_" + test_user,
                                      landed=True,
                                      time_of_attempt=datetime.datetime.utcnow())
            models.db.session.add(oppo_att)
            models.db.session.commit()

            models.db.session.add(game)
            models.db.session.commit()  # re-sync attempts
            game_state = models.get_game_state(game.attempts, test_user)
            assert game_state.user_score == 0
            assert game_state.opponent_score == n_wins_first


            # A one-off repeat should count as fail, turn over priority to opponent
            user_att = models.Attempt(trick_id=test_tricks[0].id,
                                      game_id=game.id,
                                      user=test_user,
                                      landed=False,
                                      time_of_attempt=datetime.datetime.utcnow())
            models.db.session.add(user_att)
            models.db.session.commit()

            for trick in test_tricks[n_wins_first:n_wins_first + n_drops_next]:
                user_att = models.Attempt(trick_id=trick.id,
                                          game_id=game.id,
                                          user="past_" + test_user,
                                          landed=True,
                                          time_of_attempt=datetime.datetime.utcnow())
                models.db.session.add(user_att)

                oppo_att = models.Attempt(trick_id=trick.id,
                                          game_id=game.id,
                                          user=test_user,
                                          landed=False,
                                          time_of_attempt=datetime.datetime.utcnow())
                models.db.session.add(oppo_att)

                models.db.session.commit()

            models.db.session.add(game)
            models.db.session.commit()  # re-sync attempts
            game_state = models.get_game_state(game.attempts, test_user)
            assert game_state.user_score == n_drops_next
            assert game_state.opponent_score == n_wins_first
            assert game_state.status_feed[0] == "Past you wins!"
