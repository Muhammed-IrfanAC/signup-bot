# Pytest configuration and fixtures for testing the Signup Bot.
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
import discord.ext.test as dpytest
from signup_bot.bot import SignupBot

# Configure logging
import logging
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
event_loop():
    """Create an instance of the default event loop for each test case."""
    import asyncio
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def bot():
    """Create a bot instance for testing."""
    # Patch the bot's setup method to avoid loading cogs during tests
    with patch('discord.ext.commands.Bot.setup_hook'):
        intents = discord.Intents.default()
        intents.message_content = True
        bot = SignupBot(intents=intents)
        
        # Mock the login method to avoid actual login
        bot.login = AsyncMock()
        bot.connect = AsyncMock()
        
        # Mock the bot's user
        bot.user = MagicMock()
        bot.user.id = 1234567890
        bot.user.display_name = "TestBot"
        
        yield bot
        
        # Cleanup
        await bot.close()

@pytest.fixture
def mock_guild():
    """Create a mock guild for testing."""
    guild = MagicMock()
    guild.id = 12345
    guild.name = "Test Guild"
    guild.roles = []
    guild.members = []
    guild.emojis = []
    guild.icon = None
    return guild

@pytest.fixture
def mock_channel():
    """Create a mock text channel for testing."""
    channel = MagicMock()
    channel.id = 67890
    channel.name = "test-channel"
    channel.guild = MagicMock()
    channel.guild.id = 12345
    channel.guild.name = "Test Guild"
    channel.send = AsyncMock()
    return channel

@pytest.fixture
def mock_message(mock_channel):
    """Create a mock message for testing."""
    message = MagicMock()
    message.id = 54321
    message.channel = mock_channel
    message.author = MagicMock()
    message.author.id = 98765
    message.author.name = "TestUser"
    message.author.mention = "@TestUser"
    message.author.bot = False
    message.guild = mock_channel.guild
    return message

@pytest.fixture
def mock_context(bot, mock_message):
    """Create a mock context for testing commands."""
    context = MagicMock()
    context.bot = bot
    context.message = mock_message
    context.author = mock_message.author
    context.guild = mock_message.guild
    context.channel = mock_message.channel
    context.send = AsyncMock()
    context.reply = AsyncMock()
    return context

@pytest.fixture
def mock_interaction(bot, mock_guild):
    """Create a mock interaction for testing application commands."""
    interaction = AsyncMock()
    interaction.client = bot
    interaction.guild = mock_guild
    interaction.user = MagicMock()
    interaction.user.id = 98765
    interaction.user.name = "TestUser"
    interaction.user.mention = "@TestUser"
    interaction.user.bot = False
    interaction.response = AsyncMock()
    interaction.followup = AsyncMock()
    return interaction

@pytest.fixture(autouse=True)
def mock_firebase():
    """Mock Firebase Admin SDK for all tests."""
    with patch('firebase_admin.initialize_app'), \
         patch('firebase_admin.firestore.client'):
        yield

@pytest.fixture(autouse=True)
def mock_http_requests():
    """Mock HTTP requests for all tests."""
    with patch('aiohttp.ClientSession.get') as mock_get, \
         patch('aiohttp.ClientSession.post') as mock_post:
        mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value={})
        mock_post.return_value.__aenter__.return_value.json = AsyncMock(return_value={})
        yield mock_get, mock_post
