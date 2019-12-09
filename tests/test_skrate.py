"""Tests for the main skrate application."""
import os

import pytest

import context
from skrate import server
from skrate import models


# Test database fully separate from production
_TEST_DB_URI = "postgresql://skrate_test_user:skrate_test_password@localhost:5432/skrate_test_db"


@pytest.fixture
def client():
    """Client test fixture for flask app testing - fake client, test database."""

    server.app.config["SQLALCHEMY_DATABASE_URI"] = _TEST_DB_URI
    server.app.config["TESTING"] = True
    server.app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  # just quiets an unnec. warning

    with server.app.test_client() as client:
        # Connect to the test database, drop and re-create tables for clean state
        models.init_db_connec(server.app)
        models.drop_db_tables(server.app)
        models.create_db_tables(server.app)

        yield client

    # Finally wipe tables again to leave in clean state
    # models.drop_db_tables(skrate.app)


class TestSkrate:

    def test_user_init(self, client) -> None:
        """Test that when we navigate to landing page first time, sets user in session."""
        assert 1 == 1

