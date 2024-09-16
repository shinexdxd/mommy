import discord
from discord.ext import commands

class RoleReactions(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_message_id = 1285044045466566676  # Replace with your message ID
        self.roles = {
            '🍆': '🍆 horny',   # Role for nsfw and rp channels
            '🔀': '🔀 switchy',  # Role for switchspace channel
        }

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.message_id != self.role_message_id:
            return  # Ignore other messages

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return  # If the bot can't find the guild, stop

        emoji = str(payload.emoji)
        if emoji in self.roles:
            role_name = self.roles[emoji]
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                member = guild.get_member(payload.user_id)
                if member:
                    await member.add_roles(role)
                    await member.send(f"you have been given the {role_name} role!")

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
                    await member.send(f"the {role_name} role has been removed.")
