"""
Tests for the Mergington High School Activities API
Uses the AAA (Arrange-Act-Assert) pattern for test structure
"""
import pytest
from fastapi.testclient import TestClient


class TestGetRoot:
    """Tests for GET / endpoint"""

    def test_root_redirects_to_static_index(self, client):
        # Arrange
        expected_redirect_url = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == expected_redirect_url


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        # Arrange
        expected_activity_count = 9
        expected_keys = {"description", "schedule", "max_participants", "participants"}

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert len(data) == expected_activity_count
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert set(activity_details.keys()) == expected_keys

    def test_get_activities_returns_correct_participants(self, client):
        # Arrange
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert "Chess Club" in data
        assert data["Chess Club"]["participants"] == ["michael@mergington.edu", "daniel@mergington.edu"]

    def test_get_activities_response_structure(self, client):
        # Arrange
        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        chess_club = data["Chess Club"]
        assert chess_club["max_participants"] == 12
        assert isinstance(chess_club["description"], str)
        assert isinstance(chess_club["schedule"], str)
        assert isinstance(chess_club["participants"], list)


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_new_participant_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"
        initial_count = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        updated_activities = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in updated_activities[activity_name]["participants"]
        assert len(updated_activities[activity_name]["participants"]) == initial_count + 1

    def test_signup_duplicate_participant_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already signed up

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_with_special_characters_in_email(self, client):
        # Arrange
        activity_name = "Programming Class"
        email = "student+tag@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        updated_activities = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert email in updated_activities[activity_name]["participants"]

    def test_signup_with_special_characters_in_activity_name(self, client):
        # Arrange
        activity_name = "Art Studio"  # Activity with space in name
        email = "artist@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"


class TestRemoveFromActivity:
    """Tests for DELETE /activities/{activity_name}/remove endpoint"""

    def test_remove_existing_participant_success(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        initial_count = len(client.get("/activities").json()[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        updated_activities = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Removed {email} from {activity_name}"
        assert email not in updated_activities[activity_name]["participants"]
        assert len(updated_activities[activity_name]["participants"]) == initial_count - 1

    def test_remove_nonexistent_participant_returns_400(self, client):
        # Arrange
        activity_name = "Chess Club"
        email = "nonexistent@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Participant not found"

    def test_remove_from_nonexistent_activity_returns_404(self, client):
        # Arrange
        activity_name = "Nonexistent Club"
        email = "student@mergington.edu"

        # Act
        response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )

        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_then_signup_same_participant(self, client):
        # Arrange
        activity_name = "Programming Class"
        email = "emma@mergington.edu"

        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )
        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        final_activities = client.get("/activities").json()

        # Assert
        assert remove_response.status_code == 200
        assert signup_response.status_code == 200
        assert email in final_activities[activity_name]["participants"]


class TestIntegrationScenarios:
    """Integration tests combining multiple operations"""

    def test_full_lifecycle_signup_and_remove(self, client):
        # Arrange
        activity_name = "Tennis Club"
        email = "newplayer@mergington.edu"

        # Act - Verify activity exists
        get_response = client.get("/activities")
        assert activity_name in get_response.json()

        # Act - Sign up
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )

        # Assert signup success
        assert signup_response.status_code == 200
        assert email in client.get("/activities").json()[activity_name]["participants"]

        # Act - Remove
        remove_response = client.delete(
            f"/activities/{activity_name}/remove",
            params={"email": email}
        )

        # Assert remove success
        assert remove_response.status_code == 200
        assert email not in client.get("/activities").json()[activity_name]["participants"]

    def test_multiple_signups_in_sequence(self, client):
        # Arrange
        activity_name = "Drama Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]

        # Act
        responses = []
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            responses.append(response)

        final_activity = client.get("/activities").json()[activity_name]

        # Assert
        assert all(r.status_code == 200 for r in responses)
        assert all(email in final_activity["participants"] for email in emails)
        assert len(final_activity["participants"]) >= 3
