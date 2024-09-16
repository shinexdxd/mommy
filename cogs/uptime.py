import discord
from discord.ext import commands, tasks
from core.utilities import db_connection
from datetime import datetime
from core.bot_instance import bot
from core.utilities import db_connection, get_user_id_by_petname, get_petname

class Uptime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

# Command to setuptime
#TODO: ensure reminder uptimes have appropriate values being passed for autoreminder functionality
#TODO: add "relationship" type with petname joins to uptime messages e.g. [foxy] + [puppy] have been [dating] for [duration] / [messagelink]
    @commands.command(name='setuptime')
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
 
    @commands.command(name='uptime', aliases=['getuptime'])
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

    @commands.command(name='resetuptimes')
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

    @commands.command(name='clearuptime')
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


#TODO: fix this?? or just update fuckups manually - need to add option to remove contexts individually
    # @commands.command(name='updatecontext')
    # @commands.has_permissions(administrator=True)
    # async def update_context(self, ctx, context_name: str, remove_context: str = None):
    #     conn = db_connection()
    #     cursor = conn.cursor()

    #     if remove_context:
    #         cursor.execute('DELETE FROM uptime_contexts WHERE context_name = ?', (remove_context,))
    #         conn.commit()
    #         await ctx.send(f"context'{remove_context}' has been removed.")
    #     else:
    #         if not ctx.message.reference:
    #             await ctx.send("you need to reply to the message you want to update the context for.")
    #             return

    #         new_message_id = ctx.message.reference.message_id
    #         new_channel_id = ctx.message.channel.id

    #         cursor.execute('UPDATE uptime_contexts SET message_id = ?, channel_id = ? WHERE context_name = ?', (new_message_id, new_channel_id, context_name))
    #         conn.commit()

    #         await ctx.send(f"context '{context_name}' updated to message {new_message_id}.")

    #     conn.close()

    @commands.command(name='listcontexts', aliases=['uptimes', 'viewuptimes', 'getuptimes', 'getalluptimes', 'alluptimes'])
    async def list_contexts(self, ctx):
        conn = db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT context_name FROM uptime_contexts')
        contexts = cursor.fetchall()

        if not contexts:
            await ctx.send("no uptime contexts found.")
            conn.close()
            return

        context_list = "\n".join(context[0] for context in contexts)
        await ctx.send(f"Uptime contexts:\n{context_list}")

        conn.close()


    #tested91124