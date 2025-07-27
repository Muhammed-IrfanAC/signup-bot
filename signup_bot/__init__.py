# Signup Bot - A Discord bot for managing Clash of Clans event signups.
from pathlib import Path
import os
import base64
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot version
__version__ = "1.0.0"

# Base directory
BASE_DIR = Path(__file__).parent

# Configuration
class Config:
    """Configuration class for the bot."""
    DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
    API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8001')
    FIREBASE_CRED = os.getenv('FIREBASE_CRED')  # Base64 encoded Firebase credentials
    AUTH = os.getenv('AUTH')
    
    @classmethod
    def get_firebase_credentials(cls):
        """Get Firebase credentials from base64 encoded string."""
        if not cls.FIREBASE_CRED:
            raise ValueError("FIREBASE_CRED environment variable is required")
        
        try:
            # Decode base64 string
            decoded = base64.b64decode(cls.FIREBASE_CRED.encode('utf-8'))
            
            # Parse JSON
            credentials = json.loads(decoded.decode('utf-8'))
            return credentials
            
        except Exception as e:
            raise ValueError(f"Failed to decode Firebase credentials: {e}")
    
    # Validate required environment variables
    @classmethod
    def validate(cls):
        """Validate that all required environment variables are set."""
        required = ['DISCORD_TOKEN', 'FIREBASE_CRED', 'AUTH']
        missing = [var for var in required if not getattr(cls, var)]
        
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        # Test Firebase credentials decoding
        try:
            cls.get_firebase_credentials()
        except Exception as e:
            raise ValueError(f"Invalid Firebase credentials: {e}")

# Validate config on import
Config.validate()
