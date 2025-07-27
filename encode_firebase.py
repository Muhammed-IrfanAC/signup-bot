#!/usr/bin/env python3
"""
Utility script to encode Firebase credentials for environment variable use.
This script reads the Firebase JSON file and outputs the base64 encoded string.
"""

import base64
import json
import os
import sys

def encode_firebase_credentials(file_path: str) -> str:
    """
    Encode Firebase credentials file to base64.
    
    Args:
        file_path: Path to the Firebase JSON credentials file
        
    Returns:
        Base64 encoded string of the Firebase credentials
    """
    try:
        # Read the JSON file
        with open(file_path, 'rb') as f:
            content = f.read()
        
        # Encode to base64
        encoded = base64.b64encode(content).decode('utf-8')
        return encoded
        
    except FileNotFoundError:
        print(f"❌ Error: File not found at {file_path}")
        return None
    except Exception as e:
        print(f"❌ Error encoding file: {e}")
        return None

def decode_firebase_credentials(encoded_string: str) -> dict:
    """
    Decode base64 encoded Firebase credentials.
    
    Args:
        encoded_string: Base64 encoded Firebase credentials
        
    Returns:
        Dictionary containing the Firebase credentials
    """
    try:
        # Decode from base64
        decoded = base64.b64decode(encoded_string.encode('utf-8'))
        
        # Parse JSON
        credentials = json.loads(decoded.decode('utf-8'))
        return credentials
        
    except Exception as e:
        print(f"❌ Error decoding credentials: {e}")
        return None

def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) != 2:
        print("Usage: python encode_firebase.py <path_to_firebase_json>")
        print("Example: python encode_firebase.py discord-bot-dev-e0574-firebase-adminsdk-fbsvc-c0e73faa39.json")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    print(f"🔐 Encoding Firebase credentials from: {file_path}")
    print("=" * 60)
    
    # Encode the file
    encoded = encode_firebase_credentials(file_path)
    
    if encoded:
        print("✅ Successfully encoded Firebase credentials!")
        print()
        print("📋 Copy this to your .env file as FIREBASE_CRED:")
        print("=" * 60)
        print(encoded)
        print("=" * 60)
        print()
        print("💡 Usage in .env file:")
        print("FIREBASE_CRED=" + encoded)
        print()
        print("🔍 To verify the encoding, you can decode it back:")
        print("python encode_firebase.py --decode " + encoded[:50] + "...")
    else:
        print("❌ Failed to encode Firebase credentials")
        sys.exit(1)

if __name__ == "__main__":
    # Check if --decode flag is provided
    if len(sys.argv) == 3 and sys.argv[1] == "--decode":
        encoded_string = sys.argv[2]
        print("🔍 Decoding Firebase credentials...")
        print("=" * 60)
        
        credentials = decode_firebase_credentials(encoded_string)
        if credentials:
            print("✅ Successfully decoded Firebase credentials!")
            print()
            print("📋 Decoded credentials:")
            print("=" * 60)
            print(json.dumps(credentials, indent=2))
            print("=" * 60)
        else:
            print("❌ Failed to decode Firebase credentials")
            sys.exit(1)
    else:
        main() 