from discord.ext import commands, tasks
import discord
import random
from core.utilities import db_connection, get_user_id_by_petname, get_petname
from core.bot_instance import bot

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='hello', aliases=['hello?', 'hello!', 'hello.', 'hi.', 'hi', 'hi!', 'hi?', 'hey', 'hey.', 'hey!'])
    async def hello(self, ctx):
        print("hello command executed")
        petname = await get_petname(ctx)
        await ctx.send(f"hello, {petname}!")

    @commands.command(name='treat?')
    async def treat(self, ctx):
        petname = await get_petname(ctx)
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
    # Limit the pet name to 30 characters
    max_length = 30
    if len(petname) > max_length:
        await ctx.send(f"petname too long! please keep it under {max_length} characters.")
        return

    # Allow most Unicode characters, but disallow control characters (e.g., \n, \t)
    if any(ord(c) < 32 or ord(c) > 126 for c in petname):
        await ctx.send("invalid characters in petname. please use only printable characters.")
        return

    conn = db_connection()
    cursor = conn.cursor()

    cursor.execute('UPDATE users SET petname = ? WHERE user_id = ?', (petname, ctx.author.id))
    conn.commit()
    conn.close()

    await ctx.send(f"your petname has been set to '{petname}'.")

    #tested91124