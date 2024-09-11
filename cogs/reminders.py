from robot import bot
import asyncio
from datetime import datetime, timedelta
import re
from utilities import db_connection
from discord.ext import commands, tasks


class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Command: View Reminders
    @commands.command(name='viewreminders')
    async def view_reminders(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, reminder_time, label FROM reminders WHERE user_id = ?', (ctx.author.id,))
        reminders = cursor.fetchall()
        conn.close()
        
        if not reminders:
            await ctx.send("you have no reminders.")
            return

        embed = discord.Embed(title="our reminders", color=discord.Color.blue())
        for reminder_id, reminder_time, label in reminders:
            embed.add_field(name=f"Reminder ID: {reminder_id}", value=f"Time: {reminder_time}\nLabel: {label}", inline=False)
        
        await ctx.send(embed=embed)

    # Command: Delete Reminder
    @commands.command(name='deletereminder')
    async def delete_reminder(self, ctx, reminder_id: int):
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, ctx.author.id))
        conn.commit()
        conn.close()

        await ctx.send(f"deleted reminder with ID {reminder_id}.")

    # Command: Set Reminder
    @commands.command(name='remind')
    async def remind(self, ctx, target: str, datetime_str: str, *, label: str):
        conn = db_connection()
        cursor = conn.cursor()

        # Parse target (me, us, or a user mention)
        if target.lower() == 'me':
            target_id = ctx.author.id
            target_mention = ctx.author.mention
        elif target.lower() == 'us':
            target_id = ctx.guild.id
            target_mention = '@here'
        else:
            try:
                target_id = int(re.sub(r'[<>@!]', '', target))
                target_mention = f'<@{target_id}>'
            except ValueError:
                await ctx.send("invalid target. please use 'me', 'us', or a user mention.")
                return

        # Parse datetime string
        try:
            if datetime_str.startswith('at '):
                reminder_time = datetime.fromisoformat(datetime_str[3:])
            elif datetime_str.startswith('in '):
                duration_str = datetime_str[3:]
                duration_parts = duration_str.split()
                duration_seconds = 0
                for part in duration_parts:
                    if part.endswith('s'):
                        duration_seconds += int(part[:-1])
                    elif part.endswith('m'):
                        duration_seconds += int(part[:-1]) * 60
                    elif part.endswith('h'):
                        duration_seconds += int(part[:-1]) * 3600
                    elif part.endswith('d'):
                        duration_seconds += int(part[:-1]) * 86400
                reminder_time = datetime.now() + timedelta(seconds=duration_seconds)
            else:
                await ctx.send("invalid datetime string. please use 'at <datetime>' or 'in <duration>'.")
                return
        except ValueError:
            await ctx.send("invalid datetime string. please use a valid iso 8601 datetime or duration.")
            return

        # Insert reminder into database
        cursor.execute('INSERT INTO reminders (user_id, reminder_time, label) VALUES (?, ?, ?)', (target_id, reminder_time, label))
        conn.commit()
        conn.close()

        await ctx.send(f"reminder set for {target_mention} at {reminder_time} with label '{label}'.")