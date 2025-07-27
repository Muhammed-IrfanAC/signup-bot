#!/usr/bin/env python3
"""
Simple test script to verify role management feature.
This script tests the API endpoints without requiring Discord.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"
TEST_GUILD_ID = "123456789"
TEST_CHANNEL_ID = "987654321"

def test_create_event_with_role():
    """Test creating an event with a role."""
    print("Testing create event with role...")
    
    data = {
        "event_name": "Test War Event",
        "guild_id": TEST_GUILD_ID,
        "channel_id": TEST_CHANNEL_ID,
        "role_id": "555666777"  # Test role ID
    }
    
    response = requests.post(f"{API_BASE_URL}/events", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Success: {result}")
        return result.get('event_name')
    else:
        print(f"Error: {response.text}")
        return None

def test_create_event_without_role():
    """Test creating an event without a role."""
    print("Testing create event without role...")
    
    data = {
        "event_name": "Test Event No Role",
        "guild_id": TEST_GUILD_ID,
        "channel_id": TEST_CHANNEL_ID
        # No role_id
    }
    
    response = requests.post(f"{API_BASE_URL}/events", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Success: {result}")
        return result.get('event_name')
    else:
        print(f"Error: {response.text}")
        return None

def test_signup_with_role(event_name):
    """Test signing up for an event with role assignment."""
    print(f"Testing signup for {event_name}...")
    
    data = {
        "player_tag": "#TEST123",
        "discord_name": "TestUser#1234",
        "discord_user_id": "111222333",
        "guild_id": TEST_GUILD_ID
    }
    
    response = requests.post(f"{API_BASE_URL}/events/{event_name}/signup", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 201:
        result = response.json()
        print(f"Success: {result}")
        print(f"Role ID returned: {result.get('role_id')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_remove_with_role(event_name):
    """Test removing from an event with role removal."""
    print(f"Testing removal from {event_name}...")
    
    data = {
        "player_tag": "#TEST123",
        "discord_name": "TestUser#1234",
        "guild_id": TEST_GUILD_ID,
        "user_roles": ["111222333"]  # Test user roles
    }
    
    response = requests.post(f"{API_BASE_URL}/events/{event_name}/remove", json=data)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result}")
        print(f"Role ID returned: {result.get('role_id')}")
        print(f"Is self removal: {result.get('is_self_removal')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def test_list_events():
    """Test listing events to see role information."""
    print("Testing list events...")
    
    response = requests.get(f"{API_BASE_URL}/events", params={"guild_id": TEST_GUILD_ID})
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        events = result.get('events', [])
        print(f"Found {len(events)} events:")
        for event in events:
            print(f"  - {event.get('event_name')}: {event.get('signup_count', 0)} signups, role_id: {event.get('role_id', 'None')}")
        return True
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("=== Role Management Feature Test ===\n")
    
    # Test creating events
    event_with_role = test_create_event_with_role()
    event_without_role = test_create_event_without_role()
    
    print("\n" + "="*50 + "\n")
    
    # Test signup with role
    if event_with_role:
        test_signup_with_role(event_with_role)
    
    print("\n" + "="*50 + "\n")
    
    # Test removal with role
    if event_with_role:
        test_remove_with_role(event_with_role)
    
    print("\n" + "="*50 + "\n")
    
    # Test listing events
    test_list_events()
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 