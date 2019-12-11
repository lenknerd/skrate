"""Encodes the basic rules of the game of SKATE.

Two-player only for now, versus your past self for progression check.
"""
from typing import List, Optional

from skrate import models


LETTERS = ("S", "K", "A", "T", "E")

_YOU_NAMES = ("New you", "Past you")

_TURN_FAULT = "Internal error! Turns order not as expected!"


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
        self.challenging_move_id: Optional[int] = None

        # What tricks have been landed, not allowed to repeat
        # unless it was previous landed challenging trick
        self.trick_ids_used_up: List[int]

    def say(self, message: str) -> None:
        """Add a message to the start of the status feed (so can show top-N)."""
        self.status_feed.insert(0, message)

    def apply_attempt(self, attempt: models.Attempt) -> bool:
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

            if attempt.landed:
                self.say("%s matched the challenge.", attempter)
                continue

            # If here, is score-changing case, player challenged and other missed
            self.say("Missed challenge! %s gains a %s" % (attempter, LETTERS))
            if user_attempt:
                letter_idx = self.user_score
                self.user_score += 1
            else:
                letter_idx = self.opponent_score
                self.opponent_score += 1

            # Lastly see if the miss results in game end
            if max(self.user_score, self.opponent_score) >= len(LETTERS):
                self.say("%s wins!", opponent)
                return True  # Game over

        elif attempt.landed:
            # This was not a challenge response, it initiates a challenge
            self.say("%s landed a %s! Can %s match it?",
                     (you, attempt.trick.name, opponent_you))
            self.challenging_move_id = attempt.trick_id

        return False  # Game not over yet


def get_game_state(attempts: List[models.Attempt], user_name: str) -> GameState:
    """Calculate the game state given ordered list of attempts.

    Args:
        attempts: the attempts by either user in this game
        user_name: the user name logged in as

    """
    # Bit wasteful to do this each time want it, but still plenty fast
    sorted_attempts = sorted(attempts, key=lambda a: a.time_of_attempt)

    # Sanity check, confirm alternating turns starting with user
    assert all(a.user == user_name for a in sorted_attempts[::2]), _TURN_FAULT
    assert all(a.user != user_name for a in sorted_attempts[1::2]), _TURN_FAULT

    # Build up state and return it
    game_state = GameState(user_name)
    for i, attempt in enumerate(sorted_attempts):
        if game_state.apply_attempt(attempt) and i != len(attempts) - 1:
            # We should only be looking at one game here, so shouldn't happen
            raise("Internal error! Game finished before last attempt.")

    return game_state
