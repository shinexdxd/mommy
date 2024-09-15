import sqlite3
from discord.ext import commands
import dateparser

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



#something with datetime strings - probably stupid
# def parse_datetime_str(datetime_str):
#     try:
#         reminder_time = dateparser.parse(datetime_str, relative=True)
#         if reminder_time is None:
#             raise ValueError("invalid datetime string")
#         return reminder_time
#     except ValueError as e:
#         print(f"error: {e}")
#         return None

# Helper function to get timezone abbreviation
def get_timezone_abbreviation(tz):
    # Map timezone offsets to abbreviations
    # You might need to update this mapping to cover all necessary timezones
    tz_map = {
        'America/Chicago': 'CDT',
        'America/New_York': 'EDT',
        'Europe/London': 'BST',
        'UTC': 'UTC'
}
    return tz_map.get(tz.key, 'UTC')  # Fallback to 'UTC' if abbreviation is not found




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

    if petname:
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


