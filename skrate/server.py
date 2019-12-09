"""Skrate application and routes for serving skateboarding data REST API."""
import logging

from flask import Flask, session, render_template
from flask_session import Session

from skrate import models
from skrate import tricks


# Flask application and session
app = Flask("skrate")
sess = Session(app)

# App constants
_APP_KEY = "skrate default key"
_SQLALCHEMY_DATABASE_URI = "postgresql://skrate_user:skrate_password@localhost:5432/postgres"
_SESSION_TYPE = "filesystem"
_SERVER_LOG = "/tmp/skrate_service.log"
_SERVER_LOG_FORMAT = "'%(asctime)s %(levelname)s: %(message)s'"


def configure_app_logger() -> None:
    """Configure app logger to file and output."""
    app.logger.setLevel(logging.INFO)
    file_handler = logging.FileHandler(_SERVER_LOG)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(_SERVER_LOG_FORMAT))
    app.logger.addHandler(file_handler)


def init_app(debug: bool) -> None:
    """Initialize Skrate applciation.
    
    Args:
        debug: whether or not to run in debug mode.

    """
    app.secret_key = _APP_KEY
    app.config["SESSION_TYPE"] = _SESSION_TYPE
    app.config["SQLALCHEMY_DATABASE_URI"] = _SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # just quiets an unnec. warning
    app.debug = debug

    configure_app_logger()

    sess.init_app(app)
    models.init_db_connec(app)

    app.logger.info("Welcome to Skrate! Application initialized.")


def set_up_database() -> None:
    app.logger.info("Setting up database tables...")
    models.create_db_tables(app)
    app.logger.info("Loading up tricks...")
    tricks.update_tricks_table(app)
    app.logger.info("Setup complete.")


@app.route("/<user>")
def index(user: str) -> str:
    """Entry point to Skrate should be URL with user in name.

    Args:
        user: the user name to log in as.

    Note, actual user authentication needed if this goes anywhere.

    """
    session["user"] = user
    app.logger.info("User %s started a session.", user)
    return render_template("index.html", user=user)


@app.route("/attempt/<trick_id>/<landed>/<past>")
def attempt(trick_id: str, landed: str, past: str) -> str:
    """Mark that you just landed or missed a trick called <trick>.
    
    Args:
        trick_id: the id of the trick (should be integer format)
        landed: whether or not you landed it ('true'/'false')
        past: whether is a "fake" attempt by past self in game ('true'/'false')

    """
    landed_bool = landed == "true"  # would be nice if Flask checked type hints?
    trick_id_int = int(trick_id)
    user = "past_" + session["user"] if past == "true" else session["user"]
    game_id_if_any = session.get("game_id")

    app.logger.info("User %s tried trick %s (landed=%s)", user, trick_id, landed)
    models.record_attempt(app, user, trick_id_int, landed_bool, game_id_if_any)
    # return """ { "ran": "true" } """
    return {"attempted": True}
    # TODO if end of game, set game_id end values (complete/winner)
    # and set session game_id back to none


@app.route("/start_game")
def start_game() -> str:
    """Start a game under the current user."""
    game_id = models.start_game(app, session["user"])
    session["game_id"] = game_id
    app.logger.info("Use %s started game, id %s", session["user"], game_id)
    return {"started": True}


# TODO
# get refreshed game block (instructions, latest game results, record overall, etc.)
# get refreshed trick block (updated stats)

