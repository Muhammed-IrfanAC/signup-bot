# Tests for the API routes.
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from signup_bot.api import create_app

@pytest.fixture
def client():
    """Create a test client for the API."""
    app = create_app()
    return TestClient(app)

def test_health_check(client):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@patch('firebase_admin.firestore.client')
def test_create_event(mock_firestore, client):
    """Test creating a new event."""
    # Mock the Firestore client
    mock_db = MagicMock()
    mock_firestore.return_value = mock_db
    
    # Mock the document operations
    mock_doc = MagicMock()
    mock_doc.get.return_value.exists = False
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc
    mock_db.collection.return_value = mock_collection
    
    # Test data
    event_data = {
        "event_name": "Test Event",
        "guild_id": "12345"
    }
    
    # Make the request
    response = client.post("/api/events", json=event_data)
    
    # Verify the response
    assert response.status_code == 201
    assert "message" in response.json()
    assert response.json()["event_name"] == "Test Event"
    
    # Verify the document was created
    mock_doc.set.assert_called_once()

@patch('firebase_admin.firestore.client')
def test_get_events(mock_firestore, client):
    """Test getting a list of events."""
    # Mock the Firestore client
    mock_db = MagicMock()
    mock_firestore.return_value = mock_db
    
    # Mock the collection query
    mock_doc = MagicMock()
    mock_doc.to_dict.return_value = {"event_name": "Test Event"}
    mock_collection = MagicMock()
    mock_collection.stream.return_value = [mock_doc]
    mock_db.collection.return_value = mock_collection
    
    # Make the request
    response = client.get("/api/events?guild_id=12345")
    
    # Verify the response
    assert response.status_code == 200
    assert "events" in response.json()
    assert len(response.json()["events"]) == 1
    assert response.json()["events"][0]["event_name"] == "Test Event"

@patch('firebase_admin.firestore.client')
def test_signup_player(mock_firestore, client):
    """Test signing up a player for an event."""
    # Mock the Firestore client
    mock_db = MagicMock()
    mock_firestore.return_value = mock_db
    
    # Mock the document operations
    mock_doc = MagicMock()
    mock_doc.get.return_value.exists = True
    mock_doc.get.return_value.to_dict.return_value = {"is_open": True, "signup_count": 0}
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc
    mock_collection.where.return_value.limit.return_value.get.return_value = []
    mock_db.collection.return_value = mock_collection
    
    # Mock the player data
    with patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {
            "name": "TestPlayer",
            "townHallLevel": 12
        }
        
        # Test data
        signup_data = {
            "player_tag": "#TEST123",
            "discord_name": "TestUser#1234",
            "guild_id": "12345"
        }
        
        # Make the request
        response = client.post("/api/events/Test%20Event/signup", json=signup_data)
        
        # Verify the response
        assert response.status_code == 201
        assert "message" in response.json()
        assert response.json()["player_name"] == "TestPlayer"
        
        # Verify the document was updated
        mock_doc.update.assert_called_once()

@patch('firebase_admin.firestore.client')
def test_export_event(mock_firestore, client):
    """Test exporting an event to Excel."""
    # Mock the Firestore client
    mock_db = MagicMock()
    mock_firestore.return_value = mock_db
    
    # Mock the document operations
    mock_doc = MagicMock()
    mock_doc.get.return_value.exists = True
    mock_collection = MagicMock()
    mock_collection.document.return_value = mock_doc
    
    # Mock the signups collection
    mock_signup = MagicMock()
    mock_signup.to_dict.return_value = {
        "index": 1,
        "player_name": "TestPlayer",
        "player_tag": "#TEST123",
        "player_th": 12,
        "discord_name": "TestUser#1234",
        "signed_up_at": "2023-01-01T00:00:00"
    }
    mock_signups_collection = MagicMock()
    mock_signups_collection.order_by.return_value.stream.return_value = [mock_signup]
    mock_collection.document.return_value.collection.return_value = mock_signups_collection
    
    mock_db.collection.return_value = mock_collection
    
    # Make the request
    response = client.get("/api/events/Test%20Event/export?guild_id=12345")
    
    # Verify the response
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "content-disposition" in response.headers
    assert "Test_Event_export.xlsx" in response.headers["content-disposition"]
