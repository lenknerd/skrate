#!/usr/bin/env python3
"""Skrate main application for serving skateboarding data interface."""
from typing import Optional

import click
import psycopg2
from flask import Flask, session, render_template
from flask_session import Session


app = Flask(__name__) 
sess = Session(app)


@app.route('/<user>')
def index(user: str) -> str:
    """Entry point to Skrate should be URL with user in name.

    Args:
        user: the user name to log in as.

    Note, actual user authentication needed if this goes anywhere.

    """
    session['user'] = user
    return render_template("index.html", user=user)


@app.route('/attempt/<trick>/<landed>')
def attempt(trick: str, landed: bool) -> str:
    """Mark that you just landed or missed a trick called <trick>.
    
    Args:
        trick: the name of the trick

    """
    # TODO log it in database
    return "Nice"

# TODO
# get refreshed game block (instructions, latest game results, record overall, etc.)
# get refreshed trick block (updated stats)
# mark an attempt at a trick (pass or fail)
#   all from db state except whether latest game is in same session

# Args for stuff like look-back time
# https://docs.google.com/document/d/1Mt8Z6fhCYwp_sQ_VUhOaYh5ghqx23Lqh3TdgOI6Elaw

@click.command()
@click.option("--debug/--no-debug", default="False", help="Whether to enable debug mode")
@click.option("-h", "--host", help="Use 0.0.0.0 for LAN, else localhost only")
def run_app(debug: bool, host: Optional[str]) -> None:
    """Run the main server application."""

    app.secret_key = 'super secret key'
    app.config['SESSION_TYPE'] = 'filesystem'
    app.debug = debug
    sess.init_app(app)
    app.run(host=host)


if __name__ == '__main__': 
    run_app()
