import discord
from discord.ext import commands
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
from core.utilities import db_connection
#partially functional - reminders are limited capability and never actually fire/trigger after being entered into the database

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # Create Reminder Command: Remind
    @commands.command(name='remind')
    async def remind(self, ctx, *, datetime_label: str):
        print(f"Received remind command with input: {datetime_label}")
        pattern = r"(in|at)\s*(\d+[a-zA-Z]+)\s*(.*)"
        match = re.match(pattern, datetime_label)
        print(f"Match result: {match}")
        
        # Handling datetime and target identification
        if match is None:
            # Handling 'me', 'us', or user mentions
            if datetime_label.lower().startswith("me"):
                target = ctx.author
                datetime_label = datetime_label[3:].strip()
            elif datetime_label.lower().startswith("us"):
                target = ctx.guild
                datetime_label = datetime_label[3:].strip()
            else:
                # Check for a user mention
                user_mention_pattern = r"<@!?(\d+)>"
                user_mention_match = re.search(user_mention_pattern, datetime_label)
                if user_mention_match:
                    target = await ctx.guild.fetch_member(int(user_mention_match.group(1)))
                    datetime_label = datetime_label.replace(user_mention_match.group(0), "").strip()
                else:
                    print("Match is none, sending error message")
                    await ctx.send("Invalid datetime string or label.")
                    return

            # Re-match the datetime_label
            match = re.match(pattern, datetime_label)
            if match is None:
                print("Match is none, sending error message")
                await ctx.send("Invalid datetime string or label.")
                return

        # If match is found, extract datetime and label
        print("Match is not none, extracting groups")
        datetime_str = match.group(2)
        print(f"Datetime string: {datetime_str}")
        label = match.group(3)
        print(f"Label: {label}")

        def parse_datetime_str(datetime_str):
            datetime_pattern = r"(\d+)([a-zA-Z]+)"
            match_datetime = re.match(datetime_pattern, datetime_str)
            if match_datetime:
                duration = int(match_datetime.group(1))
                unit = match_datetime.group(2)
                if unit == "s":
                    reminder_time = datetime.utcnow() + timedelta(seconds=duration)
                elif unit == "m":
                    reminder_time = datetime.utcnow() + timedelta(minutes=duration)
                elif unit == "h":
                    reminder_time = datetime.utcnow() + timedelta(hours=duration)
                elif unit == "d":
                    reminder_time = datetime.utcnow() + timedelta(days=duration)
                elif unit == "w":
                    reminder_time = datetime.utcnow() + timedelta(weeks=duration)
                elif unit == "M":
                    reminder_time = datetime.utcnow() + relativedelta(months=duration)
                elif unit == "y":
                    reminder_time = datetime.utcnow() + relativedelta(years=duration)
                else:
                    raise ValueError("Unknown unit")

                return reminder_time

            # If unable to parse, raise an error
            raise ValueError("Invalid datetime string")

        # Parsing the datetime string
        print("Parsing datetime string")
        try:
            reminder_time = parse_datetime_str(datetime_str)
        except ValueError:
            await ctx.send("Invalid datetime string. Please use 'in <duration>'.")
            return

        # Round reminder time to the nearest minute
        reminder_time = reminder_time.replace(second=0, microsecond=0)

        # Storing the reminder in the database
        conn = db_connection()
        cursor = conn.cursor()

        print("Inserting reminder into database")
        try:
            if isinstance(target, discord.Member):
                cursor.execute('INSERT INTO uptime_contexts (user_id, reminder_time, reminder_message, type, target) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, reminder_time, label, 'reminder', target.id))
            else:
                cursor.execute('INSERT INTO uptime_contexts (user_id, reminder_time, reminder_message, type, target) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, reminder_time, label, 'reminder', ctx.guild.id))
            conn.commit()
        except Exception as e:
            print(f"Error inserting reminder into database: {e}")
            await ctx.send(f"Error inserting reminder into database: {e}")
            return

        conn.close()

        # Formatting the success message
        reminder_time_str = reminder_time.strftime('%Y-%m-%d %H:%M')

        if isinstance(target, discord.Member):
            target_str = target.mention  # Use the user's mention to actually tag them
        else:
            target_str = "@everyone"

        print("Sending success message")
        await ctx.send(f"Reminder set for {target_str} at {reminder_time_str} with label: {label}.")


    # Command: View Reminders
    @commands.command(name='viewreminders')
    async def view_reminders(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()
        
        print("checking reminders")
        cursor.execute('SELECT id, reminder_time, reminder_message FROM uptime_contexts WHERE type = \'reminder\'')
        print("cursor executed")
        try:
            reminders = cursor.fetchall()
            print("reminders:", reminders)
        except:
            print("error grabbing reminders from db")
        
        if not reminders:
            await ctx.send("you have no reminders.")
            return

        embed = discord.Embed(title="our reminders", color=discord.Color.blue())
        for reminder_id, reminder_time, reminder_message in reminders:
            embed.add_field(name=f"reminder id: {reminder_id}", value=f"time: {reminder_time}\nlabel: {reminder_message}", inline=False)
        
        await ctx.send(embed=embed)

    # Command: Delete Reminder
    @commands.command(name='deletereminder')
    async def delete_reminder(self, ctx, reminder_id: int):
        conn = db_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM uptime_contexts WHERE id = ? AND type = \'reminder\'', (reminder_id,))
        conn.commit()
        conn.close()

        await ctx.send(f"deleted reminder with id {reminder_id}.")