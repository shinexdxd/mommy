import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Get bot and reminder channels from .env
BOT_CHANNEL = int(os.getenv('BOT_CHANNEL'))
REMINDER_CHANNEL = int(os.getenv('REMINDER_CHANNEL'))

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

def get_prefix(bot, msg):
    if msg.channel.id == BOT_CHANNEL:  # Use the loaded BOT_CHANNEL variable
        return ''
    else:
        return 'mommy, '

bot = commands.Bot(command_prefix=get_prefix, intents=intents)

# Your other bot code follows...


bot = commands.Bot(command_prefix=get_prefix, intents=intents)
