import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from dateutil.relativedelta import relativedelta
import re
import os
from core.utilities import db_connection, get_user_id_by_petname, get_petname, special_keywords
import logging
from dotenv import load_dotenv

env_path = os.path.join('config', '.env')
load_dotenv(dotenv_path=env_path)
logging.basicConfig(level=logging.INFO)
REMINDER_CHANNEL_ID = int(os.getenv('REMINDER_CHANNEL'))
BOT_CHANNEL_ID = int(os.getenv('BOT_CHANNEL'))

class Reminders(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.check_reminders.start()  # Start the task loop when the cog is loaded

    def cog_unload(self):
        self.check_reminders.cancel()  # Cancel the task loop when the cog is unloaded

    def get_user_timezone(self, user_id):
        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT timezone FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'utc'  # Default to UTC if no timezone is set

    def get_timezone_offset(self, timezone_str):
        try:
            tz = ZoneInfo(timezone_str)
            now = datetime.now(tz)
            offset = now.utcoffset().total_seconds() / 3600
            return offset
        except Exception as e:
            logging.error(f"error getting timezone offset: {e}")
            return 0

    def parse_datetime_to_unix(self, datetime_str, timezone_str):
        """
        Converts a datetime string (e.g., "2024-09-18 14:00") to a Unix timestamp, with timezone handling.
        """
        try:
            tz = ZoneInfo(timezone_str)
            target_time = datetime.strptime(datetime_str, '%Y-%m-%d %H:%M').replace(tzinfo=tz)
            return int(target_time.timestamp())
        except Exception as e:
            logging.error(f"error parsing datetime '{datetime_str}': {e}")
            raise ValueError("invalid datetime format!")

    def parse_at_time(self, time_str, timezone_str):
        """
        Converts a time string (e.g., "12am", "3:30pm") to a Unix timestamp for today or tomorrow, 
        with timezone handling, applying the timezone offset mathematically.
        """
        try:
            # Get the current time and offset for the specified timezone
            tz = ZoneInfo(timezone_str)
            now = datetime.now(tz)
            offset = self.get_timezone_offset(timezone_str)
            
            # Determine the correct time format based on the input
            if ':' in time_str:
                time_format = '%I:%M%p'
            else:
                time_format = '%I%p'

            # Parse the time string
            parsed_time = datetime.strptime(time_str, time_format)
            
            # Combine the parsed time with today's date in local time
            target_time_local = now.replace(hour=parsed_time.hour, minute=parsed_time.minute, second=0, microsecond=0)

            # If the target time is before now, set for tomorrow
            if target_time_local <= now:
                target_time_local += timedelta(days=1)

            # Adjust target time to UTC by subtracting the offset
            target_time_utc = target_time_local - timedelta(hours=offset)

            # Convert UTC time to Unix timestamp
            return int(target_time_utc.timestamp())

        except Exception as e:
            logging.error(f"error parsing time '{time_str}': {e}")
            raise ValueError("invalid time format!")

    def parse_duration_to_unix(self, duration_str):
        """
        Converts a duration string (e.g., "10m", "1h", "2d", "30s", "3M") into a Unix timestamp.
        """
        if not re.match(r'\d+[a-zA-Z]+', duration_str):
            logging.error(f"invalid duration string: {duration_str}")
            raise ValueError("invalid duration string!")

        try:
            amount = int(re.search(r'\d+', duration_str).group())  # Get the number
            unit = re.search(r'[a-zA-Z]+', duration_str).group()  # Get the unit

            if unit == 's':  # Seconds
                return int((datetime.utcnow() + timedelta(seconds=amount)).timestamp())
            elif unit == 'm':  # Minutes
                return int((datetime.utcnow() + timedelta(minutes=amount)).timestamp())
            elif unit == 'h':  # Hours
                return int((datetime.utcnow() + timedelta(hours=amount)).timestamp())
            elif unit == 'd':  # Days
                return int((datetime.utcnow() + timedelta(days=amount)).timestamp())
            elif unit == 'M':  # Months
                return int((datetime.utcnow() + relativedelta(months=amount)).timestamp())
            elif unit == 'y':  # Years
                return int((datetime.utcnow() + relativedelta(years=amount)).timestamp())
            else:
                raise ValueError("invalid time unit!")
        except Exception as e:
            logging.error(f"error parsing duration '{duration_str}': {e}")
            raise

    @commands.command(name='settimezone', help='set timezone in user database, use string e.g. America/Chicago')
    async def set_timezone(self, ctx, timezone: str):
        try:
            tz = ZoneInfo(timezone)
        except Exception:
            await ctx.send("invalid timezone! please provide a valid timezone string (e.g., 'america/chicago').")
            return

        conn = db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET timezone = ? WHERE user_id = ?', (timezone, ctx.author.id))
        conn.commit()
        conn.close()

        await ctx.send(f"your timezone has been set to {timezone}.")

    @commands.command(name='remind', help='set a reminder, use remind [target] [in/at] [duration/time] [+frequency (optional!)] [label/message]')
    async def remind(self, ctx, *, datetime_label: str):
        logging.info(f"received remind command with input: {datetime_label}")

        # Updated regex pattern to capture the frequency and label after the time string
        pattern = r"^(me|us|we|you|\w+)\s*(in|at)\s*([\d\w:amp]+)\s*(?:\+)?(daily|monthly|annually|weekly)?\s*(.*)$"
        match = re.match(pattern, datetime_label, re.IGNORECASE)

        if not match:
            await ctx.send("invalid format. please use 'in <duration> <message>' or 'at <time> <message>'.")
            return

        target_str = match.group(1).strip()
        time_str = match.group(3).strip()
        frequency = match.group(4)  # Capture the frequency if present
        label = match.group(5).strip()  # Capture the label after the frequency or time

        logging.info(f"parsed target: {target_str}, time: {time_str}, label: {label}, frequency: {frequency}")

        # Fetch user's timezone before time parsing
        try:
            timezone_str = self.get_user_timezone(ctx.author.id)
        except Exception as e:
            await ctx.send(f"error fetching timezone: {e}")
            return

        # Handle target and petname resolution (same as before)
        if target_str in ["me", "us", "we", "you"]:
            target_user_id, mention = special_keywords[target_str](ctx)
            target_user_id = target_user_id or (1 if target_str in ["us", "we"] else ctx.author.id)
            # Ensure the replacement happens only in the target field
            if target_str in ["us", "we"]:
                label = label.replace(target_str, mention or f"<@{target_user_id}>")
            else:
                label = label
        else:
            petname_match = re.search(r"\b(\w+)\b", label)
            if petname_match:
                petname = petname_match.group(1)
                logging.info(f"resolved petname: {petname}")
                target_user_id = get_user_id_by_petname(petname)
                if target_user_id:
                    label = label.replace(petname, f"<@{target_user_id}>")
                else:
                    await ctx.send("error: unable to determine target user id.")
                    return
            else:
                target_user_id = ctx.author.id

        try:
            # Handle 'at' time parsing
            if match.group(2).lower() == 'at':
                if re.match(r'\d{1,2}(:\d{2})?(am|pm)?', time_str):
                    reminder_time = self.parse_at_time(time_str, timezone_str)
                else:
                    reminder_time = self.parse_datetime_to_unix(time_str, timezone_str)
            else:
                reminder_time = self.parse_duration_to_unix(time_str)

            logging.info(f"reminder time (unix): {reminder_time}")
        except ValueError as e:
            await ctx.send(f"error parsing time: {e}")
            return

        current_time_unix = int(datetime.utcnow().timestamp())
        conn = db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO uptime_contexts (type, reminder_message, user_id, target, created_at, reminder_time, frequency) VALUES (?, ?, ?, ?, ?, ?, ?)',
                           ('reminder', label, ctx.author.id, target_user_id, current_time_unix, reminder_time, frequency))
            conn.commit()
            logging.info(f"reminder inserted into database with target {target_user_id}")
        except Exception as e:
            await ctx.send(f"error inserting reminder into database: {e}")
        finally:
            conn.close()

        # Timezone offset for displaying the reminder
        timezone_offset = self.get_timezone_offset(timezone_str)
        reminder_time_utc = datetime.fromtimestamp(reminder_time, tz=ZoneInfo(timezone_str))
        reminder_time_local = reminder_time_utc + timedelta(hours=timezone_offset)
        discord_timestamp = f"<t:{int(reminder_time_local.timestamp())}:R>"

        # Format response
        if target_user_id == 1:
            formatted_response = f"reminder set for {discord_timestamp}: '{label}' (target: @here)"
        else:
            formatted_response = f"reminder set for {discord_timestamp}: '{label}' (target: <@{target_user_id}>)"
        
        if frequency:
            formatted_response += f" - repeats {frequency}"  # Display the frequency

        await ctx.send(formatted_response)


    @tasks.loop(seconds=60.0)
    async def check_reminders(self):
        logging.info("checking for reminders...")
        conn = db_connection()
        cursor = conn.cursor()
        current_time = int(datetime.utcnow().timestamp())

        try:
            cursor.execute('SELECT user_id, reminder_message, target, reminder_time, frequency FROM uptime_contexts WHERE type = "reminder" AND reminder_time <= ?', (current_time,))
            reminders = cursor.fetchall()

            logging.info(f"Found reminders: {reminders}")

            for reminder in reminders:
                user_id, reminder_message, target, reminder_time, frequency = reminder

                # Log each reminder being processed
                logging.info(f"Processing reminder: user_id={user_id}, reminder_message={reminder_message}, target={target}, reminder_time={reminder_time}, frequency={frequency}")

                if target == 1:
                    channel = self.bot.get_channel(REMINDER_CHANNEL_ID)  # Use REMINDER_CHANNEL_ID for @here
                    if not channel:
                        logging.error(f"Channel with ID {REMINDER_CHANNEL_ID} not found.")
                        continue
                    
                    # Include @here tag in the message content
                    message_content = f"@here reminder!! {reminder_message}"
                    await channel.send(message_content)

                else:
                    channel = self.bot.get_channel(BOT_CHANNEL_ID)  # Use BOT_CHANNEL_ID for DM or other notifications
                    if not channel:
                        logging.error(f"channel with ID {BOT_CHANNEL_ID} not found.")
                        continue

                    member = await self.bot.fetch_user(user_id)
                    if member:
                        # Include the frequency only if it exists
                        reminder_text = f"reminder!! {reminder_message}"
                        if frequency:
                            reminder_text += f" - repeats {frequency}"
                        await member.send(reminder_text)
                    else:
                        logging.error(f"user with ID {user_id} not found.")


                # Handle frequency and rescheduling
                if frequency == "daily":
                    new_reminder_time = reminder_time + 86400  # 1 day
                elif frequency == "monthly":
                    new_reminder_time = reminder_time + 2628000  # 1 month (approx)
                elif frequency == "annually":
                    new_reminder_time = reminder_time + 31536000  # 1 year
                elif frequency == "weekly":
                    new_reminder_time = reminder_time + 604800  # 1 week
                else:
                    new_reminder_time = None

                # Log reminder rescheduling or deletion
                if new_reminder_time:
                    logging.info(f"rescheduling reminder to new time: {new_reminder_time}")
                    cursor.execute('UPDATE uptime_contexts SET reminder_time = ? WHERE reminder_message = ?', (new_reminder_time, reminder_message))
                else:
                    logging.info(f"deleting reminder: user_id={user_id}, reminder_message={reminder_message}")
                    cursor.execute('DELETE FROM uptime_contexts WHERE reminder_message = ?', (reminder_message))

                conn.commit()
        except Exception as e:
            logging.error(f"error processing reminders: {e}")
        finally:
            conn.close()


    @commands.command(name='viewreminders', aliases=['reminders', 'getreminders'], help='view an embed listing all reminders')
    async def view_reminders(self, ctx):
        try:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, reminder_message, reminder_time, target, frequency FROM uptime_contexts WHERE type = \'reminder\'')
            reminders = cursor.fetchall()
            conn.close()

            if not reminders:
                await ctx.send("we have no upcoming reminders.")
                return

            embed = discord.Embed(title="✨our reminders✨", color=0x00ff00)
            user_id = ctx.author.id
            timezone_str = self.get_user_timezone(user_id)
            timezone_offset = self.get_timezone_offset(timezone_str)

            for id, reminder_message, reminder_time, target, frequency in reminders:
                reminder_time_local = reminder_time + int(timezone_offset * 3600)
                formatted_time = f"<t:{reminder_time_local}:F>"
                
                if target == 1:
                    target_label = "@here"
                else:
                    target_user = self.bot.get_user(target)
                    if target_user:
                        target_label = target_user.display_name
                    else:
                        target_label = "unknown"

                embed.add_field(name=f"reminder id: {id}", 
                                value=f"time: {formatted_time}\nmessage: {reminder_message}\ntarget: {target_label}\nfrequency: {frequency}", 
                                inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"error fetching reminders: {e}")
            await ctx.send("error retrieving reminders.")

    @commands.command(name='clearreminder', help='clears a reminder by its id')
    async def clear_reminder(self, ctx, reminder_id: int):
        """
        Clears a reminder by its ID.
        """
        conn = db_connection()
        cursor = conn.cursor()

        try:
            # Check if the reminder exists
            cursor.execute('SELECT * FROM uptime_contexts WHERE id = ?', (reminder_id,))
            reminder = cursor.fetchone()

            if reminder:
                # Delete the reminder
                cursor.execute('DELETE FROM uptime_contexts WHERE id = ?', (reminder_id,))
                conn.commit()
                await ctx.send(f"Reminder with ID {reminder_id} has been cleared.")
                logging.info(f"Reminder with ID {reminder_id} cleared by user {ctx.author.id}.")
            else:
                await ctx.send("Error: Reminder not found.")
        except Exception as e:
            await ctx.send(f"Error clearing reminder: {e}")
            logging.error(f"Error clearing reminder with ID {reminder_id}: {e}")
        finally:
            conn.close()


