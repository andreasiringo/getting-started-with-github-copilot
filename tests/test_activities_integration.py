"""Integration tests for activity endpoints using AAA pattern."""

import pytest


class TestSignupAndRemovalFlow:
    """Integration tests combining multiple endpoints."""

    def test_signup_then_verify_in_list(self, client, mock_activities):
        """
        Arrange: client ready, unregistered student
        Act: POST signup, then GET /activities
        Assert: student appears in GET response and in participant list
        """
        # Arrange
        email = "integration@example.com"
        activity_name = "Chess Club"
        
        # Act - Signup
        signup_response = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Act - Get activities to verify
        activities_response = client.get("/activities")
        
        # Assert
        assert signup_response.status_code == 200
        assert activities_response.status_code == 200
        activities_data = activities_response.json()
        assert email in activities_data[activity_name]["participants"]

    def test_signup_then_remove_then_signup_again(self, client, mock_activities):
        """
        Arrange: client ready, student not registered
        Act: signup → remove → signup again
        Assert: all operations succeed and final state has student
        """
        # Arrange
        email = "cycle@example.com"
        activity_name = "Programming Class"
        
        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Act - Remove
        response2 = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Act - Signup again
        response3 = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Act - Verify in list
        response4 = client.get("/activities")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response3.status_code == 200
        assert response4.status_code == 200
        assert email in response4.json()[activity_name]["participants"]

    def test_multiple_students_signup_and_remove(self, client, mock_activities):
        """
        Arrange: client ready, 3 students not registered
        Act: all signup, remove first, verify others remain
        Assert: correct students present after operations
        """
        # Arrange
        emails = ["multi1@example.com", "multi2@example.com", "multi3@example.com"]
        activity_name = "Art Studio"
        
        # Act - All signup
        for email in emails:
            client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act - Remove first
        client.delete(f"/activities/{activity_name}/participants?email={emails[0]}")
        
        # Act - Verify state
        response = client.get("/activities")
        participants = response.json()[activity_name]["participants"]
        
        # Assert
        assert emails[0] not in participants
        assert emails[1] in participants
        assert emails[2] in participants

    def test_activity_capacity_enforcement_across_signups(self, client, mock_activities):
        """
        Arrange: Tennis Club has max 16, initially 2 participants
        Act: signup students until full, then try to add one more
        Assert: can add up to capacity, then 16th fails
        """
        # Arrange
        activity_name = "Tennis Club"
        base_emails = [f"capacity{i}@example.com" for i in range(14)]  # Need 14 more for 16 total
        
        # Act - Fill to capacity
        responses = []
        for email in base_emails:
            response = client.post(f"/activities/{activity_name}/signup?email={email}")
            responses.append(response)
        
        # Act - Try one more (should fail)
        overflow_response = client.post(
            f"/activities/{activity_name}/signup?email=overflow@example.com"
        )
        
        # Assert - All first 14 succeed
        for response in responses:
            assert response.status_code == 200
        
        # Assert - Overflow fails
        assert overflow_response.status_code == 400
        assert "Activity is full" in overflow_response.json()["detail"]

    def test_remove_from_full_activity_allows_new_signup(self, client, mock_activities):
        """
        Arrange: activity at capacity with a student
        Act: remove one student, then new student signs up
        Assert: new signup succeeds
        """
        # Arrange
        activity_name = "Tennis Club"
        # Fill it first with 14 students
        for i in range(14):
            client.post(f"/activities/{activity_name}/signup?email=temp{i}@example.com")
        
        # Find a participant to remove (sarah or alex)
        remove_email = "sarah@mergington.edu"
        new_email = "after_removal@example.com"
        
        # Act - Remove one
        response1 = client.delete(f"/activities/{activity_name}/participants?email={remove_email}")
        
        # Act - Try to signup
        response2 = client.post(f"/activities/{activity_name}/signup?email={new_email}")
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        # Verify new student is in list
        response3 = client.get("/activities")
        assert new_email in response3.json()[activity_name]["participants"]
        assert remove_email not in response3.json()[activity_name]["participants"]

    def test_duplicate_signup_after_removal_succeeds(self, client, mock_activities):
        """
        Arrange: client ready, student in activity
        Act: remove student, then signup again
        Assert: both operations succeed
        """
        # Arrange
        email = "duplicate_test@example.com"
        activity_name = "Music Band"
        
        # Act - First signup
        client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Act - Remove
        response_remove = client.delete(
            f"/activities/{activity_name}/participants?email={email}"
        )
        
        # Act - Signup again (should succeed, no longer marked as duplicate)
        response_signup = client.post(
            f"/activities/{activity_name}/signup?email={email}"
        )
        
        # Assert
        assert response_remove.status_code == 200
        assert response_signup.status_code == 200
        
        # Verify in list
        response_list = client.get("/activities")
        assert email in response_list.json()[activity_name]["participants"]

    def test_cross_activity_signup_independence(self, client, mock_activities):
        """
        Arrange: client ready, student not in any activity
        Act: signup to multiple activities
        Assert: student appears in all activities without conflicts
        """
        # Arrange
        email = "multi_activity@example.com"
        activities_to_join = ["Chess Club", "Programming Class", "Art Studio"]
        
        # Act - Signup to all
        for activity in activities_to_join:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200
        
        # Act - Verify all
        response_list = client.get("/activities")
        data = response_list.json()
        
        # Assert - In all activities
        for activity in activities_to_join:
            assert email in data[activity]["participants"], \
                f"Email {email} not found in {activity}"
