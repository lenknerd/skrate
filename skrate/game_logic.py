"""Encodes the basic rules of the game of SKATE.

Two-player only for now, versus your past self for progression check.
"""
import random
import os
from typing import List, Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

# Letters to get in a game of SKATE
LETTERS = ("S", "K", "A", "T", "E")

# Constants in various messages
_YOU_NAMES = ("New you", "Past you")
_TURN_FAULT = "Internal error! Turns order not as expected!"

# In game of SKATE, determine land probability based on last _ tries
_RECENT_ATTEMPTS_WINDOW = 10

# Constant to randomize computer user trick choices (will use trick with best
# success rate still available, but will skip to next best with this probability)
_TRICK_RANDOM_SKIP = 0.5


class GameState:
    """State keeper for score, who's challenging."""

    def __init__(self, user_name: str) -> None:
        """Initialize a new game state.
        
        Args:
            user_name: the user name logged in as

        """
        # Score as number of letters (lose when get to len(LETTERS))
        self.user_score = 0
        self.opponent_score = 0
        self.user_name = user_name

        # Messages updating on instructions and what happened
        self.status_feed = ["Starting game! %s to go first." % user_name]

        # If previous move was a landed challenge, what trick was it
        self.challenging_move_id = None  # Optional[int] ??

        # What tricks have been landed, not allowed to repeat
        # unless it was previous landed challenging trick
        self.trick_ids_used_up = []  # List[int] ??

    def say(self, message: str) -> None:
        """Add a message to the start of the status feed (so can show top-N)."""
        self.status_feed.insert(0, message)

    def apply_attempt(self, attempt: "models.Attempt") -> bool:
        """Update the game state given an attempt that just happened.
        
        Args:
            attempt: the attempt object (what trick, whether landed).

        Returns:
            Whether the game is over

        """
        user_attempt = attempt.user == self.user_name
        attempter, opponent = _YOU_NAMES if user_attempt else _YOU_NAMES[::-1]

        if attempt.trick_id in self.trick_ids_used_up:
            self.say("Trick already used! Treating as miss for game purposes.")
            attempt.landed = False

        if self.challenging_move_id is not None:
            # Check player tried the right trick, and mark it as used up
            if attempt.trick_id != self.challenging_move_id:
                self.say("Wrong trick, treating as a miss for game purposes. "
                          "%s was supposed to try a %s" % (attempter, attempt.trick.name))
                attempt.landed = False
            self.trick_ids_used_up.append(attempt.trick_id)

            # This is a response to the challenge last turn, resetting challenge trick
            self.challenging_move_id = None

            if attempt.landed:
                self.say("%s matched the challenge." % attempter)
                return False

            # If here, is score-changing case, player challenged and other missed
            if user_attempt:
                letter_idx = self.user_score
                self.user_score += 1
            else:
                letter_idx = self.opponent_score
                self.opponent_score += 1
            self.say("Missed challenge! %s gains a %s" % (attempter, LETTERS[letter_idx]))

            # Lastly see if the miss results in game end
            if max(self.user_score, self.opponent_score) >= len(LETTERS):
                self.say("%s wins!" % opponent)
                return True  # Game over

        elif attempt.landed:
            # This was not a challenge response, it initiates a challenge
            self.say("%s landed a %s! Can %s match it?" %
                     (attempter, attempt.trick.name, opponent))
            self.challenging_move_id = attempt.trick_id

        return False  # Game not over yet

    def is_ongoing(self) -> bool:
        """Whether the game is complete/won by someone."""
        return self.user_score < len(LETTERS) and self.opponent_score < len(LETTERS)


def _read_sql_resource(query_name: str) -> str:
    """Read a .sql file from directory of this python file.

    Args:
        query_name: file name minus .sql extension, expected in same dir as this module

    """
    with open(os.path.join(os.path.dirname(__file__), query_name + ".sql")) as qfile:
        return qfile.read()


def game_trick_choice(app: Flask, user: str, tricks_prohibited: List[int], db: SQLAlchemy) -> int:
    """Find the trick the user is most likely to land.

    Args:
        app: the Flask web server application object
        user: the user trying the trick
        tricks_prohibited: Tricks can't use (e.g. already hit in game)
        db: the persistence layer connection

    """
    with app.app_context():
        statement = _read_sql_resource("rates_by_trick")

        result = db.session.execute(statement, {"username": user, "nlimit": _RECENT_ATTEMPTS_WINDOW})
        for row in result:
            if row[0] not in tricks_prohibited and random.uniform(0, 1) < _TRICK_RANDOM_SKIP:
                return row[0]

    raise RuntimeError("All tricks used up! Crazy outcome expected to never happen!")


def get_odds(user: str, trick_id: int, db: SQLAlchemy) -> float:
    """Get odds of user landing a trick based on recent attempts.

    Args:
        user: the user trying the trick
        trick_id: which trick is in question
        db: the persistence layer connection

    """
    pass

