import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities

original_activities = copy.deepcopy(activities)

@pytest.fixture(autouse=True)
def reset_activities():
    activities.clear()
    activities.update(copy.deepcopy(original_activities))
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_all_activities():
    # Arrange
    client = TestClient(app)
    expected_activity_names = set(original_activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_data = response.json()
    assert set(response_data.keys()) == expected_activity_names
    assert response_data["Chess Club"]["description"] == original_activities["Chess Club"]["description"]


def test_signup_for_activity_adds_participant():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = "newstudent@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in activities[activity_name]["participants"]


def test_signup_for_activity_duplicate_returns_400():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = original_activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up"


def test_remove_participant_unregisters_user():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = original_activities[activity_name]["participants"][0]

    # Act
    response = client.delete(
        f"/activities/{encoded_activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email} from {activity_name}"}
    assert email not in activities[activity_name]["participants"]


def test_remove_nonexistent_participant_returns_404():
    # Arrange
    client = TestClient(app)
    activity_name = "Chess Club"
    encoded_activity = quote(activity_name, safe="")
    email = "missing@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{encoded_activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"


def test_remove_participant_from_missing_activity_returns_404():
    # Arrange
    client = TestClient(app)
    activity_name = "Unknown Club"
    encoded_activity = quote(activity_name, safe="")
    email = "anyone@mergington.edu"

    # Act
    response = client.delete(
        f"/activities/{encoded_activity}/participants",
        params={"email": email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
