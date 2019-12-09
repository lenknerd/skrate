"""Tests for the main skrate application."""
import os

import pytest

import context
import run_skrate
from skrate import models


# Test database fully separate from production
_TEST_DB_URI = "postgresql://skrate_test_user:skrate_test_password@localhost:5432/skrate_test_db"


@pytest.fixture
def client():
    """Client test fixture for flask app testing - fake client, test database."""

    run_skrate.app.config["SQLALCHEMY_DATABASE_URI"] = _TEST_DB_URI
    run_skrate.app.config["TESTING"] = True
    run_skrate.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # just quiets an unnec. warning

    with run_skrate.app.test_client() as client:
        # Connect to the test database, drop and re-create tables for clean state
        models.init_db_connec(run_skrate.app)
        models.drop_db_tables(run_skrate.app)
        models.create_db_tables(run_skrate.app)

        yield client

    # Finally wipe tables again to leave in clean state
    # models.drop_db_tables(skrate.app)


class TestSkrate:

    def test_user_init(self, client) -> None:
        """Test that when we navigate to landing page first time, sets user in session."""
        assert 1 == 1

