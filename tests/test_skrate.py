"""Tests for the main skrate application."""
import os
from typing import Any

import pytest

import context
from skrate import server
from skrate import models


# Test database fully separate from production
_TEST_DB_URI = "postgresql://skrate_test_user:skrate_test_password@localhost:5432/skrate_test_db"


@pytest.fixture
def client(monkeypatch: Any):
    """Client test fixture for flask app testing - fake client, test database."""

    monkeypatch.setattr(server, "_SQLALCHEMY_DATABASE_URI", _TEST_DB_URI)
    monkeypatch.setattr(server, "_TESTING", True)

    server.init_app(False)  # test with debug mode off (False)

    # In the test database, drop and re-create tables for clean state
    models.drop_db_tables(server.app)
    models.create_db_tables(server.app)

    with server.app.test_client() as client:
        yield client

    # Finally wipe tables again to leave in clean state
    models.drop_db_tables(server.app)


class TestSkrate:

    def test_user_init(self, client) -> None:
        """Test that when we navigate to landing page first time, sets user in session."""
        client.get("/johndoe")
        assert server.session["user"] == "johndoe"

