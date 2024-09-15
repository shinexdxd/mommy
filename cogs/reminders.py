import discord
from discord.ext import commands, tasks
from datetime import datetime, timedelta, timezone
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

    @commands.command(name='settimezone')
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

    @commands.command(name='remind')
    async def remind(self, ctx, *, datetime_label: str):
        logging.info(f"received remind command with input: {datetime_label}")

        pattern = r"^(\w+)\s*(in|at)\s*(\d+[a-zA-Z]+)\s*(.*)"
        match = re.match(pattern, datetime_label)

        if not match:
            await ctx.send("invalid format. please use 'in <duration> <message>' or 'at <time> <message>'.")
            return

        target_str = match.group(1).strip()
        datetime_str = match.group(3).strip()
        label = match.group(4).strip()

        logging.info(f"parsed target: {target_str}, datetime: {datetime_str}, label: {label}")

        if target_str in ["me", "us", "we", "you"]:
            target_user_id, mention = special_keywords[target_str](ctx)
            if target_user_id is None and target_str != "you":
                target_user_id = 1 if target_str in ["us", "we"] else ctx.author.id
            if target_user_id is None:
                await ctx.send("error: unable to determine target user id.")
                return
            label = label.replace(target_str, mention or f"<@{target_user_id}>")
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
            reminder_time = self.parse_duration_to_unix(datetime_str)
            logging.info(f"reminder time (unix): {reminder_time}")
        except ValueError as e:
            await ctx.send(f"error parsing time: {e}")
            return

        current_time_unix = int(datetime.utcnow().timestamp())
        conn = db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('INSERT INTO uptime_contexts (user_id, reminder_time, reminder_message, type, created_at, target) VALUES (?, ?, ?, ?, ?, ?)',
                           (ctx.author.id, reminder_time, label, 'reminder', current_time_unix, target_user_id))
            conn.commit()
            logging.info(f"reminder inserted into database with target {target_user_id}")
        except Exception as e:
            await ctx.send(f"error inserting reminder into database: {e}")
        finally:
            conn.close()

        timezone_str = self.get_user_timezone(ctx.author.id)
        timezone_offset = self.get_timezone_offset(timezone_str)
        reminder_time_utc = datetime.fromtimestamp(reminder_time, timezone.utc)
        reminder_time_local = reminder_time_utc + timedelta(hours=timezone_offset)
        discord_timestamp = f"<t:{int(reminder_time_local.timestamp())}:R>"

        def get_user_mention(user_id):
            return "@here" if user_id == 1 else f"<@{user_id}>"

        await ctx.send(f"reminder set for {discord_timestamp} with label: {label} for {get_user_mention(target_user_id)}.")

    @commands.command(name='viewreminders')
    async def view_reminders(self, ctx):
        try:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT id, reminder_message, reminder_time, target FROM uptime_contexts WHERE type = \'reminder\'')
            reminders = cursor.fetchall()
            conn.close()

            if not reminders:
                await ctx.send("we have no upcoming reminders.")
                return

            embed = discord.Embed(title="✨our reminders✨", color=0x00ff00)
            user_id = ctx.author.id
            timezone_str = self.get_user_timezone(user_id)
            timezone_offset = self.get_timezone_offset(timezone_str)

            for id, reminder_message, reminder_time, target in reminders:
                reminder_time_local = reminder_time + int(timezone_offset * 3600)
                formatted_time = f"<t:{reminder_time_local}:F>"
                
                if target == 1:
                    target_label = "everyone"
                else:
                    target_user = self.bot.get_user(target)
                    if target_user:
                        target_label = target_user.display_name
                    else:
                        target_label = "unknown"

                embed.add_field(name=f"Reminder ID: {id}", value=f"Time: {formatted_time}\nMessage: {reminder_message}\nTarget: {target_label}", inline=False)

            await ctx.send(embed=embed)
        except Exception as e:
            logging.error(f"error fetching reminders: {e}")
            await ctx.send("error retrieving reminders.")

    @commands.command(name='clearreminder')
    async def clear_reminder(self, ctx, reminder_id: int):
        try:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM uptime_contexts WHERE type = \'reminder\' AND id = ?', (reminder_id,))
            conn.commit()
            conn.close()

            if cursor.rowcount > 0:
                await ctx.send(f"reminder with id '{reminder_id}' has been cleared.")
            else:
                await ctx.send("no matching reminder found.")
        except Exception as e:
            logging.error(f"error clearing reminder: {e}")
            await ctx.send("error clearing reminder.")

    @commands.command(name='clearallreminders')
    async def clear_all_reminders(self, ctx):
        try:
            conn = db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM uptime_contexts WHERE type = \'reminder\'')
            conn.commit()
            conn.close()

            if cursor.rowcount > 0:
                await ctx.send(f"reminder with ID '{reminder_id}' has been cleared.")
            else:
                await ctx.send("no matching reminder found.")
        except Exception as e:
            logging.error(f"error clearing reminder: {e}")
            await ctx.send("error clearing reminder.")

    @tasks.loop(minutes=1)
    async def check_reminders(self):
        logging.info("Checking reminders")
        try:
            conn = db_connection()
            cursor = conn.cursor()
            current_time_unix = int(datetime.utcnow().timestamp())
            cursor.execute('SELECT id, user_id, reminder_time, reminder_message, target FROM uptime_contexts WHERE type = \'reminder\' AND reminder_time <= ?', 
                           (current_time_unix,))
            reminders = cursor.fetchall()
            conn.close()

            for reminder_id, user_id, reminder_time, reminder_message, target in reminders:
                if target == 1:
                    # Send to the reminder channel
                    reminder_channel_id = int(os.getenv('REMINDER_CHANNEL'))
                    reminder_channel = self.bot.get_channel(reminder_channel_id)
                    if reminder_channel:
                        await reminder_channel.send(f"reminder for everyone: {reminder_message}")
                else:
                    # Send to the specific user
                    user = self.bot.get_user(target)
                    if user:
                        try:
                            await user.send(f"reminder: {reminder_message}")
                        except discord.Forbidden:
                            logging.error(f"cannot DM user {target}. sending in channel instead.")
                            reminder_channel_id = int(os.getenv('REMINDER_CHANNEL'))
                            reminder_channel = self.bot.get_channel(reminder_channel_id)
                            if reminder_channel:
                                await reminder_channel.send(f"reminder for {user.mention}: {reminder_message}")

                # Remove the reminder from the database
                conn = db_connection()
                cursor = conn.cursor()
                cursor.execute('DELETE FROM uptime_contexts WHERE id = ?', (reminder_id,))
                conn.commit()
                conn.close()

        except Exception as e:
            logging.error(f"error checking reminders: {e}")

