import discord
from discord.ext import commands
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

def get_prefix(bot, msg):
    if msg.channel.id == 1282898835848564858:  # Replace with the desired channel ID
        return ''
    else:
        return 'mommy, '

bot = commands.Bot(command_prefix=get_prefix, intents=intents)
