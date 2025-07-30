# Main Discord bot module for the Signup Bot.
import logging
import discord
from discord.ext import commands
from discord import app_commands
import asyncio
from typing import List
import os
from datetime import datetime

from . import __version__, Config
from .api import Config as APIConfig
import aiohttp
from .cogs.events import EventView

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
            activity=discord.Game(name=f"Signup Bot v{__version__}"),
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
