#!/usr/bin/env python3
"""Skrate main application for serving skateboarding data interface."""
from flask import Flask, render_template


app = Flask(__name__) 


@app.route('/<user>')
def index(user: str) -> str:
    """Entry point to Skrate should be URL with user in name.

    Args:
        user: the user name to log in as.

    Note, actual user authentication needed if this goes anywhere.

    """
    session['user'] = user
    return render_template("index.html", user=user)


@app.route('/landed/<trick>')
def hello_name(trick: str) -> str:
    """Mark that you just landed a trick called <trick>.
    
    Args:
        trick: the name of the trick

    """
    # TODO log it in database
    return "Nice"


if __name__ == '__main__': 
    app.run()
