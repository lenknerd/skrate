"""Tests for the main skrate application."""
import logging
import os
from typing import Any

import pytest

import context
from skrate import server
from skrate import models
from skrate import tricks


# Test database fully separate from production
_TEST_DB_URI = "postgresql://skrate_test_user:skrate_test_password@localhost:5432/skrate_test_db"


@pytest.fixture
def client(monkeypatch: Any):
    """Client test fixture for flask app testing - fake client, test database."""

    monkeypatch.setattr(server, "_SQLALCHEMY_DATABASE_URI", _TEST_DB_URI)
    monkeypatch.setattr(server, "_TESTING", True)
    monkeypatch.setattr(server, "_LOG_LEVEL", logging.WARN)

    server.init_app(False)  # test with debug mode off (False)

    # In the test database, drop and re-create tables for clean state
    models.drop_db_tables(server.app)
    models.create_db_tables(server.app)

    # And upload trick definitions
    tricks.update_tricks_table(server.app)

    # Return client for test runs
    with server.app.test_client() as client:
        yield client

    # Finally wipe tables again to leave in clean state
    models.drop_db_tables(server.app)


class TestSkrate:

    def test_user_init(self, client) -> None:
        """Test landing page sets user and gets trick list."""
        rv = client.get("/johndoe")
        assert server.session["user"] == "johndoe"
        assert rv.status_code == 200
        html_str = str(rv.data)
        assert "trick84" in html_str  # should be this many ids
        assert "Heelflip Bigspin" in html_str  # just one of them

    def test_attempt_success(self, client) -> None:
        """Test a successful attempt leads to incrememnt on tricks stats."""
        client.get("/johndoe")
        client.get("/attempt/1/true/false")
        db_atts = models.Attempt.query.all()
        assert len(db_atts) == 1
        assert db_atts[0].user == "johndoe"
        assert db_atts[0].trick.id == 1
        assert db_atts[0].trick.name == "Kickflip"
