import discord
import json
from discord.ext import commands
from dotenv import load_dotenv
import os
import asyncio

class RoleReactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load the config file with UTF-8 encoding
        with open("config/config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Set up roles from the config file
        self.roles = self.config["roles"]
        self.memory_channels = self.config["memory_channels"]
        self.role_message_id = int(self.config["ROLE_MESSAGE_ID"])

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

        # Get existing reactions from the message
        existing_reactions = [str(reaction.emoji) for reaction in role_message.reactions]

        # Loop through the roles and add reactions if they don't already exist
        for emoji in self.roles.keys():
            if emoji not in existing_reactions:
                try:
                    await role_message.add_reaction(emoji)
                    await asyncio.sleep(0.5)  # Add a small delay to avoid rate limiting
                except discord.HTTPException as e:
                    print(f"failed to add reaction {emoji}: {e}")
            else:
                print(f"reaction {emoji} already exists.")

        print("reactions checked and added to the role message if missing.")

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.role_message_id:
            return  # Ignore other messages

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            print(f"Guild with ID {payload.guild_id} not found.")
            return

        emoji = str(payload.emoji)
        print(f"Received reaction: {emoji}")

        if emoji in self.roles:
            role_name = self.roles[emoji]
            print(f"Role name for emoji {emoji}: {role_name}")

            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                print(f"Found role: {role_name}")

                member = guild.get_member(payload.user_id)
                if member:
                    if member == self.bot.user:
                        return  # Don't give the role to the bot

                    await member.add_roles(role)
                    print(f"Added role {role_name} to {member.display_name}")
                    try:
                        await member.send(f"you have been given the {role_name} role!")
                    except discord.Forbidden:
                        print(f"Couldn't send a DM to {member.display_name}.")
            else:
                print(f"Role {role_name} not found.")
        else:
            print(f"Emoji {emoji} not in roles dictionary.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if payload.message_id != self.role_message_id:
            return  # Ignore other messages

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        emoji = str(payload.emoji)
        if emoji in self.roles:
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