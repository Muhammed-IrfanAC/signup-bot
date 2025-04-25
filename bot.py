import discord
from discord import app_commands
import aiohttp
import os
import io
from dotenv import load_dotenv
from collections import defaultdict
from typing import List
import asyncio

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.environ['DISCORD_TOKEN']
API_BASE_URL = 'http://127.0.0.1:8080'

class ClashClient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.tree = app_commands.CommandTree(self)
        # Store message IDs for each event to update embeds
        self.event_messages = {}
        # Store TH counts for each event
        self.th_counts = defaultdict(lambda: defaultdict(int))

    async def setup_hook(self):
        await self.tree.sync()

client = ClashClient()

@client.event
async def on_ready():
    print(f'Logged in as {client.user}')

    await asyncio.sleep(10)

    # Fetch all guilds the bot is in
    for guild in client.guilds:
        guild_id = guild.id

        # Fetch existing events for the guild from the API
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/api/events?guild_id={guild_id}') as response:
                if response.status == 200:
                    data = await response.json()
                    events = data.get('events', [])

                    # Recreate the embed and register persistent views for each event
                    for event in events:
                        event_name = event.get('event_name')
                        message_id = event.get('message_id')
                        embed_data = event.get('embed', {})
                        if event_name and message_id and embed_data:
                            # Fetch signup data for the event
                            async with session.get(f'{API_BASE_URL}/api/events/{event_name}/signups?guild_id={guild_id}') as signup_response:
                                if signup_response.status == 200:
                                    signup_data = await signup_response.json()
                                    signups = signup_data.get('signups', [])

                                    # Calculate total signups and TH composition
                                    total_signups = len(signups)
                                    th_counts = defaultdict(int)
                                    for signup in signups:
                                        th_level = signup.get('player_th')
                                        if th_level:
                                            th_counts[th_level] += 1

                                    # Create TH composition text
                                    th_comp_text = "\n".join([f"TH {th_level} - {count}" for th_level, count in sorted(th_counts.items())])
                                    if not th_comp_text:
                                        th_comp_text = "No signups yet"

                                    # Recreate the embed
                                    embed = discord.Embed(
                                        title=embed_data.get('title'),
                                        description=embed_data.get('description'),
                                        color=embed_data.get('color', 0x00ff00)  # Default to green
                                    )
                                    embed.add_field(name="Total Signups", value=str(total_signups), inline=False)
                                    embed.add_field(name="TH Composition", value=th_comp_text, inline=False)

                                    # Register the persistent view
                                    view = EventView(event_name)
                                    client.add_view(view)

                                    # Edit the existing message
                                    try:
                                        channel = guild.system_channel  # Or specify a specific channel
                                        if channel:
                                            message = await channel.fetch_message(message_id)
                                            await message.edit(embed=embed, view=view)
                                            print(f"Updated embed for event: {event_name} in guild: {guild_id}")
                                    except discord.NotFound:
                                        print(f"Message {message_id} not found for event: {event_name}")
                                    except Exception as e:
                                        print(f"Error updating embed for event {event_name}: {e}")
                                else:
                                    print(f"Failed to fetch signups for event {event_name}: {signup_response.status}")
                else:
                    print(f"Failed to fetch events for guild {guild_id}: {response.status}")

async def update_embed(interaction: discord.Interaction, event_name: str):
    guild_id = interaction.guild_id

    # Fetch the event data from Firestore
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_BASE_URL}/api/events/{event_name}?guild_id={guild_id}') as response:
            if response.status == 200:
                event_data = await response.json()
                embed_data = event_data.get('embed', {})
                message_id = event_data.get('message_id')

                # Fetch signup data for the event
                async with session.get(f'{API_BASE_URL}/api/events/{event_name}/signups?guild_id={guild_id}') as signup_response:
                    if signup_response.status == 200:
                        signup_data = await signup_response.json()
                        signups = signup_data.get('signups', [])

                        # Calculate total signups and TH composition
                        total_signups = len(signups)
                        th_counts = defaultdict(int)
                        for signup in signups:
                            th_level = signup.get('player_th')
                            if th_level:
                                th_counts[th_level] += 1

                        # Create TH composition text
                        th_comp_text = "\n".join([f"TH {th_level} - {count}" for th_level, count in sorted(th_counts.items())])
                        if not th_comp_text:
                            th_comp_text = "No signups yet"

                        # Recreate the embed
                        embed = discord.Embed(
                            title=embed_data.get('title'),
                            description=embed_data.get('description'),
                            color=embed_data.get('color', 0x00ff00) 
                        )
                        embed.add_field(name="Total Signups", value=str(total_signups), inline=False)
                        embed.add_field(name="TH Composition", value=th_comp_text, inline=False)

                        # Update the existing message
                        if message_id:
                            try:
                                message = await interaction.channel.fetch_message(message_id)
                                await message.edit(embed=embed) 
                            except discord.NotFound:
                                print(f"Message {message_id} not found")
                            except Exception as e:
                                print(f"Error updating embed: {e}")

async def is_leader(interaction: discord.Interaction) -> bool:
    guild_id = interaction.guild_id
    user_roles = [role.id for role in interaction.user.roles]

    # Fetch leader roles from the API
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_BASE_URL}/api/servers/{guild_id}/leader_roles') as response:
            if response.status == 200:
                data = await response.json()
                leader_role_ids = data.get('leader_role_ids', [])
                return any(role_id in user_roles for role_id in leader_role_ids)
            else:
                return False
            
class EventView(discord.ui.View):
    def __init__(self, event_name):
        super().__init__(timeout=None)
        self.event_name = event_name

        # Add buttons with custom_id
        self.add_item(SignupButton(event_name))
        self.add_item(RemoveButton(event_name))
        self.add_item(CheckButton(event_name))
        self.add_item(CloseButton(event_name))
        self.add_item(ExportButton(event_name))

@client.tree.command(name="create_event", description="Create a new event")
async def create_event(interaction: discord.Interaction, event_name: str):
    await interaction.response.defer()
    guild_id = interaction.guild_id
    
    async with aiohttp.ClientSession() as session:
        # Create the event in Firestore
        async with session.post(
            f'{API_BASE_URL}/api/events',
            json={
                'event_name': event_name,
                'event_role': interaction.guild_id,
                'guild_id': guild_id
            }
        ) as response:
            data = await response.json()
            
            if response.status == 201:
                # Create a persistent view for the event
                view = EventView(event_name)
                
                # Create the embed
                embed = discord.Embed(
                    title=f"{event_name.upper()} Roster",
                    color=discord.Color.green()
                )
                embed.add_field(name="Total Signups", value="0", inline=False)
                embed.add_field(name="TH Composition", value="No signups yet", inline=False)
                
                # Send the embed to the channel
                message = await interaction.followup.send(embed=embed, view=view)
                
                # Store the message ID in Firestore
                async with session.post(
                    f'{API_BASE_URL}/api/events/{event_name}/update_message_id',
                    json={
                        'guild_id': guild_id,
                        'message_id': message.id
                    }
                ) as update_response:
                    if update_response.status != 200:
                        print(f"Failed to store message ID for event {event_name}: {update_response.status}")
                
                # Register the view for persistence
                client.add_view(view)
                print(f"Registered persistent view for new event: {event_name} in guild: {guild_id}")
                
            else:
                await interaction.followup.send(f"Error: {data.get('error', 'Unknown error')}")
                
class SignupButton(discord.ui.Button):
    def __init__(self, event_name):
        super().__init__(style=discord.ButtonStyle.green, row=0, label="Sign Up", custom_id= f'sign_up_{event_name}')
        self.event_name = event_name

    async def callback(self, interaction: discord.Interaction):
        modal = SignupModal(self.event_name)
        await interaction.response.send_modal(modal)

class RemoveButton(discord.ui.Button):
    def __init__(self, event_name):
        super().__init__(style=discord.ButtonStyle.red, row= 0, label="Remove", custom_id= f'remove_{event_name}')
        self.event_name = event_name

    async def callback(self, interaction: discord.Interaction):
        modal = RemoveModal(self.event_name)
        await interaction.response.send_modal(modal)

class ExportButton(discord.ui.Button):
    def __init__(self, event_name):
        super().__init__(style=discord.ButtonStyle.grey, row= 1, label="Export", custom_id= f'export_{event_name}')
        self.event_name = event_name

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild_id
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{API_BASE_URL}/api/events/{self.event_name}/export?guild_id={guild_id}') as response:
                if response.status == 200:
                    # Read the file content from the response
                    file_content = await response.read()
                    
                    # Send the file as an attachment
                    file = discord.File(fp=io.BytesIO(file_content), filename=f"{self.event_name}_export.xlsx")
                    await interaction.followup.send("Export successful! Here is the file:", file=file)
                else:
                    data = await response.json()
                    await interaction.followup.send(f"Export failed: {data.get('error', 'Unknown error')}")

class CheckButton(discord.ui.Button):
    def __init__(self, event_name):
        super().__init__(style=discord.ButtonStyle.blurple, row= 0, label="Check", custom_id= f'check_{event_name}')
        self.event_name = event_name

    async def callback(self, interaction: discord.Interaction):
        modal = CheckModal(self.event_name)
        await interaction.response.send_modal(modal)

class CloseButton(discord.ui.Button):
    def __init__(self, event_name):
        super().__init__(style=discord.ButtonStyle.danger, row= 1, label="Close", custom_id=f'close_{event_name}')
        self.event_name = event_name

    async def callback(self, interaction: discord.Interaction):
        modal = CloseConfirmationModal(self.event_name)
        await interaction.response.send_modal(modal)


class CloseConfirmationModal(discord.ui.Modal, title="Close Registration Confirmation"):
    def __init__(self, event_name):
        super().__init__()
        self.event_name = event_name
        
    confirmation = discord.ui.TextInput(
        label="Type 'Yes' to confirm closing registration",
        placeholder="Yes/No",
        required=True,
        max_length=3
    )

    async def on_submit(self, interaction: discord.Interaction):
        if not await is_leader(interaction):
            await interaction.response.send_message("You do not have permission to perform this action.", ephemeral=True)
            return
    
        await interaction.response.defer()
        guild_id = interaction.guild_id
        
        # Check confirmation response
        response = str(self.confirmation).lower()
        if response not in ['yes', 'y']:
            await interaction.followup.send(
                "Registration closure cancelled.",
                ephemeral=True
            )
            return
            
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{API_BASE_URL}/api/events/{self.event_name}/close', json= {'guild_id': guild_id}
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    # Update the original message embed to show closed status
                    if self.event_name in client.event_messages:
                        try:
                            message_id = client.event_messages[self.event_name]
                            message = await interaction.channel.fetch_message(message_id)
                            
                            # Get the current embed
                            current_embed = message.embeds[0]
                            
                            # Create new embed with closed status
                            new_embed = discord.Embed(
                                title=f"🔒 {self.event_name} Roster (CLOSED)",
                                color=discord.Color.red()
                            )
                            
                            # Copy existing fields
                            for field in current_embed.fields:
                                new_embed.add_field(
                                    name=field.name,
                                    value=field.value,
                                    inline=field.inline
                                )
                            
                            # Update the message
                            await message.edit(embed=new_embed)

                        except Exception as e:
                            await interaction.followup.send(
                              f"Error: {data.get('error', 'Unknown error')}",
                              ephemeral=True
                            )

                            
                    await interaction.followup.send(
                        "✅ Registration has been closed successfully!",
                        ephemeral=True
                    )
                    
                    # Send a public message to notify everyone
                    await interaction.channel.send(
                        f"🔒 Registration for **{self.event_name}** has been closed by {interaction.user.mention}"
                    )
                else:
                    await interaction.followup.send(
                        f"Error: {data.get('error', 'Unknown error')}",
                        ephemeral=True
                    )

class CheckModal(discord.ui.Modal, title="Check Player Status"):
    def __init__(self, event_name):
        super().__init__()
        self.event_name = event_name
        
    player_tag = discord.ui.TextInput(
        label="Player Tag to Check",
        placeholder="#ABCD1234",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{API_BASE_URL}/api/events/{self.event_name}/check',
                json={'player_tag': str(self.player_tag), 'guild_id': guild_id}
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    if data['is_signed_up']:
                        player_data = data['player_data']
                        embed = discord.Embed(
                            title="Player Status Check",
                            description="✅ Player is signed up!",
                            color=discord.Color.green()
                        )
                        embed.add_field(
                            name="Player Details",
                            value=f"""
                            **Name:** {player_data['name']}
                            **Tag:** {str(self.player_tag)}
                            **TH Level:** {player_data['th_level']}
                            **Discord:** {player_data['discord_name']}
                            """,
                            inline=False
                        )
                    else:
                        embed = discord.Embed(
                            title="Player Status Check",
                            description="❌ Player is not signed up",
                            color=discord.Color.red()
                        )
                        embed.add_field(
                            name="Player Tag",
                            value=str(self.player_tag),
                            inline=False
                        )
                    
                    await interaction.followup.send(embed=embed, ephemeral=True)
                else:
                    await interaction.followup.send(
                        f"Error: {data.get('error', 'Unknown error')}",
                        ephemeral=True
                    )

class SignupModal(discord.ui.Modal, title="Sign Up"):
    def __init__(self, event_name):
        super().__init__()
        self.event_name = event_name
        
    player_tag = discord.ui.TextInput(
        label="Player Tag",
        placeholder="#ABCD1234",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild_id
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{API_BASE_URL}/api/events/{self.event_name}/signup',
                json={
                    'player_tag': str(self.player_tag),
                    'discord_name': str(interaction.user),
                    'guild_id': guild_id
                }
            ) as response:
                data = await response.json()
                
                if response.status == 201:
                    # Update TH counts
                    player_th = data['player_th']
                    client.th_counts[self.event_name][player_th] += 1
                    
                    # Update the embed
                    await update_embed(interaction, self.event_name)
                    
                    await interaction.followup.send(
                        f"Successfully signed up {data['player_name']} (TH{player_th})",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"Error: {data.get('error', 'Unknown error')}",
                        ephemeral=True
                    )

class RemoveModal(discord.ui.Modal, title="Remove Player"):
    def __init__(self, event_name):
        super().__init__()
        self.event_name = event_name
        
    player_tag = discord.ui.TextInput(
        label="Player Tag to Remove",
        placeholder="#ABCD1234",
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        guild_id = interaction.guild_id

        if_leader = await is_leader(interaction)
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{API_BASE_URL}/api/events/{self.event_name}/remove',
                json={
                    'player_tag': str(self.player_tag),
                    'requester_discord_name': str(interaction.user),
                    'is_leader': if_leader,
                    'guild_id': guild_id  
                }
            ) as response:
                data = await response.json()
                
                if response.status == 200:
                    # Get player data from the response
                    player_data = data.get('player_data', {})
                    player_th = player_data.get('player_th')
                    player_name = player_data.get('player_name', 'Unknown Player')
                    
                    # Update TH counts
                    if player_th and client.th_counts[self.event_name][player_th] > 0:
                        client.th_counts[self.event_name][player_th] -= 1
                    
                    # Update the embed
                    await update_embed(interaction, self.event_name)
                    
                    await interaction.followup.send(
                        f"✅ Successfully removed {player_name} (TH{player_th}) from the roster",
                        ephemeral=True
                    )
                else:
                    await interaction.followup.send(
                        f"Error: {data.get('error', 'Unknown error')}",
                        ephemeral=True
                    )

async def get_event_choices(interaction: discord.interactions, current: str) -> List[app_commands.Choice[str]]:
    choices = []
    guild_id = interaction.guild_id
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_BASE_URL}/api/events?guild_id={guild_id}') as response:
            if response.status == 200:
                data = await response.json()
                events = data.get('events', [])
                
                for event in events:
                    event_name = event.get('event_name', '')
                    if event_name:
                        # Add signup count to the name for better context
                        signup_count = event.get('signup_count', 0)
                        display_name = f"{event_name} ({signup_count} signups)"
                        choices.append(app_commands.Choice(name=display_name, value=event_name))
    
    return choices

@client.tree.command(name="delete_event", description="Delete an existing event")
@app_commands.describe(event_name="Select the event to delete")
@app_commands.autocomplete(event_name = get_event_choices)
async def delete_event(interaction: discord.Interaction, event_name: str):
    """Delete an event and its associated Discord messages"""
    await interaction.response.defer()
    
    if await is_leader(interaction): 
        view = ConfirmDeletionView(event_name)
        await interaction.followup.send(
            f"⚠️ Are you sure you want to delete the event **{event_name}**? This action cannot be undone.",
            view=view,
            ephemeral=True
        )
    else:
        await interaction.followup.send("❌ You do not have the permission to delete event!", ephemeral=True)

class ConfirmDeletionView(discord.ui.View):
    def __init__(self, event_name):
        super().__init__(timeout=60)
        self.event_name = event_name
    
    @discord.ui.button(label="Confirm Deletion", style=discord.ButtonStyle.danger)
    async def confirm_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        guild_id = interaction.guild_id
        
        # Delete the event from the database
        async with aiohttp.ClientSession() as session:
            async with session.delete(f'{API_BASE_URL}/api/events/{self.event_name}?guild_id={ guild_id}') as response:
                if response.status == 200:
                    # Remove the message from Discord if it exists
                    if self.event_name in client.event_messages:
                        try:
                            message_id = client.event_messages[self.event_name]
                            message = await interaction.channel.fetch_message(message_id)
                            await message.delete()
                            
                            # Remove from tracking
                            del client.event_messages[self.event_name]
                            if self.event_name in client.th_counts:
                                del client.th_counts[self.event_name]
                                
                            await interaction.followup.send(
                                f"✅ Event **{self.event_name}** has been successfully deleted!",
                                ephemeral=True
                            )
                            
                            # Post public notification
                            await interaction.channel.send(
                                f"🗑️ Event **{self.event_name}** has been deleted by {interaction.user.mention}"
                            )
                        except discord.NotFound:
                            await interaction.followup.send(
                                f"✅ Event deleted from database, but message could not be found in Discord.",
                                ephemeral=True
                            )
                        except Exception as e:
                            await interaction.followup.send(
                                f"❌ Event deleted from database, but there was an error removing the Discord message: {str(e)}",
                                ephemeral=True
                            )
                    else:
                        await interaction.followup.send(
                            f"✅ Event **{self.event_name}** has been deleted from the database, but no associated Discord message was found.",
                            ephemeral=True
                        )
                else:
                    data = await response.json()
                    await interaction.followup.send(
                        f"❌ Failed to delete event: {data.get('error', 'Unknown error')}",
                        ephemeral=True
                    )
        
        # Disable all buttons
        for child in self.children:
            child.disabled = True
        
        await interaction.edit_original_response(view=self)
    
    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        # Disable all buttons
        for child in self.children:
            child.disabled = True
            
        await interaction.response.edit_message(
            content="Event deletion cancelled.",
            view=self
        )

@client.tree.command(name="toggle_leader", description="Add or remove a role as a leader")
@app_commands.describe(role="The role to add or remove as a leader")
async def toggle_leader(interaction: discord.Interaction, role: discord.Role):
    guild_id = interaction.guild_id
    role_id = role.id

    # Check if the requester is an admin or has permissions to manage leaders
    if not interaction.user.guild_permissions.administrator:
        await interaction.response.send_message("You do not have permission to manage leaders.", ephemeral=True)
        return

    # Check if the role is already a leader
    async with aiohttp.ClientSession() as session:
        async with session.get(f'{API_BASE_URL}/api/servers/{guild_id}/leader_roles') as response:
            if response.status == 200:
                data = await response.json()
                leader_role_ids = data.get('leader_role_ids', [])
            else:
                await interaction.response.send_message("Failed to fetch leader roles.", ephemeral=True)
                return

    # Toggle the role's leader status
    if role_id in leader_role_ids:
        # Remove the role
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{API_BASE_URL}/api/servers/{guild_id}/remove_leader_role',
                json={'role_id': role_id}
            ) as response:
                if response.status == 200:
                    await interaction.response.send_message(f"✅ Removed the role {role.name} from the leader list.", ephemeral=True)
                else:
                    await interaction.response.send_message("Failed to remove leader role.", ephemeral=True)
    else:
        # Add the role
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f'{API_BASE_URL}/api/servers/{guild_id}/add_leader_role',
                json={'role_id': role_id}
            ) as response:
                if response.status == 200:
                    await interaction.response.send_message(f"✅ Added the role {role.name} as a leader.", ephemeral=True)
                else:
                    await interaction.response.send_message("Failed to add leader role.", ephemeral=True)

client.run(DISCORD_TOKEN)