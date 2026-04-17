"""
Comprehensive test suite for the Mergington High School Activities API.

Tests cover all endpoints with success cases, error handling, and edge cases.
Uses AAA (Arrange-Act-Assert) pattern throughout.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Provide a TestClient for API testing."""
    return TestClient(app)


# ===========================
# GET / (Root Redirect)
# ===========================

def test_root_redirect(client):
    """
    Arrange: No setup needed
    Act: GET /
    Assert: Returns redirect to /static/index.html
    """
    # Act
    response = client.get("/", follow_redirects=False)
    
    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


# ===========================
# GET /activities
# ===========================

def test_get_all_activities(client):
    """
    Arrange: API has predefined activities
    Act: GET /activities
    Assert: Returns all activities with correct structure
    """
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    assert response.status_code == 200
    assert isinstance(data, dict)
    assert len(data) == 9  # 9 predefined activities
    
    # Verify each activity has required fields
    for activity_name, activity_details in data.items():
        assert isinstance(activity_name, str)
        assert "description" in activity_details
        assert "schedule" in activity_details
        assert "max_participants" in activity_details
        assert "participants" in activity_details
        assert isinstance(activity_details["participants"], list)


def test_get_activities_contains_chess_club(client):
    """
    Arrange: Chess Club is a predefined activity
    Act: GET /activities
    Assert: Response includes Chess Club with initial participants
    """
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    assert "Chess Club" in data
    assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
    assert "michael@mergington.edu" in data["Chess Club"]["participants"]
    assert "daniel@mergington.edu" in data["Chess Club"]["participants"]


def test_get_activities_participant_counts(client):
    """
    Arrange: Each activity has predefined participants
    Act: GET /activities
    Assert: Participant counts match actual list lengths
    """
    # Act
    response = client.get("/activities")
    data = response.json()
    
    # Assert
    for activity_name, activity_details in data.items():
        participant_count = len(activity_details["participants"])
        assert participant_count <= activity_details["max_participants"]
        assert participant_count > 0  # All activities have at least 1 participant


# ===========================
# POST /activities/{activity_name}/signup
# ===========================

def test_signup_success(client):
    """
    Arrange: Valid activity, unique email
    Act: POST /activities/Chess Club/signup?email=test@example.com
    Assert: Returns 200 with success message, participant added
    """
    # Arrange
    activity_name = "Chess Club"
    email = "test_signup_success@example.com"
    initial_count = len(activities[activity_name]["participants"])
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert email in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count + 1


def test_signup_duplicate_prevention(client):
    """
    Arrange: Student already signed up for an activity
    Act: Attempt to sign up the same student again
    Assert: Returns 400 with error message, student not added twice
    """
    # Arrange
    activity_name = "Programming Class"
    email = "duplicate_test@example.com"
    
    # First signup
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    initial_count = len(activities[activity_name]["participants"])
    
    # Act: Attempt duplicate signup
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "already signed up" in data["detail"].lower()
    # Ensure participant wasn't added twice
    assert len(activities[activity_name]["participants"]) == initial_count


def test_signup_activity_not_found(client):
    """
    Arrange: Activity does not exist
    Act: POST /activities/Nonexistent Activity/signup?email=test@example.com
    Assert: Returns 404 with error message
    """
    # Act
    response = client.post(
        "/activities/Nonexistent Activity/signup",
        params={"email": "test@example.com"}
    )
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_signup_with_special_characters_in_email(client):
    """
    Arrange: Email with special characters that need URL encoding
    Act: POST /activities/Art Club/signup?email=test+user@example.com
    Assert: Returns 200, email properly stored
    """
    # Arrange
    activity_name = "Art Club"
    email = "test+special@example.com"
    
    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_signup_multiple_different_students(client):
    """
    Arrange: Multiple unique students signing up
    Act: Three different students sign up for same activity
    Assert: All successfully added without interference
    """
    # Arrange
    activity_name = "Drama Club"
    students = [
        "student1_multi@example.com",
        "student2_multi@example.com",
        "student3_multi@example.com"
    ]
    initial_count = len(activities[activity_name]["participants"])
    
    # Act & Assert for each student
    for student_email in students:
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": student_email}
        )
        assert response.status_code == 200
        assert student_email in activities[activity_name]["participants"]
    
    # Final assert
    assert len(activities[activity_name]["participants"]) == initial_count + 3


# ===========================
# DELETE /activities/{activity_name}/signup
# ===========================

def test_unregister_success(client):
    """
    Arrange: Student is signed up for activity
    Act: DELETE /activities/Debate Team/signup?email=student@example.com
    Assert: Returns 200, participant removed
    """
    # Arrange
    activity_name = "Debate Team"
    email = "unregister_test@example.com"
    
    # Sign up first
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    initial_count = len(activities[activity_name]["participants"])
    assert email in activities[activity_name]["participants"]
    
    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    
    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert email in data["message"]
    assert email not in activities[activity_name]["participants"]
    assert len(activities[activity_name]["participants"]) == initial_count - 1


def test_unregister_not_registered(client):
    """
    Arrange: Student is NOT signed up for activity
    Act: DELETE /activities/Science Club/signup?email=notregistered@example.com
    Assert: Returns 400 with error message
    """
    # Act
    response = client.delete(
        "/activities/Science Club/signup",
        params={"email": "not_registered_test@example.com"}
    )
    
    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "not registered" in data["detail"].lower()


def test_unregister_activity_not_found(client):
    """
    Arrange: Activity does not exist
    Act: DELETE /activities/Fake Activity/signup?email=test@example.com
    Assert: Returns 404 with error message
    """
    # Act
    response = client.delete(
        "/activities/Fake Activity/signup",
        params={"email": "test@example.com"}
    )
    
    # Assert
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data
    assert "not found" in data["detail"].lower()


def test_signup_then_unregister_cycle(client):
    """
    Arrange: Clean activity state
    Act: Sign up, verify added, unregister, verify removed
    Assert: All operations succeed, no orphaned records
    """
    # Arrange
    activity_name = "Basketball Team"
    email = "cycle_test@example.com"
    
    # Act 1: Sign up
    response1 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response1.status_code == 200
    assert email in activities[activity_name]["participants"]
    
    # Act 2: Unregister
    response2 = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response2.status_code == 200
    assert email not in activities[activity_name]["participants"]
    
    # Act 3: Sign up again (should succeed)
    response3 = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )
    assert response3.status_code == 200
    assert email in activities[activity_name]["participants"]


def test_unregister_preserves_other_participants(client):
    """
    Arrange: Activity has multiple participants
    Act: Unregister one participant
    Assert: Other participants remain unchanged
    """
    # Arrange
    activity_name = "Track and Field"
    emails_to_keep = list(activities[activity_name]["participants"])  # Copy original
    email_to_remove = "participant_to_remove@example.com"
    
    # Add new participant
    client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email_to_remove}
    )
    
    # Act: Remove the new participant
    response = client.delete(
        f"/activities/{activity_name}/signup",
        params={"email": email_to_remove}
    )
    
    # Assert
    assert response.status_code == 200
    assert email_to_remove not in activities[activity_name]["participants"]
    # Verify original participants still exist
    for original_email in emails_to_keep:
        assert original_email in activities[activity_name]["participants"]
