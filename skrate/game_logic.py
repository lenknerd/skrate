"""Encodes the basic rules of the game of SKATE.

Two-player only for now, versus your past self for progression check.
"""
import random
import os
from typing import Dict, List, Optional

from flask import Flask
from flask_sqlalchemy import SQLAlchemy  # type: ignore


# Letters to get in a game of SKATE
LETTERS = ("S", "K", "A", "T", "E")

# Constants in various messages
_YOU_NAMES = ("New you", "Past you")
_TURN_FAULT = "Internal error! Turns order not as expected!"

# In game of SKATE, determine land probability based on last _ tries
_RECENT_ATTEMPTS_WINDOW_OLDEST = 10
_RECENT_ATTEMPTS_WINDOW_NEWEST = 1

# Constant to randomize computer user trick choices (will use trick with best
# success rate still available, but will skip to next best with this probability)
_TRICK_RANDOM_SKIP = 0.5


class GameFeedMessage:
    """A game feed message."""

    def __init__(self, msg_text: str, msg_type: str="") -> None:
        """Initialze a game feed message.
        
        Args:
            msg_text: the text of the message
            msg_type: controls coloring or other options

        """
        self.msg_text = msg_text
        self.msg_type = ""
        if msg_type:
            self.msg_type = "list-group-item-" + msg_type  # primary, success, danger


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

        self.turn_idx = 0

        # If previous move was a landed challenge, what trick was it
        self.challenging_move_id: Optional[int] = None

        # What tricks have been landed, not allowed to repeat
        # unless it was previous landed challenging trick
        self.trick_ids_used_up: List[int] = []

        # Messages updating on instructions and what happened
        self.status_feed: List[GameFeedMessage] = []
        self._say("Starting game! %s up first." % user_name, "primary")

    def _say(self, message: str, msg_type: str="") -> None:
        """Add a message to the start of the status feed (so can show top-N).
        
        Args:
            message: The message to put in the feed
            msg_type: type of message ('success', 'primary', '')

        """
        self.status_feed.append(
                GameFeedMessage("[Turn %s]: %s" % (self.turn_idx, message), msg_type))

    def apply_attempt(self, trick_id: int, trick_name: str, landed: bool, user: str) -> bool:
        """Update the game state given an attempt that just happened.
        
        Args:
            trick_id: the id of the trick tried
            trick_name: the name of the trick being tried
            landed: whether or not the trick was landed
            user: who was attempting the trick

        Returns:
            Whether the game is over

        """
        user_attempt = user == self.user_name
        attempter, opponent = _YOU_NAMES if user_attempt else _YOU_NAMES[::-1]

        if trick_id in self.trick_ids_used_up:
            self._say("Trick already used! Treating as miss for game purposes.", "dark")
            landed = False

        if self.challenging_move_id is not None:
            # Check player tried the right trick, and mark it as used up
            if trick_id != self.challenging_move_id:
                self._say("Wrong trick, treating as a miss for game purposes.", "dark")
                landed = False
            self.trick_ids_used_up.append(trick_id)

            # This is a response to the challenge last turn, resetting challenge trick
            self.challenging_move_id = None

            if landed:
                next_instruc = "" if user_attempt else "Try something else!"
                self._say("%s matched the challenge. %s" % (attempter, next_instruc), "success")
                self.turn_idx += 1
                return False

            # If here, is score-changing case, player challenged and other missed
            if user_attempt:
                letter_idx = self.user_score
                self.user_score += 1
            else:
                letter_idx = self.opponent_score
                self.opponent_score += 1
            self._say("Missed challenge! %s gains a %s" % (attempter, LETTERS[letter_idx]), "danger")

            # Lastly see if the miss results in game end
            if max(self.user_score, self.opponent_score) >= len(LETTERS):
                self._say("%s wins!" % opponent, "primary")
                return True  # Game over

        elif landed:
            # This was not a challenge response, it initiates a challenge
            self._say("%s landed a %s! Can %s match it?" %
                     (attempter, trick_name, opponent), "warning")
            self.challenging_move_id = trick_id
        else:
            # This was not a challenge, and was a miss, nothing to do but report
            self._say("%s missed a %s, back to %s" % (attempter, trick_name, opponent))

        self.turn_idx += 1
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
        result = db.session.execute(statement, {"username": user,
                                                "nlimit": _RECENT_ATTEMPTS_WINDOW_OLDEST,
                                                "nmin": _RECENT_ATTEMPTS_WINDOW_NEWEST})
        for row in result:
            if row[0] not in tricks_prohibited and random.uniform(0, 1) > _TRICK_RANDOM_SKIP:
                return row[0]

    raise RuntimeError("All tricks used up! Crazy outcome expected to never happen!")


def get_odds_lookup_dict(app: Flask, user: str, db: SQLAlchemy) -> Dict[int, float]:
    """Get dict to look up odds of landing trick by trick id.

    Args:
        app: The flask server application
        user: the user to look up land rate for
        db: the persistence layer connection

    """
    with app.app_context():
        statement = _read_sql_resource("rates_by_trick")
        result = db.session.execute(statement, {"username": user,
                                                "nlimit": _RECENT_ATTEMPTS_WINDOW_OLDEST,
                                                "nmin": _RECENT_ATTEMPTS_WINDOW_NEWEST})
        return {row[0]: row[1] for row in result}


def get_odds(app: Flask, user: str, trick_id: int, db: SQLAlchemy) -> float:
    """Get odds of user landing a trick based on recent attempts.

    Args:
        app: the Flask web server application object
        user: the user trying the trick
        trick_id: which trick is in question
        db: the persistence layer connection

    """
    with app.app_context():
        # Would be more efficient to use different query only on one trick, but trivial scale for now
        statement = _read_sql_resource("rates_by_trick")
        result = db.session.execute(statement, {"username": user,
                                                "nlimit": _RECENT_ATTEMPTS_WINDOW_OLDEST,
                                                "nmin": _RECENT_ATTEMPTS_WINDOW_NEWEST})
        for row in result:
            if row[0] == trick_id:
                return row[1]

    raise ValueError("Requested odds for non-existent trick id " + str(trick_id))

