import discord
import os
import asyncio
import logging
from discord.ext import commands
from dotenv import load_dotenv
from core.utilities import db_connection, CleanupTask
from cogs.uptime import Uptime
from cogs.reminders import Reminders
from cogs.points import Points
from cogs.rewards import Rewards
from cogs.tasks import Tasks
from cogs.fun import Fun
from cogs.memories import Memories
from cogs.roles import RoleReactions
from core.bot_instance import bot

# Set up logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Load environment variables from .env file
env_path = os.path.join('config', '.env')
load_dotenv(dotenv_path=env_path)
TOKEN = os.getenv('DISCORD_TOKEN')

async def load_cogs():
    cogs = [Uptime, Reminders, Points, Tasks, Rewards, Fun, Memories, RoleReactions]
    for cog in cogs:
        try:
            await bot.add_cog(cog(bot))
            print(f"Successfully loaded {cog.__name__} cog.")
        except Exception as e:
            print(f"Failed to load {cog.__name__} cog: {e}")

async def run_cleanup_task():
    cleanup_task = CleanupTask(bot)  # Initialize CleanupTask
    await cleanup_task.cleanup()      # Run cleanup immediately

@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')
    print("registered commands:")
    for command in bot.commands:
        print(f"  - {command.name}")
    
    await bot.wait_until_ready()  # Wait until the bot is fully ready

    # Run the cleanup task before sending the online message
    await run_cleanup_task()
    
    channel = bot.get_channel(int(os.getenv('BOT_CHANNEL')))
    if channel:
        await channel.send('online. baking pie.')
    else:
        print('channel not found')

async def main():
    await load_cogs()
    await bot.start(TOKEN)

# Run the bot
asyncio.run(main())
