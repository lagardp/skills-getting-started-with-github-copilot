import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture(scope="function")
def client():
    """Fixture to provide a TestClient for the FastAPI app."""
    return TestClient(app)


# Store the original activities state
original_activities = copy.deepcopy(activities)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to original state before each test."""
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
