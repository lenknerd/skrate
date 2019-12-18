"""Skrate application and routes for serving skateboarding data REST API."""
import typing
import logging
from json import JSONEncoder

from flask import Flask, session, render_template
from flask_session import Session

from skrate import models
from skrate import tricks


# Flask application and session
app = Flask("skrate")
sess = Session(app)

# App constants
_APP_KEY = "skrate default key"
_LOG_LEVEL = logging.INFO 
_SQLALCHEMY_DATABASE_URI = "postgresql://skrate_user:skrate_password@localhost:5432/postgres"
_SESSION_TYPE = "filesystem"
_SERVER_LOG = "/tmp/skrate_service.log"
_SERVER_LOG_FORMAT = "'%(asctime)s %(levelname)s: %(message)s'"
_TESTING = False


class SkrateActionResponse:
    """Response to action route, confirm route and say what to update."""

    def __init__(self, route_confirm: str, update_game: bool = False,
            update_tricks: typing.List[int] = [], update_all_tricks: bool = False) -> None:
        """Initialize an action response object.
        
        Args:
            route_confirm: echo back name of route you just ran to get this
            update_game: whether to update the game view
            update_tricks: list of which trick views to upate
            update_all_tricks: whether to override above and say all tricks

        """
        self.route_confirm = route_confirm
        self.update_game = update_game
        self.update_tricks = update_tricks
        self.update_all_tricks = update_all_tricks

    def obj(self) -> typing.Mapping[str, typing.Any]:
        """Convert self to a json-serializable response."""
        return vars(self)


# json serialized object of above
_SkrateActionResponse = typing.Mapping[str, typing.Any]


def configure_app_logger() -> None:
    """Configure app logger to file and output."""
    app.logger.setLevel(_LOG_LEVEL)
    file_handler = logging.FileHandler(_SERVER_LOG)
    file_handler.setLevel(_LOG_LEVEL)
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
    app.config["TESTING"] = _TESTING
    app.debug = debug

    configure_app_logger()

    sess.init_app(app)
    models.init_db_connec(app)

    app.logger.info("Welcome to Skrate! Application initialized.")


def set_up_database() -> None:
    """Create any tables not already present, load tricks not there."""
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

    Note, actual user authentication needed in the future, or at least
    check if the user argument above is not empty.

    """
    session["user"] = user
    app.logger.info("User %s started a session.", user)

    all_tricks = models.get_all_trick_infos(app, session["user"])

    game_view_params = models.get_latest_game_params(app, session["user"])
    return render_template("index.html", user=user, tricks=all_tricks, **game_view_params)


@app.route("/attempt/<trick_id>/<landed>/<past>")
def attempt(trick_id: str, landed: str, past: str) -> _SkrateActionResponse:
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

    # Record whether we were in a game which required view update
    to_be_updated = [trick_id]
    redraw_game = False
    if game_id_if_any is not None:
        redraw_game = True
        # Need to get state of game to figure out whether oppoent response call needed
        models.opponent_response_if_any(app, user, game_id_if_any)

    return SkrateActionResponse("attempt", redraw_game, [trick_id], False).obj()


@app.route("/start_game")
def start_game() -> _SkrateActionResponse:
    """Start a game under the current user."""

    if session["game_id"] is not None:
        raise RuntimeError("Tried to start game when one already started!")

    session["game_id"] = models.start_game(app, session["user"])
    app.logger.info("Use %s started game, id %s", session["user"], session["game_id"])
    return SkrateActionResponse("start_game", True, [], False).obj()


@app.route("/get_single_trick_stats/<trick_id>")
def get_single_trick_stats(trick_id: str) -> str:
    """Get rendered template showing my latest up-to-date stats on trick.

    Args:
        The id of the trick you want to update/render block for.

    """
    trick = models.Trick.query.filter_by(id=trick_id).one()
    trick_params = models.get_trick_view_params(session["user"], trick)
    return render_template("trickstats.html", trick=trick_params)


@app.route("/get_latest_game_view")
def get_latest_game_view() -> str:
    """Get the view showing status, instructions for current or latests game."""
    game_view_params = models.get_latest_game_params(app, session["user"])
    return render_template("game.html", **game_view_params)

