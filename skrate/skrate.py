#!/usr/bin/env python3
"""Skrate main application for serving skateboarding data interface."""
from typing import Optional

import click
from flask import Flask, session, render_template
from flask_session import Session

import models
import tricks


# Flask application and session
app = Flask(__name__) 
sess = Session(app)


# App constants
_APP_KEY = "skrate default key"
_SQLALCHEMY_DATABASE_URI = "postgresql://skrate_user:skrate_password@localhost:5432/postgres"
_SESSION_TYPE = "filesystem"


# Route definitions for the Skrate REST API


@app.route("/<user>")
def index(user: str) -> str:
    """Entry point to Skrate should be URL with user in name.

    Args:
        user: the user name to log in as.

    Note, actual user authentication needed if this goes anywhere.

    """
    session["user"] = user
    return render_template("index.html", user=user)


@app.route("/attempt/<trick_id>/<landed>/<past>")
def attempt(trick_id: int, landed: bool, past: bool) -> str:
    """Mark that you just landed or missed a trick called <trick>.
    
    Args:
        trick_id: the id of the trick
        landed: whether or not you landed it
        past: whether it is a "fake" attempt by your past self in a game

    """
    user = "past_" + session["user"] if past else session["user"]
    models.record_attempt(user, trick_id, landed)
    # TODO if end of game, set game_id end values (complete/winner)
    # and set session game_id back to none


@app.route("/start_game")
def start_game() -> str:
    """Start a game under the current user."""
    game_id = models.start_game(session["user"])
    session["game_id"] = game_id


# TODO
# get refreshed game block (instructions, latest game results, record overall, etc.)
# get refreshed trick block (updated stats)


# Skrate CLI tool defintion


@click.group()
@click.option("--debug/--no-debug", default="False", help="Whether to enable debug mode")
def skrate(debug: bool) -> None:
    """Main entry point for skrate command line interface."""

    print("Welcome to Skrate!")

    app.secret_key = _APP_KEY
    app.config["SESSION_TYPE"] = _SESSION_TYPE
    app.config["SQLALCHEMY_DATABASE_URI"] = _SQLALCHEMY_DATABASE_URI
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # silence warning
    app.debug = debug
    sess.init_app(app)
    models.init_db_connec(app)


@skrate.command()
def database_setup() -> None:
    """Create tables in skrate schema based on app models."""

    print("Setting up database tables...")
    models.create_db_tables(app)
    print("Loading up tricks...")
    tricks.update_tricks_table(app)
    print("Setup complete.")


@skrate.command()
@click.option("-p", "--port", help="Port to listen on", default=5000, type=int)
@click.option("-h", "--host", help="Use 0.0.0.0 for LAN, else localhost only")
def serve(port: int, host: Optional[str]) -> None:
    """Run the main server application."""

    print("Running skrate web server.")
    app.run(port=port, host=host)


if __name__ == '__main__': 
    skrate()
