import discord
import json
from discord.ext import commands

class Memories(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Load config from config/config.json with UTF-8 encoding
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Set up emoji to channel mapping from the config file
        self.memory_channels = config['memory_channels']

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        # Make sure the bot doesn't react to itself
        if payload.member.bot:
            return

        # Get the emoji that was reacted
        emoji = str(payload.emoji)

        # Check if it's a specified memory emoji
        if emoji in self.memory_channels:
            # Get the channel where the message was posted
            channel = self.bot.get_channel(payload.channel_id)
            if channel is None:
                return

            # Get the message that was reacted to
            message = await channel.fetch_message(payload.message_id)
            if message is None:
                return

            # Get the target memory channel by its name
            guild = self.bot.get_guild(payload.guild_id)
            memory_channel_name = self.memory_channels[emoji]
            memory_channel = discord.utils.get(guild.text_channels, name=memory_channel_name)

            if memory_channel is None:
                return  # If the target channel doesn't exist, do nothing

            # Create an embed with the message details
            embed = discord.Embed(
                description=message.content,
                color=discord.Color.purple()
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.avatar.url)
            embed.set_footer(text=f"Saved from {channel.name}")

            # If there are any attachments, add them to the embed
            if message.attachments:
                embed.set_image(url=message.attachments[0].url)  # Show the first attachment as an image

            # Send the embed to the memory channel
            await memory_channel.send(embed=embed)
