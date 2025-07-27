"""
Emoji configuration for the Signup Bot.
Handles different emoji IDs for development and production environments.
"""

import os
from typing import Dict

# Environment detection
def is_production() -> bool:
    """Check if running in production environment."""
    # You can customize this based on your deployment setup
    return os.getenv('ENVIRONMENT', 'dev').lower() == 'prod'

# Emoji configurations
DEVELOPMENT_EMOJIS = {
    "loading": "<a:loading:1398868096818610187>",
    "success": "<a:success:1398882295154343967>",
    "error": "<a:error:1398882317312856235>"
}

PRODUCTION_EMOJIS = {
    "loading": "<a:loading:1398892117081722940>",
    "success": "<a:success:1337039802968707133>",
    "error": "<a:error:1337040970260418630>"
}

def get_emoji_config() -> Dict[str, str]:
    """Get emoji configuration based on environment."""
    if is_production():
        return PRODUCTION_EMOJIS
    else:
        return DEVELOPMENT_EMOJIS

def get_loading_emoji() -> str:
    """Get loading emoji for current environment."""
    return get_emoji_config()["loading"]

def get_success_emoji() -> str:
    """Get success emoji for current environment."""
    return get_emoji_config()["success"]

def get_error_emoji() -> str:
    """Get error emoji for current environment."""
    return get_emoji_config()["error"]

# Convenience function to get all emojis
def get_all_emojis() -> Dict[str, str]:
    """Get all emojis for current environment."""
    return get_emoji_config() 