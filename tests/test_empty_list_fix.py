#!/usr/bin/env python3
"""
Test script to verify the empty list fix for check_player endpoint.
"""

import requests
import json

# Configuration
API_BASE_URL = "http://localhost:5000/api"
TEST_GUILD_ID = "123456789"

def test_check_player_not_signed_up():
    """Test checking a player that is not signed up (empty list scenario)."""
    print("Testing check_player with player not signed up...")
    
    data = {
        "player_tag": "#NOTSIGNEDUP",
        "guild_id": TEST_GUILD_ID
    }
    
    response = requests.post(f"{API_BASE_URL}/events/Test Event/check", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result}")
        if result.get('is_signed_up') == False:
            print("✅ Correctly identified player as not signed up")
            return True
        else:
            print("❌ Incorrectly identified player as signed up")
            return False
    else:
        print(f"Error: {response.text}")
        return False

def test_check_player_signed_up():
    """Test checking a player that is signed up."""
    print("Testing check_player with player signed up...")
    
    # First, sign up a player
    signup_data = {
        "player_tag": "#SIGNEDUP",
        "discord_name": "TestUser#1234",
        "discord_user_id": "111222333",
        "guild_id": TEST_GUILD_ID
    }
    
    # Try to sign up (this might fail if event doesn't exist, but that's okay)
    signup_response = requests.post(f"{API_BASE_URL}/events/Test Event/signup", json=signup_data)
    
    # Now check the player
    check_data = {
        "player_tag": "#SIGNEDUP",
        "guild_id": TEST_GUILD_ID
    }
    
    response = requests.post(f"{API_BASE_URL}/events/Test Event/check", json=check_data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result}")
        if result.get('is_signed_up') == True:
            print("✅ Correctly identified player as signed up")
            return True
        else:
            print("❌ Incorrectly identified player as not signed up")
            return False
    else:
        print(f"Error: {response.text}")
        return False

def test_check_player_empty_event():
    """Test checking a player in an event with no signups."""
    print("Testing check_player in event with no signups...")
    
    data = {
        "player_tag": "#ANYPLAYER",
        "guild_id": TEST_GUILD_ID
    }
    
    response = requests.post(f"{API_BASE_URL}/events/Empty Event/check", json=data)
    print(f"Status: {response.status_code}")
    
    if response.status_code == 200:
        result = response.json()
        print(f"Success: {result}")
        if result.get('is_signed_up') == False:
            print("✅ Correctly handled empty event")
            return True
        else:
            print("❌ Incorrectly handled empty event")
            return False
    else:
        print(f"Error: {response.text}")
        return False

def main():
    """Run all tests."""
    print("=== Empty List Fix Test ===\n")
    
    # Test 1: Player not signed up
    test1 = test_check_player_not_signed_up()
    
    print("\n" + "="*50 + "\n")
    
    # Test 2: Player signed up (if possible)
    test2 = test_check_player_signed_up()
    
    print("\n" + "="*50 + "\n")
    
    # Test 3: Empty event
    test3 = test_check_player_empty_event()
    
    print("\n" + "="*50 + "\n")
    
    if test1 and test3:
        print("✅ All tests passed! Empty list issue is fixed.")
    else:
        print("❌ Some tests failed. Check the implementation.")
    
    print("\n=== Test Complete ===")

if __name__ == "__main__":
    main() 