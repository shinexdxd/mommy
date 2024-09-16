import discord
import json
from discord.ext import commands
import asyncio

class Memories(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load the config file with UTF-8 encoding
        with open("config/config.json", "r", encoding="utf-8") as f:
            self.config = json.load(f)

        # Set up memory channels from the config file
        self.memory_channels = self.config["memory_channels"]

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if payload.member.bot:
            return

        emoji = str(payload.emoji)
        if emoji in self.memory_channels:
            channel = self.bot.get_channel(payload.channel_id)
            if channel is None:
                return

            message = await channel.fetch_message(payload.message_id)
            if message is None:
                return

            guild = self.bot.get_guild(payload.guild_id)
            memory_channel_name = self.memory_channels[emoji]
            memory_channel = discord.utils.get(guild.text_channels, name=memory_channel_name)

            if memory_channel is None:
                return

            embed = discord.Embed(
                description=message.content,
                color=discord.Color.purple()
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
            embed.set_footer(text=f"Saved from {channel.name}")

            if message.attachments:
                embed.set_image(url=message.attachments[0].url)

            await memory_channel.send(embed=embed)