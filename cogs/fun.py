from robot import bot
from discord.ext import commands, tasks
import discord
import random
from utilities import db_connection, get_user_id_by_petname  # Import utility functions

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello')
    async def hello(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT petname FROM users WHERE user_id = ?', (ctx.author.id,))
        petname = cursor.fetchone()

        conn.close()

        if petname:
            await ctx.send(f"hello, {petname[0]}!")
        else:
            await ctx.send('hello, cutie!')

    @commands.command(name='treat?')
    async def treat(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT petname FROM users WHERE user_id = ?', (ctx.author.id,))
        petname = cursor.fetchone()

        conn.close()

        if petname:
            petname = petname[0]
        else:
            petname = 'cutie'

        responses = [
            'NO TREAT.',
            'NO TREAT.',
            'NO TREAT.',
            'NO TREAT!',
            'treats are overrated.',
            f'okay, you can have a treat, {petname}.',
            'NO. TREAT.',
        ]

        await ctx.send(random.choice(responses))

    @commands.command(name='setpetname')
    async def set_petname(self, ctx, *, petname: str):
        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute('UPDATE users SET petname = ? WHERE user_id = ?', (petname, ctx.author.id))
        conn.commit()
        conn.close()

        await ctx.send(f"your petname has been set to '{petname}'.")