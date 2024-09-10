import discord
from utilities import db_connection
import sqlite3
import asyncio
from datetime import datetime, timedelta
import re
import points
import reminders
import tasks
import rewards
from robot import bot
from dotenv import load_dotenv
import os

# Event: When the bot is ready
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    for guild in bot.guilds:
        channel = guild.text_channels[5]  # Send to channel 5
        await channel.send("online, baking pie.")

# Command: Simple hello command
@bot.command(name='hello')
async def hello(ctx):
    await ctx.send('hello, cutie!')


# Command: Simple hello command
@bot.command(name='treat?')
async def treat(ctx):
    await ctx.send('NO TREAT.')


# Command: Set Petname
@bot.command(name='setpetname')
async def set_petname(ctx, *, petname: str):
    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET petname = ? WHERE user_id = ?', (petname, ctx.author.id))
    conn.commit()
    conn.close()

    await ctx.send(f"your petname has been set to '{petname}'.")

# Command: List Commands
@bot.command(name='commands')
async def list_commands(ctx):
    embed = discord.Embed(title="Available Commands", color=discord.Color.blue())
    embed.add_field(name="hello", value="greet the bot.", inline=False)
    embed.add_field(name="setpetname", value="set your preferred submissive petname.", inline=False)
    embed.add_field(name="addtask", value="add a task with points. usage: `mommy, addtask <points> <task>`", inline=False)
    embed.add_field(name="viewtasks", value="view all your tasks.", inline=False)
    embed.add_field(name="completetask", value="complete a task by id and optionally award points to a user. usage: `mommy, completetask <task_id> [<user>]`", inline=False)
    embed.add_field(name="viewreminders", value="view all your reminders.", inline=False)
    embed.add_field(name="deletereminder", value="delete a reminder by id. usage: `mommy, deletereminder <reminder_id>`", inline=False)
    embed.add_field(name="givepoints", value="give points to a user or everyone with a reason. usage: `mommy, givepoints <user> <points> <reason>`", inline=False)
    embed.add_field(name="viewpoints", value="view your total points.", inline=False)
    embed.add_field(name="resetpoints", value="reset points for a user. usage: `mommy, resetpoints <user>`", inline=False)
    embed.add_field(name="commands", value="list all commands with usage examples.", inline=False)
    embed.add_field(name="leaderboard", value="view points leaderboard.", inline=False)
    embed.add_field(name="createreward", value="`mommy, createreward <point_value> <description>", inline=False)
    embed.add_field(name="claimreward", value="`mommy, claimreward <reward_id>` - claim a reward for points.", inline=False)
    embed.add_field(name="viewrewards", value="`mommy, viewrewards` - view all available rewards.", inline=False)
    await ctx.send(embed=embed)

load_dotenv()  # Load environment variables from .env file
TOKEN = os.getenv('DISCORD_TOKEN')  # Get the token from environment variables

bot.run(TOKEN)
