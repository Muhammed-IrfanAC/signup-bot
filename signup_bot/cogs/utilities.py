# Utility commands and functions for the Signup Bot.
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
from datetime import datetime

from .. import Config, __version__

logger = logging.getLogger(__name__)

class Utilities(commands.Cog):
    """Utility commands for the bot."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="ping", description="Check the bot's latency")
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency."""
        latency = round(self.bot.latency * 1000)  # Convert to ms
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")
    
    @commands.hybrid_command(name="uptime", description="Check the bot's uptime")
    async def uptime(self, ctx: commands.Context):
        """Check how long the bot has been running."""
        delta = datetime.utcnow() - self.bot.start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        
        uptime_str = []
        if days:
            uptime_str.append(f"{days} day{'s' if days > 1 else ''}")
        if hours:
            uptime_str.append(f"{hours} hour{'s' if hours > 1 else ''}")
        if minutes:
            uptime_str.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
        if seconds or not uptime_str:  # Always show at least seconds
            uptime_str.append(f"{seconds} second{'s' if seconds != 1 else ''}")
        
        await ctx.send(f"⏱️ Uptime: {', '.join(uptime_str)}")
    
    @commands.hybrid_command(name="version", description="Show bot version")
    async def version(self, ctx: commands.Context):
        """Show the bot's version information."""
        embed = discord.Embed(
            title="Signup Bot",
            description=f"Version: {__version__}\n"
                      f"Discord.py: {discord.__version__}",
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="invite", description="Get an invite link for the bot")
    async def invite(self, ctx: commands.Context):
        """Get an invite link for the bot."""
        perms = discord.Permissions()
        perms.update(
            read_messages=True,
            send_messages=True,
            manage_messages=True,
            embed_links=True,
            read_message_history=True,
            use_external_emojis=True,
            add_reactions=True
        )
        
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=perms,
            scopes=('bot', 'applications.commands')
        )
        
        await ctx.send(
            f"🔗 Invite me to your server: {invite_url}",
            ephemeral=True
        )
    
    @commands.hybrid_command(name="bothelp", description="Show help information")
    async def bothelp(self, ctx: commands.Context):
        """Show help information about the bot's commands."""
        embed = discord.Embed(
            title="Signup Bot Help",
            description="A bot for managing Clash of Clans event signups.",
            color=discord.Color.blue()
        )
        
        # Admin Commands
        admin_commands = [
            ("add_leader_role [role]", "Add a role as a leader role"),
            ("remove_leader_role [role]", "Remove a leader role"),
            ("list_leader_roles", "List all leader roles")
        ]
        
        # Event Commands
        event_commands = [
            ("create_event [name] [role]", "Create a new event (role is optional)"),
            ("list_events", "List all events"),
            ("sign_up [event]", "Sign up for an event"),
            ("check [event]", "Check your signup status"),
            ("remove [event]", "Remove your signup"),
            ("export [event]", "Export event data")
        ]
        
        # Utility Commands
        utility_commands = [
            ("ping", "Check the bot's latency"),
            ("uptime", "Check the bot's uptime"),
            ("version", "Show bot version"),
            ("invite", "Get an invite link"),
            ("bothelp", "Show this help message")
        ]
        
        # Add fields to the embed
        embed.add_field(
            name="🎮 Event Commands",
            value="\n".join(f"`/{cmd[0]}` - {cmd[1]}" for cmd in event_commands),
            inline=False
        )
        
        embed.add_field(
            name="⚙️ Admin Commands",
            value="\n".join(f"`/{cmd[0]}` - {cmd[1]}" for cmd in admin_commands),
            inline=False
        )
        
        embed.add_field(
            name="🔧 Utility Commands",
            value="\n".join(f"`/{cmd[0]}` - {cmd[1]}" for cmd in utility_commands),
            inline=False
        )
        
        embed.set_footer(text="Use /help [command] for more info on a command.")
        
        await ctx.send(embed=embed)

async def setup(bot):
    """Set up the utilities cog."""
    await bot.add_cog(Utilities(bot))
