"""
Main entry point for the Signup Bot.
"""
import asyncio
import logging
import os
from dotenv import load_dotenv

from signup_bot.bot import SignupBot

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """Run the bot."""
    # Load environment variables
    load_dotenv()
    
    # Check required environment variables
    required_vars = ['DISCORD_TOKEN', 'FIREBASE_CRED', 'AUTH']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        return
    
    # Create and run the bot
    bot = SignupBot()
    bot.run(os.getenv('DISCORD_TOKEN'))

if __name__ == "__main__":
    main()
