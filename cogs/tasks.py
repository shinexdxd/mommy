from discord.ext import commands, tasks
import discord
from core.utilities import db_connection, get_user_id_by_petname, get_petname  # Import utility functions
from core.bot_instance import bot

class Tasks(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command: Add Task
    @commands.command(name='addtask')
    async def add_task(self, ctx, points: int, *, task: str):
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO tasks (user_id, points, task) VALUES (?, ?, ?)', (ctx.author.id, points, task))
        conn.commit()
        conn.close()

        await ctx.send(f"added task '{task}' with {points} points.")


    # Command: View Tasks
    @commands.command(name='viewtasks')
    async def view_tasks(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, points, task FROM tasks WHERE user_id = ?', (ctx.author.id,))
        tasks = cursor.fetchall()
        conn.close()
        
        if not tasks:
            await ctx.send("you have no tasks.")
            return

        sorted_tasks = sorted(tasks, key=lambda x: x[1], reverse=True)
        embed = discord.Embed(title="our tasks", color=discord.Color.blue())
        for task_id, points, task in sorted_tasks:
            embed.add_field(
                name=f"**{task}**",
                value=f"points: {points}**\n**completion id: {task_id}",
                inline=False
            )
        
        await ctx.send(embed=embed)

    # Command: Complete Task
    @commands.command(name='completetask')
    async def complete_task(self, ctx, task_id: int, user: str = None):
        conn = db_connection()
        cursor = conn.cursor()

        # Determine the target user
        if user is None:
            target_user_id = ctx.author.id
            target_user_mention = ctx.author.mention
        else:
            target_user = ctx.message.mentions
            if target_user:
                target_user_id = target_user[0].id
                target_user_mention = target_user[0].mention
            else:
                # Check if it's a petname
                target_user_id = get_user_id_by_petname(user)
                if target_user_id:
                    target_user_mention = f"{user}"
                else:
                    await ctx.send(f"could not find a user or petname '{user}'.")
                    conn.close()
                    return

        # Retrieve the task details
        cursor.execute('SELECT points, task FROM tasks WHERE id = ?', (task_id,))
        task = cursor.fetchone()

        if task is None:
            # Debug: Print out the SQL query and parameters
            print(f"SQL Query: SELECT points, task FROM tasks WHERE id = ?")
            print(f"Parameters: {(task_id,)}")

            await ctx.send("task not found.")
            conn.close()
            return

        points, task_name = task[0], task[1]
        cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
        conn.commit()

        # Update the user's points
        cursor.execute('INSERT INTO users (user_id, points) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET points = points + ?', (target_user_id, points, points))

        # Log the points awarded with reason
        cursor.execute('INSERT INTO points_log (user_id, points, reason) VALUES (?, ?, ?)', (target_user_id, points, f"completed task: {task_name}"))

        conn.commit()
        conn.close()

        await ctx.send(f"completed task {task_name} and awarded {points} points to {target_user_mention}.")

