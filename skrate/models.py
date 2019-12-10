"""Models for key nouns in Skrate, namely tricks, attempts, games."""
import datetime
from typing import Any, List, Mapping, Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Our app database
db = SQLAlchemy()


def init_db_connec(app: Flask) -> None:
    """Connect to persistence layer for Skrate app.
    
    Args:
        app: The Flask web server application object

    """
    db.init_app(app)


def create_db_tables(app: Flask) -> None:
    """Create or update table schemas based on models defined in this file.

    Args:
        app: The Flask web server application object

    """
    with app.app_context():
        db.create_all()


def drop_db_tables(app: Flask) -> None:
    """Drop all tables, useful in test (ensure URI contains TEST).

    Args:
        app: The Flask web server application object

    Raises:
        ValueError: if you try to run this on production config

    """
    if not "test" in app.config["SQLALCHEMY_DATABASE_URI"]:
        raise ValueError("drop_all() only permitted on test db, use psql.")
    with app.app_context():
        db.drop_all()


class Trick(db.Model):
    """A type of trick (i.e., kickflip) - **NOT** a specific attempt of one."""

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    attempts = db.relationship("Attempt", backref="trick", lazy=True)


class Attempt(db.Model):
    """An attempt at a trick, with landed or not result."""

    id = db.Column(db.Integer, primary_key=True)
    trick_id = db.Column(db.Integer, db.ForeignKey("trick.id"), nullable=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"))
    user = db.Column(db.String(16), nullable=False)  # Note can be past_<user>
    landed = db.Column(db.Boolean, nullable=False)
    time_of_attempt = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class Game(db.Model):
    """A single game of SKATE against your past self."""

    id = db.Column(db.Integer, primary_key=True)
    attempts = db.relationship("Attempt", backref="game", lazy=True)
    complete = db.Column(db.Boolean, nullable=False)
    user = db.Column(db.String(16), nullable=False)
    user_won = db.Column(db.Boolean)  # Null if still in progress


def record_attempt(app: Flask, user: str, trick_id: int, landed: bool,
                   game_id: Optional[bool]) -> None:
    """Record an attempt by user (or fake attempt as part of a game)

    Args:
        app: The Flask web server application object
        user: the user attempting the trick (may be past_someone)
        trick_id: id of the trick being attempted
        landed: whether or not it was landed successfully
        game_id: id of which game it's part of, if any

    """
    with app.app_context():
        att = Attempt(trick_id=trick_id, game_id=game_id, user=user, landed=landed)
        db.session.add(att)
        db.session.commit()
        app.logger.info("Committed new attempt with id %s" % att.id)


def start_game(app: Flask, user: str) -> int:
    """Start a new game of SKATE with current user, return game_id.

    Args:
        app: the Flask web server application object
        user: the name of the current user

    """
    with app.app_context():
        game = Game(attempts=[], complete=False, user=user)
        db.session.add(game)
        db.session.commit()
        app.logger.info("Started new game with id %s" % game.id)


def get_trick_view_params(user: str, trick: Trick) -> Mapping[str, Any]:
    """Get parameters to render landing page view of trick and stats on it.

    Args:
        user: the currente Skrate user
        trick: the Trick object representing the type of trick

    """

    user_attempts = Attempt.query.filter_by(user=user, trick_id=trick.id).count()
    user_lands = Attempt.query.filter_by(user=user,
            trick_id=trick.id, landed=True).count()
    return {
        "attempts": user_attempts,
        "lands": user_lands,
        "name": trick.name,
        "id": trick.id
    }


def get_all_trick_infos(app: Flask, user: str) -> List[Mapping[str, Any]]:
    """Get list of all trick infos and user stats on them, for view render."""
    all_tricks = Trick.query.all()
    results = []
    for trick in all_tricks:
        results.append(get_trick_view_params(user, trick))
    return results


def get_latest_game_params(app: Flask, user: str) -> Mapping[str, Any]:
    """Get parameters to render the game view.

    Args:
        app: the server flask application object
        user: current user

    """
    # Temp debug TODO finish
    turn_lines = [
        {"classes": "list-group-item active", "text": "Turn [14]: Do work next"},
        {"classes": "list-group-item", "text": "Turn [13]: Was good for good you"},
        {"classes": "list-group-item", "text": "Turn [12]: Was bad for past you"},
    ]
    return {"turn_lines": turn_lines}

