import discord
import os
import asyncio
from discord.ext import commands, tasks
from dotenv import load_dotenv
from core.utilities import db_connection
from cogs.uptime import Uptime #tested, small features to add relating to autoreminder
from cogs.reminders import Reminders #tested, needs work
from cogs.points import Points #tested
from cogs.rewards import Rewards #tested
from cogs.tasks import Tasks #tested
from cogs.fun import Fun #tested
from core.bot_instance import bot

# load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

async def load_cogs():
    cogs = [Uptime, Reminders, Points, Tasks, Rewards, Fun]
    for cog in cogs:
        try:
            await bot.add_cog(cog(bot))
            print(f"successfully loaded {cog.__name__} cog.")
        except Exception as e:
            print(f"failed to load {cog.__name__} cog: {e}")

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')
    print("registered commands:")
    for command in bot.commands:
        print(f"  - {command.name}")
    await bot.wait_until_ready()  # wait until the bot is fully ready
    channel = bot.get_channel(1282898835848564858)  # move to config
    await channel.send('online. baking pie.')

async def main():
    await load_cogs()
    await bot.start(TOKEN)

# Run the bot
asyncio.run(main())