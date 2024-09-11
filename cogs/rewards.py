import discord
from robot import bot
import sqlite3
from discord.ext import commands, tasks
from utilities import db_connection, get_user_id_by_petname  # Import utility functions

class Rewards(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	# View Rewards
	@commands.command(name='viewrewards')
	async def viewrewards(self, ctx):
	    print("viewrewards command called!")
	    conn = db_connection()
	    print("database connected successfully.")
	    cursor = conn.cursor()

	    # Retrieve all rewards from the database
	    cursor.execute('SELECT id, description, point_value, consumable FROM rewards')
	    print("query executed.")
	    rewards = cursor.fetchall()

	    # Create a Discord rich embed
	    embed = discord.Embed(title="Available Rewards", color=0x00ff00)

	    for reward in rewards:
	        reward_id, description, point_value, consumable = reward
	        embed.add_field(name=f"**{reward_id}**: {description}", value=f"Points: {point_value}\nConsumable: {'Yes' if consumable else 'No'}", inline=False)

	    # Send the embed to the user
	    await ctx.send(embed=embed)

	    conn.close()


	# Claim a Reward
	@commands.command(name='claimreward')
	async def claim_reward(ctx, reward_id: int, user: discord.Member = None):
		conn = db_connection()
		cursor = conn.cursor()

		# Get reward details
		cursor.execute('SELECT description, point_value, consumable, target_user_id FROM rewards WHERE id = ?', (reward_id,))
		reward = cursor.fetchone()

		if reward is None:
			await ctx.send("reward not found.")
			conn.close()
			return

		description, point_value, consumable, target_user_id = reward

		# Check user points
		cursor.execute('SELECT points FROM users WHERE user_id = ?', (ctx.author.id,))
		user_points = cursor.fetchone()
		if user_points is None or user_points[0] < point_value:
			await ctx.send("you don't have enough points to claim this reward.")
			conn.close()
			return

		# Deduct points
		cursor.execute('UPDATE users SET points = points - ? WHERE user_id = ?', (point_value, ctx.author.id))

		# Remove the reward if it's consumable
		if consumable:
			cursor.execute('DELETE FROM rewards WHERE id = ?', (reward_id,))
		
		# Log reward claim
		cursor.execute('INSERT INTO rewards_log (user_id, reward_id, description, point_value) VALUES (?, ?, ?, ?)', (ctx.author.id, reward_id, description, point_value))
		conn.commit()
		conn.close()

		# Notify the target user if specified
		if target_user_id:
			target_user = bot.get_user(target_user_id)
			if target_user:
				await ctx.send(f"congratulations! {ctx.author.mention} claimed the reward '{description}' worth {point_value} points. {target_user.mention} has been notified.")
			else:
				await ctx.send(f"congratulations! {ctx.author.mention} claimed the reward '{description}' worth {point_value} points. however, the target user could not be found.")
		else:
			await ctx.send(f"congratulations! {ctx.author.mention} claimed the reward '{description}' worth {point_value} points.")

	# Remove Rewards
	@commands.command(name='removereward')
	@commands.has_permissions(administrator=True)  # Only allow admins to use this command
	async def remove_reward(ctx, reward_id: int):
		conn = db_connection()
		cursor = conn.cursor()

		# Check if the reward exists
		cursor.execute('SELECT description FROM rewards WHERE id = ?', (reward_id,))
		reward = cursor.fetchone()

		if reward is None:
			await ctx.send("Reward not found.")
			conn.close()
			return

		# Remove the reward
		cursor.execute('DELETE FROM rewards WHERE id = ?', (reward_id,))
		conn.commit()
		conn.close()

		await ctx.send(f"reward with id {description} has been removed.")

	# Create a Reward
	@commands.command(name='createreward')
	async def create_reward(ctx, point_value: int, *, description: str):
		# Check if the point value is valid
		if point_value <= 0:
			await ctx.send("points value must be greater than 0.")
			return

		# Check if the description is valid
		if not description:
			await ctx.send("description cannot be empty.")
			return

		# Ask if the reward is consumable
		def check(m):
			return m.author == ctx.author and m.channel == ctx.channel

		await ctx.send("is this reward consumable? Reply with 'yes' or 'no'.")
		try:
			response = await bot.wait_for('message', timeout=30.0, check=check)
		except asyncio.TimeoutError:
			await ctx.send("you took too long to respond. please try again.")
			return

		if response.content.lower() in ['yes', 'y']:
			consumable = True
		elif response.content.lower() in ['no', 'n']:
			consumable = False
		else:
			await ctx.send("Invalid response. Reward not created.")
			return

		# Optional: Ask for a target user
		await ctx.send("optionally, mention a user who will be notified when the reward is claimed, or type 'none':")
		try:
			response = await bot.wait_for('message', timeout=30.0, check=check)
		except asyncio.TimeoutError:
			await ctx.send("you took too long to respond. reward created without a target user.")
			target_user_id = None
		else:
			if response.mentions:
				target_user_id = response.mentions[0].id
			elif response.content.lower() == 'none':
				target_user_id = None
			else:
				await ctx.send("invalid response. reward created without a target user.")
				target_user_id = None

		conn = db_connection()
		cursor = conn.cursor()
		
		cursor.execute('INSERT INTO rewards (description, point_value, consumable, target_user_id) VALUES (?, ?, ?, ?)', (description, point_value, consumable, target_user_id))
		conn.commit()
		conn.close()

		await ctx.send(f"reward created: '{description}' for {point_value} points. consumable: {'yes' if consumable else 'no'}. {'target user set.' if target_user_id else 'no target user.'}")
