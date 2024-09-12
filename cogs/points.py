import discord
import sqlite3
from discord.ext import commands, tasks
import importlib.util
from core.utilities import db_connection, get_user_id_by_petname, get_petname
from core.bot_instance import bot

special_keywords = {
    'me': lambda ctx: (ctx.author.id, ctx.author.mention),
    'us': lambda ctx: (None, '@here')
}

class Points(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='leaderboard')
    async def leaderboard(self, ctx):
        print("leaderboard command called")  # Add this line to see if the command is being called
        conn = db_connection()
        cursor = conn.cursor()
        
        # Modify the query to also fetch petnames and ignore users with zero points
        cursor.execute('SELECT user_id, points, petname FROM users WHERE points > 0 ORDER BY points DESC LIMIT 10')
        leaderboard = cursor.fetchall()
        conn.close()

        if not leaderboard:
            await ctx.send("no points data available.")
            return

        embed = discord.Embed(title="Points Leaderboard", color=discord.Color.green())
        
        for idx, (user_id, points, petname) in enumerate(leaderboard, start=1):
            user = self.bot.get_user(user_id)
            user_name = user.name if user else "unknown user"  # Default to "Unknown User" if user is not in cache

            # If petname exists, use it; otherwise, fallback to the username
            display_name = petname+' ('+user_name+')' if petname else user_name

            embed.add_field(name=f"{idx}. {display_name}", value=f"{points} points", inline=False)

        print("About to send embed")  # Add this line to see if the command is getting to this point
        await ctx.send(embed=embed)
        print("Embed sent")  # Add this line to see if the command is successfully sending the embed


    @commands.command(name='givepoints')
    async def give_points(self, ctx, user: str, points: int, *, reason: str):
        conn = db_connection()
        cursor = conn.cursor()

        if user in special_keywords:
            target_user_id, target_user_mention = special_keywords[user](ctx)
        else:
            # First, try to parse a user mention
            target_user = ctx.message.mentions
            if target_user:
                target_user_id = target_user[0].id
                target_user_mention = target_user[0].mention
            else:
                # Check if it's a petname
                target_user_id = get_user_id_by_petname(user)
                if target_user_id:
                    target_user_mention = user
                else:
                    await ctx.send(f"could not find a user or petname '{user}'.")
                    return

        # Award points
        if target_user_id is None:
            # Give points to everyone in the channel, excluding bot users
            for member in ctx.guild.members:
                if not member.bot:  # Ignore bot users
                    cursor.execute('INSERT INTO users (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points + ?', (member.id, points, points))
        else:
            cursor.execute('INSERT INTO users (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points + ?', (target_user_id, points, points))

        # Log points with the reason
        cursor.execute('INSERT INTO points_log (user_id, points, reason) VALUES (?, ?, ?)', (target_user_id if target_user_id else None, points, reason))
        
        conn.commit()
        conn.close()

        if target_user_id is None:
            await ctx.send(f"gave {points} points to everyone in the channel with reason: '{reason}'.")
        else:
            await ctx.send(f"gave {points} points to {target_user_mention} with reason: '{reason}'.")

    @commands.command(name='viewpoints')
    async def view_points(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT points FROM users WHERE user_id = ?', (ctx.author.id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            points = result[0]
            await ctx.send(f"you have {points} points.")
        else:
            await ctx.send("you have no points.")

    @commands.command(name='resetpoints')
    @commands.has_permissions(administrator=True)
    async def reset_points(self, ctx, user: str = None):
        conn = db_connection()
        cursor = conn.cursor()
        
        if user is None:
            # No user specified, reset points for the command author
            user_id = ctx.author.id
            user_mention = ctx.author.mention
        else:
            # Check if the user input is a petname
            target_user_id = get_user_id_by_petname(user)
            if target_user_id:
                user_id = target_user_id
                user_mention = user
            else:
                # Check if it's a mention
                mentioned_user = ctx.message.mentions
                if mentioned_user:
                    user_id = mentioned_user[0].id
                    user_mention = mentioned_user[0].mention
                else:
                    await ctx.send(f"could not find a user or petname '{user}'.")
                    return

        cursor.execute('UPDATE users SET points = 0 WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

        await ctx.send(f"reset points for {user_mention} to zero.")