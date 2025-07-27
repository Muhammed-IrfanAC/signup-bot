# Tests for the admin cog.
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import discord
from discord.ext import commands

from signup_bot.cogs.admin import Admin

@pytest.mark.asyncio
async def test_add_leader_role(bot, mock_interaction):
    """Test adding a leader role."""
    # Setup test data
    test_role = MagicMock()
    test_role.id = 54321
    test_role.name = "Test Role"
    test_role.mention = "@TestRole"
    
    mock_interaction.guild.roles = [test_role]
    
    # Create the cog and add it to the bot
    admin_cog = Admin(bot)
    
    # Mock the API response
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"message": "Leader role added successfully"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Call the command
        await admin_cog.add_leader_role(mock_interaction, role=test_role)
        
        # Verify the response
        mock_interaction.response.send_message.assert_awaited_once_with(
            f"Added {test_role.mention} as a leader role.", 
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_remove_leader_role(bot, mock_interaction):
    """Test removing a leader role."""
    # Setup test data
    test_role = MagicMock()
    test_role.id = 54321
    test_role.name = "Test Role"
    test_role.mention = "@TestRole"
    
    mock_interaction.guild.roles = [test_role]
    
    # Create the cog and add it to the bot
    admin_cog = Admin(bot)
    
    # Mock the API response
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"message": "Leader role removed successfully"}
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Call the command
        await admin_cog.remove_leader_role(mock_interaction, role=test_role)
        
        # Verify the response
        mock_interaction.response.send_message.assert_awaited_once_with(
            f"Removed {test_role.mention} from leader roles.", 
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_list_leader_roles(bot, mock_interaction):
    """Test listing leader roles."""
    # Setup test data
    test_roles = [
        {"id": "12345", "name": "Admin"},
        {"id": "67890", "name": "Moderator"}
    ]
    
    # Create the cog and add it to the bot
    admin_cog = Admin(bot)
    
    # Mock the API response
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"leader_role_ids": ["12345", "67890"]}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Call the command
        await admin_cog.list_leader_roles(mock_interaction)
        
        # Verify the response
        mock_interaction.response.send_message.assert_awaited_once()
        
        # Get the embed from the call
        embed = mock_interaction.response.send_message.call_args[1]['embed']
        assert embed.title == "Leader Roles"
        assert "• <@&12345> (Admin)\n• <@&67890> (Moderator)" in embed.description

@pytest.mark.asyncio
async def test_list_leader_roles_empty(bot, mock_interaction):
    """Test listing leader roles when there are none."""
    # Create the cog and add it to the bot
    admin_cog = Admin(bot)
    
    # Mock the API response
    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"leader_role_ids": []}
        mock_get.return_value.__aenter__.return_value = mock_response
        
        # Call the command
        await admin_cog.list_leader_roles(mock_interaction)
        
        # Verify the response
        mock_interaction.response.send_message.assert_awaited_once_with(
            "No leader roles have been set up yet.", 
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_api_error_handling(bot, mock_interaction):
    """Test error handling when the API returns an error."""
    # Setup test data
    test_role = MagicMock()
    test_role.id = 54321
    test_role.name = "Test Role"
    test_role.mention = "@TestRole"
    
    mock_interaction.guild.roles = [test_role]
    
    # Create the cog and add it to the bot
    admin_cog = Admin(bot)
    
    # Mock the API response with an error
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = {"error": "Failed to add leader role"}
        mock_response.status = 500
        mock_post.return_value.__aenter__.return_value = mock_response
        
        # Call the command
        await admin_cog.add_leader_role(mock_interaction, role=test_role)
        
        # Verify the error response
        mock_interaction.followup.send.assert_awaited_once_with(
            "An error occurred while processing your request.", 
            ephemeral=True
        )

@pytest.mark.asyncio
async def test_missing_permissions(bot, mock_interaction):
    """Test that commands check for administrator permissions."""
    # Setup test data
    test_role = MagicMock()
    test_role.id = 54321
    test_role.name = "Test Role"
    test_role.mention = "@TestRole"
    
    mock_interaction.guild.roles = [test_role]
    mock_interaction.user.guild_permissions.administrator = False
    
    # Create the cog and add it to the bot
    admin_cog = Admin(bot)
    
    # Call the command without permissions
    await admin_cog.add_leader_role(mock_interaction, role=test_role)
    
    # Verify the permission error response
    mock_interaction.response.send_message.assert_awaited_once_with(
        "You need administrator permissions to use this command.", 
        ephemeral=True
    )
