import discord
import aiohttp
from datetime import datetime
from typing import Optional, Dict, Any
from .embed_builder import EmbedBuilder

class EventLogger:
    """Utility class for logging event actions to Discord channels."""
    
    @staticmethod
    async def log_action(
        bot,
        guild_id: int,
        event_name: str,
        action: str,
        user_name: str,
        user_avatar_url: str,
        success: bool,
        details: str = "",
        error_reason: str = "",
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """
        Log an event action to the designated log channel.
        
        Args:
            bot: Discord bot instance
            guild_id: ID of the guild
            event_name: Name of the event
            action: Action being performed (create, signup, remove, export, close)
            user_name: Name of the user performing the action
            user_avatar_url: Avatar URL of the user
            success: Whether the action was successful
            details: Additional details about the action
            error_reason: Reason for failure if not successful
            additional_data: Any additional data to include in the embed
        """
        try:
            # Get the log channel ID from the event data
            log_channel_id = await EventLogger._get_log_channel_id(guild_id, event_name)
            if not log_channel_id:
                return  # No log channel configured
            
            # Get the channel
            channel = bot.get_channel(int(log_channel_id))
            if not channel:
                return  # Channel not found
            
            # Create the embed
            embed = EventLogger._create_log_embed(
                event_name, action, user_name, user_avatar_url, 
                success, details, error_reason, additional_data
            )
            
            # Send the embed
            await channel.send(embed=embed)
            
        except Exception as e:
            print(f"Error logging action: {e}")
    
    @staticmethod
    async def _get_log_channel_id(guild_id: int, event_name: str) -> Optional[str]:
        """Get the log channel ID for an event."""
        try:
            import firebase_admin
            from firebase_admin import firestore
            
            db = firestore.client()
            event_ref = db.collection('servers').document(str(guild_id)).collection('events').document(event_name)
            event_doc = event_ref.get()
            
            if event_doc.exists:
                event_data = event_doc.to_dict()
                return event_data.get('log_channel_id')
            
            return None
        except Exception as e:
            print(f"Error getting log channel ID: {e}")
            return None
    
    @staticmethod
    def _create_log_embed(
        event_name: str,
        action: str,
        user_name: str,
        user_avatar_url: str,
        success: bool,
        details: str = "",
        error_reason: str = "",
        additional_data: Optional[Dict[str, Any]] = None
    ) -> discord.Embed:
        """Create a formatted embed for logging."""
        
        # Set color based on success
        color = discord.Color.green() if success else discord.Color.red()
        
        # Set emoji and title based on action
        action_emojis = {
            'create': '📝',
            'signup': '✅',
            'remove': '❌',
            'export': '📊',
            'close': '🔒',
            'check': '🔍'
        }
        
        action_emoji = action_emojis.get(action, '📋')
        status_emoji = "✅" if success else "❌"
        
        # Create embed
        embed = discord.Embed(
            title=f"{action_emoji} {action.title()} Action",
            description=f"**Event:** {event_name}\n**User:** {user_name}\n**Status:** {status_emoji} {'Success' if success else 'Failed'}",
            color=color,
            timestamp=datetime.utcnow()
        )
        
        # Set author with user info
        embed.set_author(
            name=user_name,
            icon_url=user_avatar_url
        )
        
        # Add details if provided
        if details:
            embed.add_field(
                name="Details",
                value=details,
                inline=False
            )
        
        # Add error reason if failed
        if not success and error_reason:
            embed.add_field(
                name="Error Reason",
                value=error_reason,
                inline=False
            )
        
        # Add additional data if provided
        if additional_data:
            for key, value in additional_data.items():
                if value:  # Only add non-empty values
                    embed.add_field(
                        name=key.replace('_', ' ').title(),
                        value=str(value),
                        inline=True
                    )
        
        return embed 