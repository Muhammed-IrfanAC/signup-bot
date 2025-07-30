# Main Discord bot module for the Signup Bot.
import logging
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import List
import os
from datetime import datetime
import firebase_admin
from firebase_admin import firestore

from . import __version__, Config
from .api import Config as APIConfig
import aiohttp
from .cogs.events import EventView
from .utils.logger import EventLogger

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize Firebase
import firebase_admin
from firebase_admin import credentials

try:
    # Get Firebase credentials
    firebase_creds = Config.get_firebase_credentials()
    cred = credentials.Certificate(firebase_creds)
    firebase_admin.initialize_app(cred)
    logger.info("Firebase initialized successfully")
except Exception as e:
    logger.error(f"Failed to initialize Firebase: {e}")

async def get_all_events(bot):
    """Fetch all events for all guilds the bot is in."""
    events_to_register = []
    async with aiohttp.ClientSession() as session:
        for guild in bot.guilds:
            async with session.get(f"{APIConfig.API_BASE_URL}/api/events", params={"guild_id": guild.id}) as resp:
                if resp.status != 200:
                    logger.warning(f"Failed to fetch events for guild {guild.id}: {resp.status}")
                    continue
                data = await resp.json()
                events = data.get("events", [])
                for event in events:
                    event_name = event.get("event_name")
                    is_open = event.get("is_open", True)
                    if event_name:
                        events_to_register.append((event_name, is_open))
    return events_to_register

class SignupBot(commands.Bot):
    """Main bot class for the Signup Bot."""
    
    def __init__(self):
        """Initialize the bot with required intents and command prefix."""
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or('!'),
            intents=intents,
            activity=discord.Game(name="Starting up..."),
        )
        
        # Store TH counts for each event
        self.th_counts = {}
        self.start_time = datetime.utcnow()  # Track when bot started
        self.initial_extensions = [
            'signup_bot.cogs.admin',
            'signup_bot.cogs.events',
            'signup_bot.cogs.utilities'
        ]
    
    async def setup_hook(self) -> None:
        """Set up the bot when it starts."""
        logger.info("Loading extensions...")
        for extension in self.initial_extensions:
            try:
                await self.load_extension(extension)
                logger.info(f"Loaded extension: {extension}")
            except Exception as e:
                logger.error(f"Failed to load extension {extension}: {e}")
        
        # Sync commands
        await self.tree.sync()
        logger.info("Commands synced")

    async def on_ready(self) -> None:
        """Called when the bot is ready."""
        logger.info(f"Logged in as {self.user}")
        logger.info(f"Bot is in {len(self.guilds)} guilds")
        
        # Register persistent views for all events
        try:
            events = await get_all_events(self)
            logger.info(f"Found {len(events)} events to register persistent views for")
            for event_name, is_open in events:
                self.add_view(EventView(event_name, closed=not is_open))
            logger.info("Persistent event views registered successfully")
        except Exception as e:
            logger.error(f"Failed to register persistent views: {e}")
        
        # Start background task to process log entries
        self.loop.create_task(self.process_log_entries())
        
        await self.update_activity()
    
    async def update_activity(self):
        """Update the bot's activity with dynamic name."""
        try:
            bot_name = self.user.name if self.user else "Signup Bot"
            
            activity = discord.Game(name=f"{bot_name} v{__version__}")
            await self.change_presence(activity=activity)
            
            logger.info(f"Updated activity to: Playing {bot_name} v{__version__}")
            
        except Exception as e:
            logger.error(f"Failed to update activity: {e}")
            await self.change_presence(activity=discord.Game(name=f"Signup Bot v{__version__}"))
    
    async def process_log_entries(self):
        """Background task to process log entries and send them to Discord."""
        db = firestore.client()
        
        while True:
            try:
                # Get all guilds the bot is in
                for guild in self.guilds:
                    # Get all events for this guild
                    events_ref = db.collection('servers').document(str(guild.id)).collection('events')
                    events = events_ref.stream()
                    
                    for event_doc in events:
                        event_name = event_doc.id
                        event_data = event_doc.to_dict()
                        log_channel_id = event_data.get('log_channel_id')
                        
                        if not log_channel_id:
                            continue
                        
                        # Get unprocessed log entries
                        logs_ref = event_doc.reference.collection('logs')
                        unprocessed_logs = logs_ref.where('processed', '==', False).stream()
                        
                        for log_doc in unprocessed_logs:
                            log_data = log_doc.to_dict()
                            
                            try:
                                # Send the log entry to Discord
                                await EventLogger.log_action(
                                    bot=self,
                                    guild_id=int(log_data['guild_id']),
                                    event_name=log_data['event_name'],
                                    action=log_data['action'],
                                    user_name=log_data['user_name'],
                                    user_avatar_url=log_data['user_avatar_url'],
                                    success=log_data['success'],
                                    details=log_data.get('details', ''),
                                    error_reason=log_data.get('error_reason', ''),
                                    additional_data=log_data.get('additional_data', {})
                                )
                                
                                # Mark as processed
                                log_doc.reference.update({'processed': True})
                                
                            except Exception as e:
                                logger.error(f"Error processing log entry: {e}")
                                # Mark as processed to avoid infinite retries
                                log_doc.reference.update({'processed': True})
                
                # Wait before next check
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in process_log_entries: {e}")
                await asyncio.sleep(10)  # Wait longer on error
    
    async def on_command_error(self, context: commands.Context, exception: Exception) -> None:
        """Handle command errors."""
        if isinstance(exception, commands.CommandNotFound):
            return
        
        logger.error(f"Error in command {context.command}: {exception}", exc_info=True)
        
        # Check if this is a hybrid command (slash command)
        if hasattr(context, 'interaction') and context.interaction:
            # For hybrid commands, use followup if deferred, otherwise response
            try:
                if context.interaction.response.is_done():
                    await context.followup.send(f"An error occurred: {exception}", ephemeral=True)
                else:
                    await context.interaction.response.send_message(f"An error occurred: {exception}", ephemeral=True)
            except:
                # Fallback to regular send
                await context.send(f"An error occurred: {exception}")
        else:
            # For regular commands
            if isinstance(exception, commands.MissingPermissions):
                await context.send("You don't have permission to use this command.")
            elif isinstance(exception, commands.MissingRequiredArgument):
                await context.send(f"Missing required argument: {exception.param.name}")
            else:
                await context.send(f"An error occurred: {exception}")

async def main():
    """Run the bot."""
    intents = discord.Intents.default()
    intents.message_content = True
    bot = SignupBot(command_prefix="!", intents=intents)
    bot.run(Config.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
