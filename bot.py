import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os
import asyncio
from cogs.uptime import Uptime
from cogs.reminders import Reminders
from cogs.points import Points
from cogs.rewards import Rewards
from cogs.tasks import Tasks
from cogs.fun import Fun

# Initialize intents
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# Initialize bot with intents and custom command prefix
bot = commands.Bot(command_prefix=lambda msg: 'mommy, ' if msg.channel.id not in [1282898835848564858] else '', intents=intents)

# Load environment variables from .env file
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

async def load_cogs():
    try:
        await bot.add_cog(Uptime(bot))
        print("successfully loaded uptime cog.")
    except Exception as e:
        print(f"failed to load uptime cog: {e}")

    try:
        await bot.add_cog(Reminders(bot))
        print("successfully loaded reminders cog.")
    except Exception as e:
        print(f"failed to load reminders cog: {e}")

    try:
        await bot.add_cog(Points(bot))
        print("successfully loaded points cog.")
    except Exception as e:
        print(f"failed to load points cog: {e}")

    try:
        await bot.add_cog(Tasks(bot))
        print("successfully loaded tasks cog.")
    except Exception as e:
        print(f"failed to load tasks cog: {e}")

    try:
        await bot.add_cog(Rewards(bot))
        print("successfully loaded rewards cog.")
    except Exception as e:
        print(f"failed to load rewards cog: {e}")

    try:
        await bot.add_cog(Fun(bot))
        print("successfully loaded fun cog.")
    except Exception as e:
        print(f"failed to load fun cog: {e}")


@bot.event
async def on_ready():
    print(f'{bot.user} has logged in.')
    await bot.wait_until_ready()  # Wait until the bot is fully ready
    channel = bot.get_channel(1282898835848564858)  # Replace CHANNEL_ID with the ID of the channel you want to send the message in
    await channel.send('online. baking pie.')

async def main():
    await load_cogs()
    await bot.start(TOKEN)

# Run the bot
asyncio.run(main())