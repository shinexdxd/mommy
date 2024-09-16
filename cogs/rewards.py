import discord
import sqlite3
import shlex
from discord.ext import commands, tasks
from core.utilities import db_connection, get_user_id_by_petname, get_petname  # Import utility functions
from core.bot_instance import bot

class Rewards(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # View Rewards
    @commands.command(name='rewards', aliases=['viewrewards'])
    async def viewrewards(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()

        # Retrieve all rewards from the database
        cursor.execute("SELECT id, description, point_value, consumable FROM rewards ORDER BY point_value DESC")
        rewards = cursor.fetchall()

        # Create an embed to display the rewards
        embed = discord.Embed(title="**✨available rewards✨**", color=0x00ff00)

        for reward in rewards:
            id, description, point_value, consumable = reward
            consumable_text="consumable" if consumable else "nonconsumable"
            embed.add_field(name=f"**{description}**", value=f"{point_value} points\n{consumable_text} \nclaim id:{id}", inline=False)

        await ctx.send(embed=embed)

        if conn:
            conn.close()

    # Create Reward Helper
    async def create_reward_helper(self, ctx, description: str, point_value: int, consumable: bool, target_user_id: int):
        try:
            conn = db_connection()
            cursor = conn.cursor()

            # Insert a new reward into the database
            cursor.execute("INSERT INTO rewards (description, point_value, consumable, target_user_id) VALUES (?, ?, ?, ?)", (description, point_value, consumable, target_user_id))
            conn.commit()
            print("new reward inserted successfully!")

            # Send a confirmation message to the user
            await ctx.send(f"new reward created: **{description}** with {point_value} points!")

        except sqlite3.Error as e:
            print(f"error creating reward: {e}")
            await ctx.send("error creating reward. please try again later.")

        finally:
            if conn:
                conn.close()

    # CreateReward Command
    @commands.command(name='createreward')
    async def create_reward(self, ctx, description: str, point_value: int):
        consumable = None
        target_user_id = None

        # Ask if reward is consumable
        await ctx.send("is the reward consumable? (yes/no)")
        try:
            consumable_response = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
            consumable = consumable_response.content.lower() == 'yes'
        except asyncio.TimeoutError:
            await ctx.send("timeout: no response received. assuming reward is not consumable.")
            consumable = False

    # Ask who to tag
        await ctx.send("who should i tag? (mention a user or type 'no one' if none, or use 'me' or 'us' for yourself or the entire channel)")
        try:
            target_user_response = await self.bot.wait_for('message', check=lambda message: message.author == ctx.author, timeout=30)
            if target_user_response.content.lower() in ['no one', 'noone', 'nobody']:
                target_user_id = None
            elif target_user_response.content.lower() == 'me':
                target_user_id = ctx.author.id
                await ctx.send(f"Tagging yourself...")
            elif target_user_response.content.lower() == 'us':
                target_user_id = 'us'
                await ctx.send(f"Tagging the entire channel...")
            else:
                target_user = target_user_response.mentions[0]
                target_user_id = target_user.id
        except asyncio.TimeoutError:
            await ctx.send("timeout: no response received. assuming no target user.")
            target_user_id = None

        # Create the reward
        await self.create_reward_helper(ctx, description, point_value, consumable, target_user_id)

        # Create the reward
        conn = db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('INSERT INTO rewards (description, point_value, consumable, target_user_id) VALUES (?, ?, ?, ?)', (description, point_value, consumable, target_user_id))
            conn.commit()
            await ctx.send("reward created successfully!")
        except Exception as e:
            print(f"error creating reward: {e}")
            await ctx.send("error creating reward. please try again later.")
        finally:
            if conn:
                conn.close()

    # ClaimReward Command
    @commands.command(name='claimreward', aliases =['claim'])
    async def claim_reward(self, ctx, reward_id: int, user: discord.Member = None):
        conn = db_connection()
        cursor = conn.cursor()
        try:
            # Get reward details
            cursor.execute('SELECT description, point_value, consumable, target_user_id FROM rewards WHERE id = ?', (reward_id,))
            reward = cursor.fetchone()

            if reward is None:
                await ctx.send("reward not found.")
                return

            description, point_value, consumable, target_user_id = reward

            # Check user points
            cursor.execute('SELECT points FROM users WHERE user_id = ?', (ctx.author.id,))
            user_points = cursor.fetchone()
            if user_points is None or user_points[0] < point_value:
                await ctx.send("you don't have enough points to claim this reward.")
                return

            # Deduct points
            cursor.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (point_value, ctx.author.id))
            conn.commit()

            # Remove the reward if it's consumable
            if consumable:
                cursor.execute('DELETE FROM rewards WHERE id = ?', (reward_id,))
                conn.commit()

            # Log reward claim
            cursor.execute('INSERT INTO rewards_log (user_id, points, reason) VALUES (?, ?, ?)', (ctx.author.id, point_value, description))
            conn.commit()

        except Exception as e:
            await ctx.send(f"an error occurred: {e}")
            conn.rollback()
        finally:
            if conn:
                conn.close()

        # Notify the target user if specified
        if target_user_id == 'us':
            await ctx.send(f"congratulations! {ctx.author.mention} claimed the reward '{description}' worth {point_value} points. let's fuckin go!")
        elif target_user_id:
            target_user = bot.get_user(target_user_id)
            if target_user:
                await ctx.send(f"congratulations! {ctx.author.mention} claimed the reward '{description}' worth {point_value} points. {target_user.mention} 👀")
            else:
                await ctx.send(f"congratulations! {ctx.author.mention} claimed the reward '{description}' worth {point_value} points. however, the target user could not be found.")
        else:
            await ctx.send(f"congratulations! {ctx.author.mention} claimed the reward '{description}' worth {point_value} points.")


    # Remove Rewards
    @commands.command(name='removereward', aliases=['clearreward', 'deletereward'])
    @commands.has_permissions(administrator=True)  # Only allow admins to use this command
    async def remove_reward(self, ctx, reward_id: int):
        conn = db_connection()
        cursor = conn.cursor()

        # Check if the reward exists
        cursor.execute('SELECT description FROM rewards WHERE id = ?', (reward_id,))
        reward = cursor.fetchone()

        if reward is None:
            await ctx.send("reward not found.")
            conn.close()
            return

        # Remove the reward
        cursor.execute('DELETE FROM rewards WHERE id = ?', (reward_id,))
        conn.commit()
        conn.close()
        # Send a confirmation message to the channel
        await ctx.send(f"reward '{reward[0]}' with id {reward_id} has been removed successfully.")