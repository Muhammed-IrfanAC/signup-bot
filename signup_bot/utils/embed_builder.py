import discord
from .emoji_config import get_success_emoji, get_error_emoji

class EmbedBuilder:
    """Reusable builder for standardized success and error embeds."""
    SUCCESS_COLOR = discord.Color.green()
    ERROR_COLOR = discord.Color.red()
    INFO_COLOR = discord.Color.blue()
    
    # Get custom emojis
    SUCCESS_EMOJI = get_success_emoji()
    ERROR_EMOJI = get_error_emoji()

    @staticmethod
    def success(title: str = "Success", description: str = "", **kwargs) -> discord.Embed:
        # Add success emoji to title if not already present
        if not title.startswith(EmbedBuilder.SUCCESS_EMOJI):
            title = f"{EmbedBuilder.SUCCESS_EMOJI} {title}"
        return discord.Embed(title=title, description=description, color=EmbedBuilder.SUCCESS_COLOR, **kwargs)

    @staticmethod
    def error(title: str = "Error", description: str = "", **kwargs) -> discord.Embed:
        # Add error emoji to title if not already present
        if not title.startswith(EmbedBuilder.ERROR_EMOJI):
            title = f"{EmbedBuilder.ERROR_EMOJI} {title}"
        return discord.Embed(title=title, description=description, color=EmbedBuilder.ERROR_COLOR, **kwargs)

    @staticmethod
    def info(title: str = "Info", description: str = "", **kwargs) -> discord.Embed:
        return discord.Embed(title=title, description=description, color=EmbedBuilder.INFO_COLOR, **kwargs) 