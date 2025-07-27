# Event management commands for the Signup Bot.
import io
import logging
from socket import timeout
from typing import List

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, Modal, TextInput, View

from .. import Config
from ..utils.embed_builder import EmbedBuilder
from ..utils.emoji_config import get_loading_emoji, get_success_emoji, get_error_emoji

# Centralized emoji configuration
LOADING_EMOJI = get_loading_emoji()
SUCCESS_EMOJI = get_success_emoji()
ERROR_EMOJI = get_error_emoji()

logger = logging.getLogger(__name__)

class EventView(View):
    """View containing event management buttons."""
    
    def __init__(self, event_name: str, closed: bool = False):
        super().__init__(timeout=None)
        self.event_name = event_name
        self.closed = closed
        # Add buttons, disabling all except Export if closed
        self.add_item(SignupButton(event_name, disabled=closed))
        self.add_item(RemoveButton(event_name, disabled=closed))
        self.add_item(CheckButton(event_name, disabled=False))
        self.add_item(CloseButton(event_name, disabled=closed))
        self.add_item(ExportButton(event_name, disabled=False))

class SignupButton(Button):
    """Button for signing up to an event."""
    
    def __init__(self, event_name: str, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.green, label="Sign Up", custom_id=f"signup_{event_name}", disabled=disabled)
        self.event_name = event_name
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click."""
        modal = SignupModal(self.event_name)
        await interaction.response.send_modal(modal)

class RemoveButton(Button):
    """Button for removing a signup."""
    
    def __init__(self, event_name: str, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.red, label="Remove", custom_id=f"remove_{event_name}", disabled=disabled)
        self.event_name = event_name
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click."""
        modal = RemoveModal(self.event_name)
        await interaction.response.send_modal(modal)

class CheckButton(Button):
    """Button for checking signup status."""
    
    def __init__(self, event_name: str, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.blurple, label="Check", custom_id=f"check_{event_name}", disabled=disabled)
        self.event_name = event_name
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click."""
        modal = CheckModal(self.event_name)
        await interaction.response.send_modal(modal)

class CloseButton(Button):
    """Button for closing event registration."""
    
    def __init__(self, event_name: str, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.danger, label="Close", custom_id=f"close_{event_name}", disabled=disabled)
        self.event_name = event_name
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click."""
        modal = CloseModal(self.event_name)
        await interaction.response.send_modal(modal)

class ExportButton(Button):
    """Button for exporting event data."""
    
    def __init__(self, event_name: str, disabled: bool = False):
        super().__init__(style=discord.ButtonStyle.grey, label="Export", custom_id=f"export_{event_name}", disabled=disabled)
        self.event_name = event_name
    
    async def callback(self, interaction: discord.Interaction):
        """Handle button click."""
        await interaction.response.send_message(f"{LOADING_EMOJI} Preparing export...", ephemeral=True)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{Config.API_BASE_URL}/api/events/{self.event_name}/export",
                params={"guild_id": interaction.guild_id}
            ) as response:
                if response.status == 200:
                    data = await response.read()
                    file = discord.File(io.BytesIO(data), filename=f"{self.event_name}_export.xlsx")
                    # For files, we need to use followup.send since edit_original_response doesn't support files
                    await interaction.followup.send("Here's the export:", file=file, ephemeral=True)
                else:
                    await interaction.edit_original_response(
                        content="",
                        embed=EmbedBuilder.error(
                            description=f"{ERROR_EMOJI} Failed to export event data."
                        )
                    )

class SignupModal(Modal):
    """Modal for signing up to an event."""
    
    def __init__(self, event_name: str):
        super().__init__(title=f"Sign Up for {event_name}")
        self.event_name = event_name
        
        self.player_tag = TextInput(
            label="Player Tag",
            placeholder="#ABCD1234",
            required=True
        )
        
        self.add_item(self.player_tag)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        await interaction.response.send_message(f"{LOADING_EMOJI} Processing your signup...", ephemeral=True)

        # Normalize the player tag - add # if not present
        player_tag = self.player_tag.value.strip()
        if not player_tag.startswith('#'):
            player_tag = f"#{player_tag}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{Config.API_BASE_URL}/api/events/{self.event_name}/signup",
                json={
                    "player_tag": self.player_tag.value,
                    "discord_name": str(interaction.user),
                    "discord_user_id": str(interaction.user.id),
                    "guild_id": interaction.guild_id
                }
            ) as response:
                if response.status == 201:
                    data = await response.json()
                    
                    # Handle role assignment if the event has a role
                    role_id = data.get('role_id')
                    if role_id:
                        try:
                            # Get the role
                            role = interaction.guild.get_role(int(role_id))
                            if role:
                                # Add the role to the user
                                await interaction.user.add_roles(role, reason=f"Signed up for event: {self.event_name}")
                        except Exception as e:
                            # Log the error but don't fail the signup
                            logger.error(f"Failed to add role {role_id} to user {interaction.user.id}: {e}")
                    
                    # Update the embed
                    await update_event_embed(interaction.guild.id, self.event_name, interaction.client)

                    embed = EmbedBuilder.success(
                        title="Signup Successful!",
                        description=f"You have been signed up for **{self.event_name}**."
                    )
                    embed.add_field(name="Player Name", value=data.get("player_name", "Unknown"), inline=True)
                    embed.add_field(name="Player Tag", value=data.get("player_tag", player_tag), inline=True)
                    embed.add_field(name="Town Hall", value=str(data.get("player_th", "Unknown")), inline=True)
                    
                    # Add role information if a role was assigned
                    if role_id:
                        role = interaction.guild.get_role(int(role_id))
                        if role:
                            embed.add_field(name="Event Role", value=f"You have been assigned: {role.mention}", inline=True)

                    # Edit the original message with the result
                    await interaction.edit_original_response(
                        content="",
                        embed=embed
                    )
                else:
                    error = await response.json()
                    await interaction.edit_original_response(
                        content="",
                        embed=EmbedBuilder.error(
                            description=f"{ERROR_EMOJI} Error: {error.get('error', 'Unknown error')}"
                        )
                    )

# Similar modal classes for RemoveModal, CheckModal, CloseModal would be defined here
class RemoveModal(Modal):
    """Modal for removing a signup from an event."""
    
    def __init__(self, event_name: str):
        super().__init__(title=f"Remove from {event_name}")
        self.event_name = event_name
        
        self.player_tag = TextInput(
            label="Player Tag",
            placeholder="#ABCD1234 or ABCD1234",
            required=True
        )
        
        self.add_item(self.player_tag)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        await interaction.response.send_message(f"{LOADING_EMOJI} Processing your removal...", ephemeral=True)
        
        # Normalize the player tag - add # if not present
        player_tag = self.player_tag.value.strip()
        if not player_tag.startswith('#'):
            player_tag = f"#{player_tag}"
        
        async with aiohttp.ClientSession() as session:
            # Get the member object to access their roles
            member = interaction.guild.get_member(interaction.user.id)
            if not member:
                try:
                    member = await interaction.guild.fetch_member(interaction.user.id)
                except:
                    await interaction.edit_original_response(content=f"{ERROR_EMOJI} Could not fetch your member information")
                    return
            
            # Extract role IDs
            user_roles = [str(role.id) for role in member.roles if role.id != interaction.guild.id]
            
            async with session.post(
                f"{Config.API_BASE_URL}/api/events/{self.event_name}/remove",
                json={
                    "player_tag": player_tag,
                    "discord_name": str(interaction.user),
                    "guild_id": interaction.guild_id,
                    "user_roles": user_roles
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Handle role removal if it's a self-removal and the event has a role
                    role_id = data.get('role_id')
                    is_self_removal = data.get('is_self_removal', False)
                    
                    if role_id and is_self_removal:
                        try:
                            # Get the role
                            role = interaction.guild.get_role(int(role_id))
                            if role:
                                # Remove the role from the user
                                await interaction.user.remove_roles(role, reason=f"Removed from event: {self.event_name}")
                        except Exception as e:
                            # Log the error but don't fail the removal
                            logger.error(f"Failed to remove role {role_id} from user {interaction.user.id}: {e}")
                    
                    # Update the embed
                    await update_event_embed(interaction.guild.id, self.event_name, interaction.client)

                    embed = EmbedBuilder.success(
                        title="Removed from Event",
                        description=f"You have been removed from **{self.event_name}**."
                    )
                    embed.add_field(name="Player Name", value=data.get("player_data", {}).get("name", "Unknown"), inline=True)
                    embed.add_field(name="Player Tag", value=data.get("player_data", {}).get("player_tag", player_tag), inline=True)
                    embed.add_field(name="Town Hall", value=str(data.get("player_data", {}).get("th_level", "Unknown")), inline=True)
                    
                    # Add role information if a role was removed
                    if role_id and is_self_removal:
                        role = interaction.guild.get_role(int(role_id))
                        if role:
                            embed.add_field(name="Event Role", value=f"Your role has been removed: {role.mention}", inline=True)

                    # Edit the original message with the result
                    await interaction.edit_original_response(content="", embed=embed)
                elif response.status == 404:
                    await interaction.edit_original_response(
                        content="",
                        embed=EmbedBuilder.error(
                            description=f"{ERROR_EMOJI} Event not found or player {player_tag} does not exist"
                        )
                    )
                else:
                    try:
                        error = await response.json()
                        await interaction.edit_original_response(
                            content="",
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Error: {error.get('error', 'Unknown error')}"
                            )
                        )
                    except:
                        await interaction.edit_original_response(
                            content="",
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Failed to remove signup (Status: {response.status})"
                            )
                        )


class CheckModal(Modal):
    """Modal for checking signup status in an event."""
    
    def __init__(self, event_name: str):
        super().__init__(title=f"Check Status in {event_name}")
        self.event_name = event_name
        
        self.player_tag = TextInput(
            label="Player Tag",
            placeholder="#ABCD1234 or ABCD1234",
            required=True
        )
        
        self.add_item(self.player_tag)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        await interaction.response.send_message(f"{LOADING_EMOJI} Checking signup status...", ephemeral=True)
        
        # Normalize the player tag - add # if not present
        player_tag = self.player_tag.value.strip()
        if not player_tag.startswith('#'):
            player_tag = f"#{player_tag}"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{Config.API_BASE_URL}/api/events/{self.event_name}/check",
                json={
                    "player_tag": player_tag,
                    "guild_id": interaction.guild_id
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data.get('is_signed_up', False):
                        signup_info = data.get('player_data', {})
                        embed = EmbedBuilder.success(
                            title="Signup Status",
                            description=f"**{signup_info.get('name', player_tag)}** is signed up for **{self.event_name}**!"
                        )
                        embed.add_field(name="Player Name", value=signup_info.get('name', player_tag), inline=True)
                        embed.add_field(name="Player Tag", value=signup_info.get('tag', player_tag), inline=True)
                        embed.add_field(name="Town Hall", value=str(signup_info.get('th_level', 'Unknown')), inline=True)
                        embed.add_field(name="Signed Up By", value=signup_info.get('discord_name', 'Unknown'), inline=True)
                        await interaction.edit_original_response(content="", embed=embed)
                    else:
                        await interaction.edit_original_response(
                            content="",
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} {player_tag} is not signed up for this event"
                            )
                        )
                elif response.status == 404:
                    await interaction.edit_original_response(
                        content="",
                        embed=EmbedBuilder.error(
                            description=f"{ERROR_EMOJI} Event not found or player {player_tag} does not exist"
                        )
                    )
                else:
                    try:
                        error = await response.json()
                        await interaction.edit_original_response(
                            content="",
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Error: {error.get('error', 'Unknown error')}"
                            )
                        )
                    except:
                        await interaction.edit_original_response(
                            content="",
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Failed to check signup status (Status: {response.status})"
                            )
                        )


class CloseModal(Modal):
    """Modal for closing event registration."""
    
    def __init__(self, event_name: str):
        super().__init__(title=f"Close {event_name}")
        self.event_name = event_name
        
        self.confirmation = TextInput(
            label="Confirm closing (type 'yes' or 'no')",
            placeholder="yes or no",
            required=True,
            max_length=3
        )
        
        self.add_item(self.confirmation)
    
    async def on_submit(self, interaction: discord.Interaction):
        """Handle form submission."""
        await interaction.response.send_message(f"{LOADING_EMOJI} Processing event closure...", ephemeral=True)
        
        # Check confirmation
        confirmation = self.confirmation.value.strip().lower()
        
        if confirmation not in ['yes', 'no']:
            await interaction.edit_original_response(
                content="",
                embed=EmbedBuilder.error(
                    description=f"{ERROR_EMOJI} Please enter either 'yes' or 'no'"
                )
            )
            return
        
        if confirmation == 'no':
            await interaction.edit_original_response(
                content="",
                embed=EmbedBuilder.error(
                    description=f"{ERROR_EMOJI} Event closing cancelled"
                )
            )
            return
        
        # Get the member object to access their roles
        member = interaction.guild.get_member(interaction.user.id)
        if not member:
            try:
                member = await interaction.guild.fetch_member(interaction.user.id)
            except:
                await interaction.edit_original_response(content=f"{ERROR_EMOJI} Could not fetch your member information")
                return
        
        # Extract role IDs
        user_roles = [str(role.id) for role in member.roles if role.id != interaction.guild.id]
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{Config.API_BASE_URL}/api/events/{self.event_name}/close",
                json={
                    "guild_id": interaction.guild_id,
                    "user_roles": user_roles
                }
            ) as response:
                if response.status == 200:
                    # Update the embed
                    await update_event_embed(interaction.guild.id, self.event_name, interaction.client)
                    
                    await interaction.edit_original_response(
                        content="",
                        embed=EmbedBuilder.success(
                            description=f"✅ Event **{self.event_name}** has been closed for registration."
                        )
                    )
                elif response.status == 403:
                    error = await response.json()
                    await interaction.edit_original_response(
                        content="",
                        embed=EmbedBuilder.error(
                            description=f"{ERROR_EMOJI} {error.get('error', 'You do not have permission to close this event')}"
                        )
                    )
                elif response.status == 409:
                    await interaction.edit_original_response(
                        content="",
                        embed=EmbedBuilder.error(
                            description=f"{ERROR_EMOJI} Event '{self.event_name}' is already closed"
                        )
                    )
                else:
                    try:
                        error = await response.json()
                        await interaction.edit_original_response(
                            content="",
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Error: {error.get('error', 'Unknown error')}"
                            )
                        )
                    except:
                        await interaction.edit_original_response(
                            content="",
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Failed to close event (Status: {response.status})"
                            )
                        )

async def update_event_embed(guild_id: int, event_name: str, bot):
    """Update the event embed with current signups and correct view."""
    import logging
    logger = logging.getLogger(__name__)
    async with aiohttp.ClientSession() as session:
        # Get event details with signups
        async with session.get(
            f"{Config.API_BASE_URL}/api/events/{event_name}",
            params={"guild_id": guild_id}
        ) as response:
            if response.status != 200:
                logger.error(f"Failed to fetch event data for {event_name} (guild {guild_id}): status {response.status}")
                return False
            event_data = await response.json()

    signups = event_data.get('signups', [])
    th_composition = event_data.get('th_composition', {})
    is_closed = not event_data.get('is_open', True)
    message_id = event_data.get('message_id')
    role_id = event_data.get('role_id')  # Get role_id from event data
    
    if not message_id:
        logger.error(f"No message_id found for event {event_name} (guild {guild_id})")
        return False

    guild = bot.get_guild(guild_id)
    if not guild:
        logger.error(f"Bot could not find guild {guild_id}")
        return False

    # Search all channels for the message
    message_found = False
    for channel in guild.text_channels:
        try:
            message = await channel.fetch_message(int(message_id))
            message_found = True
            break
        except (discord.NotFound, discord.Forbidden, discord.HTTPException) as e:
            continue
        except Exception as e:
            logger.error(f"Error fetching message {message_id} in channel {channel.id}: {e}")
    if not message_found:
        logger.error(f"Could not find message {message_id} for event {event_name} in any text channel of guild {guild_id}")
        return False

    # Build embed
    embed_color = discord.Color.red() if is_closed else discord.Color.green()
    embed_title = f'🔒 {event_name}' if is_closed else event_name
    embed = message.embeds[0] if message.embeds else discord.Embed(title=embed_title, color=embed_color)
    embed.title = embed_title
    embed.color = embed_color

    # Format TH composition
    th_text = "\n".join([f"TH{th}: {count}" for th, count in sorted(th_composition.items(), reverse=True)]) or "No signups yet"

    # Update or add fields
    if embed.fields:
        for i, field in enumerate(embed.fields):
            if field.name == "Total Signups":
                embed.set_field_at(i, name="Total Signups", value=str(len(signups)), inline=False)
            elif field.name == "TH Composition":
                embed.set_field_at(i, name="TH Composition", value=th_text, inline=False)
            elif field.name == "Event Role":
                # Update role field if it exists
                if role_id:
                    role = guild.get_role(int(role_id))
                    if role:
                        embed.set_field_at(i, name="Event Role", value=f"Participants receive: {role.mention}", inline=False)
                else:
                    # Remove role field if no role
                    embed.remove_field(i)
    else:
        embed.add_field(name="Total Signups", value=str(len(signups)), inline=False)
        embed.add_field(name="TH Composition", value=th_text, inline=False)
        
        # Add role field if event has a role
        if role_id:
            role = guild.get_role(int(role_id))
            if role:
                embed.add_field(name="Event Role", value=f"Participants receive: {role.mention}", inline=False)

    # Always update the view as well
    view = EventView(event_name, closed=is_closed)
    try:
        await message.edit(embed=embed, view=view)
    except Exception as e:
        logger.error(f"Failed to edit message {message_id} for event {event_name}: {e}")
        return False
    return True

class Events(commands.Cog):
    """Event management commands."""
    
    def __init__(self, bot):
        self.bot = bot
    
    @commands.hybrid_command(name="create_event", description="Create a new event")
    @app_commands.describe(
        name="Name of the event",
        role="Optional role to assign to event participants (leave empty for no role)"
    )
    async def create_event(self, ctx: commands.Context, name: str, role: discord.Role = None):
        """Create a new event."""
        await ctx.defer()
        
        # Prepare the request data
        request_data = {
            "event_name": name,
            "guild_id": ctx.guild.id,
            "channel_id": ctx.channel.id
        }
        
        # Add role_id if a role was provided
        if role:
            request_data["role_id"] = str(role.id)
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{Config.API_BASE_URL}/api/events",
                json=request_data
            ) as response:
                if response.status == 201:
                    # Create and send the event embed
                    embed = discord.Embed(
                        title=name,
                        description="Event roster and signups",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Total Signups", value="0", inline=False)
                    embed.add_field(name="TH Composition", value="No signups yet", inline=False)
                    
                    # Add role information if a role was set
                    if role:
                        embed.add_field(name="Event Role", value=f"Participants will receive: {role.mention}", inline=False)
                    
                    # Send the message with buttons
                    view = EventView(name)
                    
                    # Use followup if available (slash commands), otherwise use send
                    if hasattr(ctx, 'followup'):
                        message = await ctx.followup.send(embed=embed, view=view)
                    else:
                        message = await ctx.send(embed=embed, view=view)
                    
                    # Store the message ID and channel ID
                    async with session.post(
                        f"{Config.API_BASE_URL}/api/events/{name}/update_message_id",
                        json={
                            "guild_id": ctx.guild.id,
                            "message_id": str(message.id),
                            "channel_id": ctx.channel.id
                        }
                    ):
                        pass  # We don't need to handle the response
                    
                    await update_event_embed(ctx.guild.id, name, self.bot)
                    
                    # Create success message
                    success_msg = f"✅ Created event: {name}"
                    if role:
                        success_msg += f"\n📋 Event role: {role.mention}"
                    
                    # Use followup if available (slash commands), otherwise use send
                    if hasattr(ctx, 'followup'):
                        await ctx.followup.send(
                            embed=EmbedBuilder.success(
                                description=success_msg
                            ),
                            ephemeral=True
                        )
                    else:
                        await ctx.send(
                            embed=EmbedBuilder.success(
                                description=success_msg
                            ),
                            ephemeral=True
                        )
                else:
                    error = await response.json()
                    # Use followup if available (slash commands), otherwise use send
                    if hasattr(ctx, 'followup'):
                        await ctx.followup.send(
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Error: {error.get('error', 'Unknown error')}"
                            ),
                            ephemeral=True
                        )
                    else:
                        await ctx.send(
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Error: {error.get('error', 'Unknown error')}"
                            )
                        )

    @commands.hybrid_command(name="list_events", description="List all events")
    async def list_events(self, ctx: commands.Context):
        """List all events in the server."""
        await ctx.defer()
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{Config.API_BASE_URL}/api/events",
                params={"guild_id": ctx.guild.id}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get('events', [])
                    
                    if not events:
                        # Use followup if available (slash commands), otherwise use send
                        if hasattr(ctx, 'followup'):
                            await ctx.followup.send("No events found.", ephemeral=True)
                        else:
                            await ctx.send("No events found.")
                        return
                    
                    # Discord embeds have a limit of 25 fields
                    # We'll show up to 20 events per embed to be safe
                    MAX_EVENTS_PER_EMBED = 20
                    
                    if len(events) <= MAX_EVENTS_PER_EMBED:
                        # Single embed for all events
                        embed = discord.Embed(
                            title="Events",
                            description=f"List of all events ({len(events)} total)",
                            color=discord.Color.blue()
                        )
                        
                        for event in events:
                            event_name = event.get('event_name', 'Unknown')
                            signup_count = event.get('signup_count', 0)
                            is_open = event.get('is_open', True)
                            role_id = event.get('role_id')
                            
                            # Build event description
                            status = "🟢 Open" if is_open else "🔴 Closed"
                            event_desc = f"Signups: {signup_count} | Status: {status}"
                            
                            # Add role information if available
                            if role_id:
                                role = ctx.guild.get_role(int(role_id))
                                if role:
                                    event_desc += f" | Role: {role.mention}"
                            
                            embed.add_field(
                                name=event_name,
                                value=event_desc,
                                inline=False
                            )
                        
                        # Use followup if available (slash commands), otherwise use send
                        if hasattr(ctx, 'followup'):
                            await ctx.followup.send(embed=embed, ephemeral=True)
                        else:
                            await ctx.send(embed=embed)
                    else:
                        # Multiple embeds for many events
                        total_events = len(events)
                        num_embeds = (total_events + MAX_EVENTS_PER_EMBED - 1) // MAX_EVENTS_PER_EMBED
                        
                        for i in range(num_embeds):
                            start_idx = i * MAX_EVENTS_PER_EMBED
                            end_idx = min(start_idx + MAX_EVENTS_PER_EMBED, total_events)
                            current_events = events[start_idx:end_idx]
                            
                            embed = discord.Embed(
                                title=f"Events (Page {i + 1}/{num_embeds})",
                                description=f"Showing events {start_idx + 1}-{end_idx} of {total_events}",
                                color=discord.Color.blue()
                            )
                            
                            for event in current_events:
                                event_name = event.get('event_name', 'Unknown')
                                signup_count = event.get('signup_count', 0)
                                is_open = event.get('is_open', True)
                                role_id = event.get('role_id')
                                
                                # Build event description
                                status = "🟢 Open" if is_open else "🔴 Closed"
                                event_desc = f"Signups: {signup_count} | Status: {status}"
                                
                                # Add role information if available
                                if role_id:
                                    role = ctx.guild.get_role(int(role_id))
                                    if role:
                                        event_desc += f" | Role: {role.mention}"
                                
                                embed.add_field(
                                    name=event_name,
                                    value=event_desc,
                                    inline=False
                                )
                            
                            # Send each embed
                            if hasattr(ctx, 'followup'):
                                await ctx.followup.send(embed=embed, ephemeral=True)
                            else:
                                await ctx.send(embed=embed)
                else:
                    # Use followup if available (slash commands), otherwise use send
                    if hasattr(ctx, 'followup'):
                        await ctx.followup.send(
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Failed to fetch events."
                            ),
                            ephemeral=True
                        )
                    else:
                        await ctx.send(
                            embed=EmbedBuilder.error(
                                description=f"{ERROR_EMOJI} Failed to fetch events."
                            )
                        )

async def setup(bot):
    """Set up the events cog."""
    await bot.add_cog(Events(bot))
