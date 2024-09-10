import discord
import utilities
from discord.ext import commands
# Create an instance of a bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Enable members intent
bot = commands.Bot(command_prefix='mommy, ', intents=intents)