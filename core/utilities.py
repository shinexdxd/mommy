import sqlite3
import discord
import os
import json
from discord.ext import commands, tasks
from dotenv import load_dotenv

# Load the .env file
env_path = os.path.join('config', '.env')
load_dotenv(dotenv_path=env_path)

# Load the config.json file
with open("config/config.json", "r", encoding="utf-8") as f:
    config = json.load(f)

BOT_CHANNEL_ID = int(os.getenv("BOT_CHANNEL"))
ROLE_MESSAGE_ID = int(config["ROLE_MESSAGE_ID"])
TITLE_MESSAGE_ID = int(config["TITLE_MESSAGE_ID"])

# Database connection
def db_connection():
    try:
        conn = sqlite3.connect('data/bot_database.db')
        return conn
    except sqlite3.Error as e:
        print(f"error connecting to database: {e}")
        return None

# Get User By Petname Function
def get_user_id_by_petname(petname, ctx=None):
    """
    Retrieves the user ID based on the petname or special keywords.
    If ctx is provided, special keywords like 'me' and 'us' are handled.
    """
    if ctx:
        special_keywords = {
            "me": lambda: ctx.author.id,
            "us": lambda: 1,  # Everyone
            "we": lambda: 1,  # Same as "us" for now
            "you": lambda: ctx.message.mentions[0].id if ctx.message.mentions else None
        }
        if petname in special_keywords:
            return special_keywords[petname]()
    
    # If petname is not a special keyword, query the database
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE petname = ?', (petname,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None

# Get Petname by User Function
async def get_petname(ctx):
    conn = db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute('SELECT petname FROM users WHERE user_id = ?', (ctx.author.id,))
        petname = cursor.fetchone()
    except Exception as e:
        print(f"failed to execute cursor: {e}")
        petname = None

    conn.close()

    # Check if petname is None or "no title" and return "cutie"
    if petname and petname[0].lower() != "no title":
        return petname[0]
    else:
        return 'cutie'
        
# Who is Us
special_keywords = {
    "me": lambda ctx: (ctx.author.id, ctx.author.mention),
    "us": lambda ctx: (None, "@here"),
    "we": lambda ctx: (None, "@here"),  # same as "us" for now
    "you": lambda ctx: (ctx.message.mentions[0].id, ctx.message.mentions[0].mention) if ctx.message.mentions else (None, None)
}

class CleanupTask:
    def __init__(self, bot):
        self.bot = bot
        self.cleanup.start()

    @tasks.loop(hours=24)
    async def cleanup(self):
        bot_channel = self.bot.get_channel(BOT_CHANNEL_ID)
        if not bot_channel:
            print(f"could not find channel with ID {BOT_CHANNEL_ID}")
            return

        async for message in bot_channel.history(limit=100):  # Adjust limit as needed
            if message.id not in [ROLE_MESSAGE_ID, TITLE_MESSAGE_ID]:
                try:
                    await message.delete()
                    print(f"deleted message from {message.author}: {message.content}")
                except discord.Forbidden:
                    print("missing permissions to delete messages.")
                except discord.HTTPException as e:
                    print(f"failed to delete message: {e}")

    @cleanup.before_loop
    async def before_cleanup(self):
        await self.bot.wait_until_ready()
