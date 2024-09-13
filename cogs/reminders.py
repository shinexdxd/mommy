import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import re
from core.utilities import db_connection

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()  # start the background task when the cog is loaded

    def cog_unload(self):
        self.check_reminders.cancel()  # stop the background task when the cog is unloaded

    # Command: Create Reminder
    @commands.command(name='remind')
    async def remind(self, ctx, *, datetime_label: str):
        print(f"received remind command with input: {datetime_label}")
        pattern = r"(in|at)\s*(\d+[a-zA-Z]+)\s*(.*)"
        match = re.match(pattern, datetime_label)
        print(f"match result: {match}")

        # Handle datetime and target identification
        if match is None:
            # Handle 'me', 'us', or user mentions
            if datetime_label.lower().startswith("me"):
                target = ctx.author  # DM the user
                datetime_label = datetime_label[3:].strip()
            elif datetime_label.lower().startswith("us"):
                target = "us"  # Flag for "@here" in the channel
                datetime_label = datetime_label[3:].strip()
            else:
                # Check for a user mention
                user_mention_pattern = r"<@!?(\d+)>"
                user_mention_match = re.search(user_mention_pattern, datetime_label)
                if user_mention_match:
                    target = await ctx.guild.fetch_member(int(user_mention_match.group(1)))
                    datetime_label = datetime_label.replace(user_mention_match.group(0), "").strip()
                else:
                    print("invalid datetime string or label.")
                    await ctx.send("invalid datetime string or label.")
                    return

            # Re-match the datetime_label
            match = re.match(pattern, datetime_label)
            if match is None:
                print("invalid datetime string or label.")
                await ctx.send("invalid datetime string or label.")
                return

        # Extract datetime and label
        datetime_str = match.group(2)
        label = match.group(3)
        print(f"datetime string: {datetime_str}")
        print(f"label: {label}")

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

            raise ValueError("invalid datetime string")

        # Parse the datetime string
        try:
            reminder_time = parse_datetime_str(datetime_str)
        except ValueError:
            await ctx.send("invalid datetime string. please use 'in <duration>'.")
            return

        # Round reminder time to the nearest minute
        reminder_time = reminder_time.replace(second=0, microsecond=0)

        # Store the reminder in the database
        conn = db_connection()
        cursor = conn.cursor()

        print("inserting reminder into database")
        try:
            if target == "us":
                cursor.execute('INSERT INTO uptime_contexts (user_id, reminder_time, reminder_message, type, target) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, reminder_time, label, 'reminder', 1))  # Store 1 as the target for "us"
            elif isinstance(target, discord.Member):
                cursor.execute('INSERT INTO uptime_contexts (user_id, reminder_time, reminder_message, type, target) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, reminder_time, label, 'reminder', target.id))
            else:
                cursor.execute('INSERT INTO uptime_contexts (user_id, reminder_time, reminder_message, type, target) VALUES (?, ?, ?, ?, ?)', (ctx.author.id, reminder_time, label, 'reminder', ctx.guild.id))
            conn.commit()
        except Exception as e:
            print(f"error inserting reminder into database: {e}")
            await ctx.send(f"error inserting reminder into database: {e}")
            return

        conn.close()

        # Format success message
        reminder_time_str = reminder_time.strftime('%Y-%m-%d %H:%M')
        if target == "us":
            target_str = "@here"
        elif isinstance(target, discord.Member):
            target_str = target.mention  # Tag the user
        else:
            target_str = "@everyone"

        print("sending success message")
        await ctx.send(f"reminder set for {target_str} at {reminder_time_str} with label: {label}.")

    # Background task: Check Reminders
    @tasks.loop(minutes=1)
    async def check_reminders(self):
        conn = db_connection()
        cursor = conn.cursor()

        current_time = datetime.utcnow()
        print(f"checking reminders at {current_time}...")

        cursor.execute('SELECT id, user_id, reminder_time, reminder_message, target FROM uptime_contexts WHERE type = \'reminder\' AND reminder_time <= ?', (current_time,))
        reminders = cursor.fetchall()
        conn.close()

        for reminder_id, user_id, reminder_time, reminder_message, target in reminders:
            if target == 1:  # This is an "us" reminder
                channel = self.bot.get_channel(1198888931295506534)  # move to config
                if channel:
                    await channel.send(f"@here reminder!! {reminder_message}")
                else:
                    print(f"channel ID not found.")
            else:
                user = self.bot.get_user(user_id)
                if user:
                    try:
                        await user.send(f"reminder!! {reminder_message}")
                    except discord.HTTPException:
                        print(f"failed to send reminder to user {user_id}")
                else:
                    print(f"user with id {user_id} not found.")

            # Delete the reminder after triggering
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM uptime_contexts WHERE id = ?', (reminder_id,))
            conn.commit()
            conn.close()

    @check_reminders.before_loop
    async def before_check_reminders(self):
        await self.bot.wait_until_ready()  # Wait until the bot is ready before checking reminders
