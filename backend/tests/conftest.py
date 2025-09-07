"""Test configuration and utilities for Signal Bloom backend."""

import asyncio
import os
import tempfile
from pathlib import Path

import pytest
from starlette.applications import Starlette
from starlette.testclient import TestClient

# Set test environment variables
os.environ["DEBUG"] = "true"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DATABASE_URL"] = "sqlite:///test.db"


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def temp_db():
    """Create a temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as temp_file:
        temp_db_path = temp_file.name

    # Set the database URL to use our temp database
    original_db_url = os.environ.get("DATABASE_URL")
    os.environ["DATABASE_URL"] = f"sqlite:///{temp_db_path}"

    yield temp_db_path

    # Cleanup
    if original_db_url:
        os.environ["DATABASE_URL"] = original_db_url
    else:
        del os.environ["DATABASE_URL"]

    # Remove temp database file
    Path(temp_db_path).unlink(missing_ok=True)


@pytest.fixture
async def app():
    """Create a test application instance."""
    # Import here to avoid circular imports
    from main import create_app

    app = await create_app()
    return app


@pytest.fixture
def client(app):
    """Create a test client."""
    return TestClient(app)
