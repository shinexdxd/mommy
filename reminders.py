from robot import bot
import asyncio
from datetime import datetime, timedelta
import re
from utilities import db_connection

# Command: View Reminders
@bot.command(name='viewreminders')
async def view_reminders(ctx):
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
@bot.command(name='deletereminder')
async def delete_reminder(ctx, reminder_id: int):
    conn = db_connection()
    cursor = conn.cursor()
    
    cursor.execute('DELETE FROM reminders WHERE id = ? AND user_id = ?', (reminder_id, ctx.author.id))
    conn.commit()
    conn.close()

    await ctx.send(f"deleted reminder with ID {reminder_id}.")