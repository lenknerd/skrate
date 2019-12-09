"""Trick definitions for Skrate app, and function to load/update en masse."""
from typing import List, Optional, Tuple

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

from skrate import models


# Trick name and whether should also include a switch, nollie, and/or fakie version.
# Only common stuff and only limited to BATB-legal - note rules here 
# https://en.wikipedia.org/wiki/Game_of_Skate#Rules_in_Battle_at_the_Berrics

_PREFIXES = ["Nollie ", "Switch ", "Fakie "]

# name,                nollie, switch, fakie
_TRICKS = [
    ("Kickflip",         True,  True,  True),
    ("Ollie",            False, True,  True),
    ("Nollie",           False, False, False),
    ("BS 180",           True,  True,  True),
    ("FS 180",           True,  True,  True),
    ("FS Shove-It",      True,  True,  True),
    ("BS Shove-It",      True,  True,  True),
    ("Heelflip",         True,  True,  True),
    ("FS 360 Shove-It",  True,  True,  True),
    ("BS 360 Shove-It",  True,  True,  True),
    ("FS Bigspin",       True,  True,  True),
    ("BS Bigspin",       True,  True,  True),
    ("Varial Flip",      True,  True,  True),
    ("Varial Heelflip",  True,  True,  True),
    ("360 Flip",         True,  True,  True),
    ("Laserflip",        True,  True,  True),
    ("BS 180 Kickflip",  True,  True,  True),
    ("FS 180 Kickflip",  True,  True,  True),
    ("BS 180 Heelflip",  True,  True,  True),
    ("FS 180 Heelflip",  True,  True,  True),
    ("Bigflip",          True,  True,  True),
    ("Heelflip Bigspin", True,  True,  True),
]


def trick_variants(trick_tuple: Tuple[str, bool, bool, bool]) -> List[str]:
    """Get list of variations of trick, e.g. Nollie Kicklip, Switch Kickflip, etc.
    
    Args:
        trick_tuple: name of the trick,
                      whether a nollie [trick] should be included,
                      whether a switch [trick] should be included,
                      whether a fakie [trick] should be included,

    """
    base = trick_tuple[0]
    prefixes = [prefix for prefix, use in zip(_PREFIXES, trick_tuple[1:]) if use]
    return [base, *[prefix + base for prefix in prefixes]]


def update_tricks_table(app: Flask) -> None:
    """Update the tricks table. Maintain any existing ID's.
    
    Args:
        app: the Flask web service app

    """
    with app.app_context():
        for trick_tuple in _TRICKS:
            for trick_name in trick_variants(trick_tuple):
                # Store tricks if they're not already there
                if not models.Trick.query.filter_by(name=trick_name).count():
                    app.logger.info("Adding trick: %s" % trick_name)
                    new_trick = models.Trick(name=trick_name)
                    models.db.session.add(new_trick)
                    models.db.session.commit()  # auto-assigns ID on commit

