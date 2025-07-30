# Admin commands for the Signup Bot.
import discord
from discord import app_commands
from discord.ext import commands
import aiohttp
import logging
from typing import Optional

from .. import Config

logger = logging.getLogger(__name__)

class Admin(commands.Cog):
    """Admin commands for managing the bot and server settings."""
    
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="add_leader_role", description="Add a role as a leader role")
    @app_commands.describe(role="The role to add as a leader")
    @commands.has_permissions(administrator=True)
    async def add_leader_role(self, ctx: commands.Context, role: discord.Role):
        """Add a role as a leader role that can manage events."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{Config.API_BASE_URL}/api/servers/{ctx.guild.id}/add_leader_role",
                json={'role_id': str(role.id)}
            ) as response:
                if response.status == 200:
                    await ctx.send(f"✅ Added {role.mention} as a leader role.", ephemeral=True)
                else:
                    await ctx.send("❌ Failed to add leader role.", ephemeral=True)

    @commands.hybrid_command(name="remove_leader_role", description="Remove a leader role")
    @app_commands.describe(role="The role to remove from leaders")
    @commands.has_permissions(administrator=True)
    async def remove_leader_role(self, ctx: commands.Context, role: discord.Role):
        """Remove a role from the leader roles."""
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{Config.API_BASE_URL}/api/servers/{ctx.guild.id}/remove_leader_role",
                json={'role_id': str(role.id)}
            ) as response:
                if response.status == 200:
                    await ctx.send(f"✅ Removed {role.mention} from leader roles.", ephemeral=True)
                else:
                    await ctx.send("❌ Failed to remove leader role.", ephemeral=True)

    @commands.hybrid_command(name="list_leader_roles", description="List all leader roles")
    async def list_leader_roles(self, ctx: commands.Context):
        """List all roles that have leader permissions."""
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{Config.API_BASE_URL}/api/servers/{ctx.guild.id}/leader_roles"
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    role_ids = data.get('leader_role_ids', [])
                    
                    if not role_ids:
                        await ctx.send("No leader roles set up yet.")
                        return
                    
                    roles = [f"<@&{role_id}>" for role_id in role_ids]
                    embed = discord.Embed(
                        title="Leader Roles",
                        description="\n".join(roles) or "No leader roles set up yet.",
                        color=discord.Color.blue()
                    )
                    await ctx.send(embed=embed, ephemeral=True)
                else:
                    await ctx.send("❌ Failed to fetch leader roles.", ephemeral=True)

async def setup(bot):
    """Set up the admin cog."""
    await bot.add_cog(Admin(bot))
