# Tests for the Signup Bot.
import pytest
from unittest.mock import patch, MagicMock
import discord
from discord.ext import commands

from signup_bot.bot import SignupBot

@pytest.mark.asyncio
async def test_bot_initialization():
    """Test that the bot initializes correctly."""
    # Patch the setup_hook to avoid loading cogs
    with patch('discord.ext.commands.Bot.setup_hook'):
        intents = discord.Intents.default()
        intents.message_content = True
        bot = SignupBot(intents=intents)
        
        assert bot is not None
        assert isinstance(bot, commands.Bot)
        
        # Verify the bot has the expected attributes
        assert hasattr(bot, 'start_time')
        assert hasattr(bot, 'config')
        
        await bot.close()

@pytest.mark.asyncio
async def test_bot_setup(bot):
    """Test the bot's setup method."""
    # Mock the load_extension method
    with patch.object(bot, 'load_extension') as mock_load_ext:
        await bot.setup_hook()
        
        # Verify that cogs are loaded
        assert mock_load_ext.call_count >= 3  # admin, events, utilities

@pytest.mark.asyncio
async def test_bot_on_ready(bot):
    """Test the on_ready event handler."""
    # Mock the setup_hook to avoid loading cogs
    with patch.object(bot, 'setup_hook'):
        # Call the on_ready event handler directly
        await bot.on_ready()
        
        # Verify that the bot's presence was updated
        assert bot.user is not None
        assert hasattr(bot, 'start_time')

@pytest.mark.asyncio
async def test_bot_close(bot):
    """Test the close method."""
    # Mock the parent class's close method
    with patch('discord.ext.commands.Bot.close') as mock_super_close:
        mock_super_close.return_value = None
        
        # Call the close method
        await bot.close()
        
        # Verify that the parent's close method was called
        mock_super_close.assert_called_once()

@pytest.mark.asyncio
async def test_bot_run(bot):
    """Test the run method."""
    # Mock the parent class's run method
    with patch('discord.ext.commands.Bot.run') as mock_super_run, \
         patch('signup_bot.bot.SignupBot.setup_hook'):
        # Call the run method with a test token
        bot.run('test.token.123')
        
        # Verify that the parent's run method was called with the token
        mock_super_run.assert_called_once_with('test.token.123')
