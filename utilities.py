import sqlite3
from discord.ext import commands

# Database connection
def db_connection():
    conn = sqlite3.connect('bot_database.db')
    return conn

# Petname Function
def get_user_id_by_petname(petname):
    conn = db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT user_id FROM users WHERE petname = ?', (petname,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None