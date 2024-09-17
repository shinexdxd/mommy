import discord
from discord.ext import commands, tasks
from datetime import datetime
from core.bot_instance import bot
from core.utilities import db_connection, get_user_id_by_petname, get_petname
from dateutil.relativedelta import relativedelta
import calendar

class Uptime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Command to setuptime
#TODO: ensure reminder uptimes have appropriate values being passed for autoreminder functionality
#TODO: add "relationship" type with petname joins to uptime messages e.g. [foxy] + [puppy] have been [dating] for [duration] / [messagelink]
    @commands.command(name='setuptime', help='reply to a message with setuptime [context] in bot channel or mommy, setuptime [context]')
    async def setuptime(self, ctx, *, context_name: str):
        print("setuptime command called!")
        if not ctx.message.reference:
            await ctx.send("you need to reply to the message you want to set the context for.")
            return

        message_id = ctx.message.reference.message_id
        channel_id = ctx.message.channel.id
        user_id = ctx.author.id  # assuming you want to store the user ID

        print(f"Message ID: {message_id}")
        print(f"Channel ID: {channel_id}")

        # Parse the command input to determine the type
        parts = ctx.message.content.split()
        type = 'uptime'
        if '+remind' in parts:
            type = 'reminder'
            # Truncate the context name to remove the +remind identifier
            context_name = context_name.split('+')[0].strip()  # or use one of the other methods

        conn = db_connection()
        cursor = conn.cursor()

        print("Executing INSERT query...")
        cursor.execute('''
            INSERT INTO uptime_contexts (type, context_name, message_id, channel_id, user_id)
            VALUES (?, ?, ?, ?, ?)
        ''', (type, context_name, message_id, channel_id, user_id))

        conn.commit()
        conn.close()

        # Create a message link using the channel and message IDs
        message_link = f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"
        await ctx.send(f"uptime context '{context_name}' set for [message]({message_link}) with type {type}.")
 
    @commands.command(name='uptime', aliases=['getuptime'], help='call an uptime by context name e.g. dating')
    async def uptime(self, ctx, context_name: str):
        conn = db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT message_id, channel_id FROM uptime_contexts WHERE context_name = ?', (context_name,))
            context = cursor.fetchone()

            if context is None:
                await ctx.send(f"no uptime context found for '{context_name}'.")
                return

            message_id, channel_id = context

            channel = self.bot.get_channel(channel_id)
            if channel is None:
                await ctx.send("channel not found.")
                return

            message = await channel.fetch_message(message_id)
            message_time = message.created_at.replace(tzinfo=None)
            current_time = datetime.utcnow()

            uptime_duration = current_time - message_time

            # Calculate years, months, days, hours, minutes, and seconds
            years, remainder = divmod(uptime_duration.days, 365)
            months, days = divmod(remainder, 30)
            hours, remainder = divmod(uptime_duration.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            # Format the duration
            duration = []
            if years > 0:
                duration.append(f"{years}y")
            if months > 0 or years > 0:
                duration.append(f"{months}m")
            if days > 0 or months > 0 or years > 0:
                duration.append(f"{days}d")
            if hours > 0 or days > 0 or months > 0 or years > 0:
                duration.append(f"{hours}h")
            if minutes > 0 or hours > 0 or days > 0 or months > 0 or years > 0:
                duration.append(f"{minutes}m")
            duration.append(f"{seconds}s")

            duration_str = " ".join(duration)
            message_link = f"https://discord.com/channels/{ctx.guild.id}/{channel_id}/{message_id}"

            await ctx.send(f"{context_name} for {duration_str} / {message_link}")

        except discord.NotFound:
            await ctx.send("message not found.")
        except discord.HTTPException:
            await ctx.send("failed to fetch the message.")
        finally:
            conn.close()

    @commands.command(name='resetuptimes', help='adim usage: reset all uptimes')
    @commands.has_permissions(administrator=True)
    async def reset_uptimes(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM uptime_contexts')
            conn.commit()

            await ctx.send("all uptime contexts have been reset.")
        
        except sqlite3.Error as e:
            await ctx.send(f"an error occurred: {e}")
        
        finally:
            conn.close()

    @commands.command(name='clearuptime', help='admin usage: reset an uptime, use clearuptime [context name]')
    @commands.has_permissions(administrator=True)
    async def clear_uptimes(self, ctx, *, context_name: str):
        conn = db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('DELETE FROM uptime_contexts WHERE context_name = ?', (context_name,))
            conn.commit()

            await ctx.send(f"uptime {context_name} has been cleared.")
        
        except sqlite3.Error as e:
            await ctx.send(f"an error occurred: {e}")
        
        finally:
            conn.close()

    @commands.command(name='updatecontext')
    @commands.has_permissions(administrator=True)
    async def update_context(self, ctx, context_name: str, new_type: str = None, frequency: str = None):
        conn = db_connection()
        cursor = conn.cursor()

        # Check if a new type is provided
        if new_type:
            # Update the context with the new type
            cursor.execute('UPDATE uptime_contexts SET type = ? WHERE context_name = ?', (new_type, context_name))
            conn.commit()  # Commit the changes immediately

            # If the new type is 'remindinguptime', we need to set a reminder_time and target
            if new_type == 'remindinguptime':
                # Fetch the original message timestamp
                cursor.execute('SELECT message_id, channel_id FROM uptime_contexts WHERE context_name = ?', (context_name,))
                context = cursor.fetchone()

                if context:
                    message_id, channel_id = context
                    channel = self.bot.get_channel(channel_id)
                    if channel is not None:
                        message = await channel.fetch_message(message_id)
                        message_time = message.created_at

                        # Process the frequency if provided with a '+' sign
                        if frequency and frequency.startswith('+'):
                            frequency = frequency[1:]  # Strip the '+' sign

                            # Calculate the next reminder_time based on frequency
                            if frequency == 'monthly':
                                # Calculate the first day of the next month
                                next_month = message_time + relativedelta(months=1)
                                next_month_start = next_month.replace(day=1)
                                # Set reminder_time as the start of the next month
                                reminder_time = next_month_start.timestamp()
                            elif frequency == 'annually':
                                # Calculate the same day next year
                                next_year = message_time + relativedelta(years=1)
                                reminder_time = next_year.timestamp()
                            else:
                                await ctx.send("please specify a valid frequency: '+monthly' or '+annually'.")
                                conn.close()
                                return

                            # Update the reminder_time, frequency, and target=1 in the database
                            cursor.execute('UPDATE uptime_contexts SET reminder_time = ?, frequency = ?, target = 1 WHERE context_name = ?', 
                                           (reminder_time, frequency, context_name))
                            conn.commit()  # Commit the changes after setting the reminder_time, frequency, and target

                            await ctx.send(f"context '{context_name}' updated to type '{new_type}' with {frequency} reminders.")
                        else:
                            await ctx.send("please specify a frequency with a '+' sign, such as '+monthly' or '+annually'.")
                            conn.close()
                            return
                    else:
                        await ctx.send("channel not found.")
                else:
                    await ctx.send(f"no context found for '{context_name}'.")
            else:
                await ctx.send(f"context '{context_name}' updated to type '{new_type}'.")

        # If no new type, update the message context
        else:
            if not ctx.message.reference:
                await ctx.send("you need to reply to the message you want to update the context for.")
                return

            new_message_id = ctx.message.reference.message_id
            new_channel_id = ctx.message.channel.id

            cursor.execute('UPDATE uptime_contexts SET message_id = ?, channel_id = ?, target = 1 WHERE context_name = ?', 
                           (new_message_id, new_channel_id, context_name))
            conn.commit()  # Commit changes after updating the message, channel ID, and target

            await ctx.send(f"context '{context_name}' updated to message {new_message_id}.")
        
        conn.close()



    @commands.command(name='listcontexts', aliases=['uptimes', 'viewuptimes', 'getuptimes', 'getalluptimes', 'alluptimes'])
    async def list_contexts(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('SELECT context_name FROM uptime_contexts')
            contexts = cursor.fetchall()

            if not contexts:
                await ctx.send("no uptime contexts found.")
                return

            # Ensure context names are not None
            context_list = "\n".join(context[0] for context in contexts if context[0] is not None)

            if not context_list:
                await ctx.send("no valid uptime contexts found.")
            else:
                await ctx.send(f"uptime contexts: {context_list}")

        except sqlite3.Error as e:
            await ctx.send(f"an error occurred: {e}")

        finally:
            conn.close()


    #tested91124