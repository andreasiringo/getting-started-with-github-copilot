"""Pytest fixtures for FastAPI testing."""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def mock_activities():
    """Create a clean copy of activities for each test to ensure isolation."""
    return deepcopy(activities)


@pytest.fixture
def client(mock_activities):
    """Create a TestClient with mocked activities."""
    import src.app

    # Store the original module-level activities before overriding
    original_activities = src.app.activities

    # Override the activities in the app module
    src.app.activities = mock_activities

    # Create the test client
    test_client = TestClient(app)

    try:
        yield test_client
    finally:
        test_client.close()

        # Restore original activities after the test
        if original_activities is not None:
            src.app.activities = original_activities


@pytest.fixture
def app_instance():
    """Provide the FastAPI app instance."""
    return app
