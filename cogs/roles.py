import discord
import json
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio
from core.utilities import db_connection, get_user_id_by_petname, get_petname
from core.bot_instance import bot

class RoleReactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load the config file with UTF-8 encoding
        with open("config/config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Set up roles and titles from the config file
        self.roles = self.config["roles"]
        self.titles = self.config["titles"]
        self.memory_channels = self.config["memory_channels"]
        self.role_message_id = int(self.config["ROLE_MESSAGE_ID"])
        self.title_message_id = int(self.config["TITLE_MESSAGE_ID"])

        # Load the BOT_CHANNEL from environment variables
        load_dotenv()
        self.bot_channel_id = int(os.getenv("BOT_CHANNEL"))

    @commands.Cog.listener()
    async def on_ready(self):
        print("on_ready called.")
        role_message_channel_id = self.bot_channel_id
        
        # Fetch the channel and message where reactions should be added
        role_message_channel = self.bot.get_channel(role_message_channel_id)
        if not role_message_channel:
            print(f"could not find channel with ID {role_message_channel_id}")
            return

        try:
            role_message = await role_message_channel.fetch_message(self.role_message_id)
        except discord.NotFound:
            print(f"could not find message with ID {self.role_message_id}")
            return

        try:
            title_message = await role_message_channel.fetch_message(self.title_message_id)
        except discord.NotFound:
            print(f"could not find message with ID {self.title_message_id}")
            return

        # Get existing reactions from the messages
        existing_role_reactions = [str(reaction.emoji) for reaction in role_message.reactions]
        existing_title_reactions = [str(reaction.emoji) for reaction in title_message.reactions]

        # Loop through the roles and add reactions if they don't already exist
        for emoji in self.roles.keys():
            if emoji not in existing_role_reactions:
                try:
                    await role_message.add_reaction(emoji)
                    await asyncio.sleep(0.5)  # Add a small delay to avoid rate limiting
                except discord.HTTPException as e:
                    print(f"failed to add reaction {emoji}: {e}")
            else:
                print(f"reaction {emoji} already exists for roles.")

        # Loop through the titles and add reactions if they don't already exist
        for emoji in self.titles.keys():
            if emoji not in existing_title_reactions:
                try:
                    await title_message.add_reaction(emoji)
                    await asyncio.sleep(0.5)
                except discord.HTTPException as e:
                    print(f"failed to add reaction {emoji}: {e}")
            else:
                print(f"reaction {emoji} already exists for titles.")

        print("reactions checked and added to both role and title messages if missing.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            print(f"Guild with ID {payload.guild_id} not found.")
            return

        emoji = str(payload.emoji)
        print(f"Received reaction: {emoji}")

        # Handle role reactions
        if payload.message_id == self.role_message_id:
            if emoji in self.roles:
                role_name = self.roles[emoji]
                print(f"Role name for emoji {emoji}: {role_name}")

                role = discord.utils.get(guild.roles, name=role_name)
                if role:
                    member = guild.get_member(payload.user_id)
                    if member and member != self.bot.user:
                        await member.add_roles(role)
                        print(f"Added role {role_name} to {member.display_name}")
                        try:
                            await member.send(f"you have been given the {role_name} role!")
                        except discord.Forbidden:
                            print(f"Couldn't send a DM to {member.display_name}.")
                else:
                    print(f"Role {role_name} not found.")

        # Handle title reactions and update petname
        elif payload.message_id == self.title_message_id:
            if emoji in self.titles:
                title_name = self.titles[emoji]
                print(f"Title for emoji {emoji}: {title_name}")

                title_role = discord.utils.get(guild.roles, name=title_name)
                if title_role:
                    member = guild.get_member(payload.user_id)
                    if member and member != self.bot.user:
                        await member.add_roles(title_role)
                        print(f"Added title {title_name} to {member.display_name}")
                        try:
                            await member.send(f"you have been given the {title_name} title!")
                        except discord.Forbidden:
                            print(f"Couldn't send a DM to {member.display_name}.")
                        
                        # Strip the emoji from the title before updating the petname
                        stripped_title = title_name.split(" ", 1)[1] if " " in title_name else title_name
                        print(f"Setting petname for {member.display_name} to {stripped_title}")
                        
                        # Update the petname in the database
                        conn = db_connection()
                        cursor = conn.cursor()
                        cursor.execute('UPDATE users SET petname = ? WHERE user_id = ?', (stripped_title, member.id))
                        conn.commit()
                        conn.close()

                        print(f"Updated petname to {stripped_title} for user {member.display_name}")
                else:
                    print(f"Title {title_name} not found.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        emoji = str(payload.emoji)

        # Handle role reactions
        if payload.message_id == self.role_message_id and emoji in self.roles:
            role_name = self.roles[emoji]
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.remove_roles(role)
                    try:
                        await member.send(f"the {role_name} role has been removed.")
                    except discord.Forbidden:
                        print(f"Couldn't send a DM to {member.display_name}.")

        # Handle title reactions
        elif payload.message_id == self.title_message_id and emoji in self.titles:
            title_name = self.titles[emoji]
            title_role = discord.utils.get(guild.roles, name=title_name)
            if title_role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.remove_roles(title_role)
                    try:
                        await member.send(f"the {title_name} title has been removed.")
                    except discord.Forbidden:
                        print(f"Couldn't send a DM to {member.display_name}.")
