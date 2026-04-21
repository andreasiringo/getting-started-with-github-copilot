"""Unit tests for activity endpoints using AAA pattern (Arrange-Act-Assert)."""

import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """
        Arrange: client is ready
        Act: GET /
        Assert: redirect response to /static/index.html
        """
        # Act
        response = client.get("/", follow_redirects=False)
        
        # Assert
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivitiesEndpoint:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities_returns_dict(self, client, mock_activities):
        """
        Arrange: mock_activities fixture with 9 activities
        Act: GET /activities
        Assert: response contains all activities as dictionary
        """
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data

    def test_activity_structure_is_valid(self, client):
        """
        Arrange: client ready
        Act: GET /activities and check first activity
        Assert: activity has required fields
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        chess_club = data["Chess Club"]
        
        # Assert
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_contains_initial_participants(self, client, mock_activities):
        """
        Arrange: mock_activities has initial participants
        Act: GET /activities
        Assert: initial participants are present
        """
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        assert "michael@mergington.edu" in data["Chess Club"]["participants"]
        assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_successful_signup(self, client, mock_activities):
        """
        Arrange: client ready, Chess Club has space
        Act: POST /activities/Chess Club/signup?email=student@example.com
        Assert: status 200, student added to participants
        """
        # Arrange
        email = "student@example.com"
        
        # Act
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for Chess Club"

    def test_signup_adds_participant_to_activity(self, client, mock_activities):
        """
        Arrange: client ready, student not yet signed up
        Act: POST signup, then GET /activities
        Assert: student appears in participants list
        """
        # Arrange
        email = "newstudent@example.com"
        
        # Act
        client.post(f"/activities/Chess Club/signup?email={email}")
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        assert email in data["Chess Club"]["participants"]

    def test_signup_to_nonexistent_activity_fails(self, client):
        """
        Arrange: client ready, activity does not exist
        Act: POST /activities/Nonexistent Activity/signup
        Assert: status 404, error message
        """
        # Act
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@example.com"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_duplicate_signup_fails(self, client, mock_activities):
        """
        Arrange: client ready, michael@mergington.edu already in Chess Club
        Act: POST signup with same email to same activity
        Assert: status 400, error message about duplicate
        """
        # Arrange
        email = "michael@mergington.edu"
        
        # Act
        response = client.post(f"/activities/Chess Club/signup?email={email}")
        
        # Assert
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_when_activity_full_fails(self, client, mock_activities):
        """
        Arrange: client ready, create activity at max capacity
        Act: attempt to signup when at capacity
        Assert: status 400, activity full error
        """
        # Arrange - Get current state
        response = client.get("/activities")
        data = response.json()
        
        # Find an activity that's near capacity or we'll fill it manually
        # For this test, let's check Gym Class which has max 30 and 2 participants
        # Add many participants to fill it
        for i in range(30):
            email = f"student{i}@example.com"
            if i < 28:  # First 28 succeed (2 already exist + 28 = 30)
                client.post(f"/activities/Gym Class/signup?email={email}")
        
        # Act - Try to signup when full
        response = client.post("/activities/Gym Class/signup?email=overflow@example.com")
        
        # Assert
        assert response.status_code == 400
        assert "Activity is full" in response.json()["detail"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants endpoint."""

    def test_successful_participant_removal(self, client, mock_activities):
        """
        Arrange: client ready, michael@mergington.edu in Chess Club
        Act: DELETE /activities/Chess Club/participants?email=michael@mergington.edu
        Assert: status 200, participant removed
        """
        # Arrange
        email = "michael@mergington.edu"
        
        # Act
        response = client.delete(
            f"/activities/Chess Club/participants?email={email}"
        )
        
        # Assert
        assert response.status_code == 200
        assert f"Removed {email} from Chess Club" in response.json()["message"]

    def test_removal_deletes_from_participants_list(self, client, mock_activities):
        """
        Arrange: client ready, michael in Chess Club
        Act: DELETE, then GET /activities
        Assert: michael no longer in Chess Club participants
        """
        # Arrange
        email = "michael@mergington.edu"
        
        # Act
        client.delete(f"/activities/Chess Club/participants?email={email}")
        response = client.get("/activities")
        
        # Assert
        data = response.json()
        assert email not in data["Chess Club"]["participants"]

    def test_remove_from_nonexistent_activity_fails(self, client):
        """
        Arrange: client ready, activity does not exist
        Act: DELETE /activities/Fake Activity/participants
        Assert: status 404, activity not found error
        """
        # Act
        response = client.delete(
            "/activities/Fake Activity/participants?email=student@example.com"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_nonexistent_participant_fails(self, client):
        """
        Arrange: client ready, participant not in activity
        Act: DELETE with email not in Chess Club
        Assert: status 404, participant not found error
        """
        # Act
        response = client.delete(
            "/activities/Chess Club/participants?email=nothere@example.com"
        )
        
        # Assert
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]
