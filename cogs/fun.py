import discord
import random
import json
import re
from discord.ext import commands
from core.utilities import db_connection, get_user_id_by_petname, get_petname
from core.bot_instance import bot

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.actions = self.load_actions()

    def load_actions(self):
        with open('config/config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        return config.get("actions", {})

    @commands.command(name='hello', aliases=['hello?', 'hello!', 'hello.', 'hi.', 'hi', 'hi!', 'hi?', 'hey', 'hey.', 'hey!'], help="greet the bot!")
    async def hello(self, ctx):
        print("hello command executed")
        petname = await get_petname(ctx)
        await ctx.send(f"hello, {petname}!")

    @commands.command(name='treat?', help='Ask mommy for a treat!')
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

    @commands.command(name='setpetname', help='manually set petname in the user database ❌ prefer to use role reactions to set pet names!')
    async def set_petname(self, ctx, *, petname: str):
        max_length = 30
        if len(petname) > max_length:
            await ctx.send(f"petname too long! please keep it under {max_length} characters.")
            return

        if any(ord(c) < 32 or ord(c) > 126 for c in petname):
            await ctx.send("invalid characters in petname. please use only printable characters.")
            return

        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET petname = ? WHERE user_id = ?', (petname, ctx.author.id))
        conn.commit()
        conn.close()

        await ctx.send(f"your petname has been set to '{petname}'.")

    @commands.command(name='names', help='list petnames from the users database')
    async def get_petnames(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id, petname FROM users WHERE petname IS NOT NULL')
        petnames = cursor.fetchall()
        conn.close()

        if not petnames:
            await ctx.send("no petnames found.")
        else:
            petname_list = []
            for user_id, petname in petnames:
                member = ctx.guild.get_member(user_id)
                if member and not member.bot:
                    petname_list.append(f"<@{user_id}>: {petname}")
            if petname_list:
                embed = discord.Embed(
                    title="✨ current petnames ✨",
                    description="\n".join(petname_list),
                    color=discord.Color.purple()
                )
                await ctx.send(embed=embed)
            else:
                await ctx.send("no petnames for non-bot users found.")

    @commands.command(name='bored', aliases=['bored!', 'bored.'], help='feeling bored? get a random action!')
    async def bored(self, ctx):
        if not self.actions:
            await ctx.send("no actions found in the configuration.")
            return

        action_key = random.choice(list(self.actions.keys()))
        action = self.actions.get(action_key)
        if action:
            message = action["message"]
            gif_url = action["gif_url"]

            embed = discord.Embed(description=message, color=discord.Color.green())
            embed.set_image(url=gif_url)
            await ctx.send(embed=embed)
        else:
            await ctx.send("an error occurred while fetching an action.")
