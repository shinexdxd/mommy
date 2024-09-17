mommy

mommy is a discord bot designed for household management within the context of a home server and a light bdsm theme. it features a point system with rewards, tasks, reminders, and relationship/message uptimes.
Bot Setup

    Clone the Repository
        Clone the bot's repository to your local machine.

    Install Required Packages
        Navigate to the bot's directory and install the required packages listed in requirements.txt.

    Setup Your .env File
        Create a .env file in the bot's directory and include the following environment variables:
            BOT_TOKEN - Your bot token from Discord Developer Portal → Your application → Bot → Token
            BOT_CHANNEL - The channel where you don't need to use the prefix, as well as the bot's "online" message channel.
            REMINDER_CHANNEL - The channel for group reminders, usually the server's main or general channel.

    Setup config.json
        See example config.

Run the Bot

    In the terminal, navigate to the bot's directory (mommybot) and run:

    bash

        python bot.py

Bot Functionality
Fun

    hello - Greet the bot.
    treat? - Ask mommy for a treat.

Points

    givepoints - Award a user points. Example: givepoints me/us/petname/@usermention 10 reason
    leaderboard - View the points leaderboard.
    resetpoints - Reset points for a specified user.
    viewpoints - Get your own points.

Reminders

    clearallreminders - Admin usage: Remove all pending reminders.
    clearreminder - Clear a specific reminder by ID.
    remind - Create a reminder. Example: remind me/us/petname/@usermention in 10m check laundry
    settimezone - Set a user's timezone. Example: settimezone America/Chicago
    viewreminders - View an embed listing all reminders.

Rewards

    claimreward - Claim a reward by ID number.
    createreward - Create a reward. Example: createreward rewardname 10 (A dialog will start to determine if the reward is consumable or tags a user.)
    removereward - Remove a reward from the database.
    rewards - View an embed listing all rewards with their IDs.

Tasks

    addtask - Add a task.
    completetask - Complete a task.
    tasks - View an embed listing all tasks.

Uptime

    clearuptime - Clear an uptime from the database. Example: clearuptime dating
    listcontexts - List uptime contexts. (Aliases: uptimes, viewuptimes, getuptimes, getalluptimes, alluptimes)
    resetuptimes - Admin usage: Reset all uptime contexts.
    setuptime - Reply to a message with setuptime [context name] to set an uptime context. Example: setuptime dating
    uptime - Call uptime for a context. Example: uptime dating

Memories

    Emote React - React to a message to save its content to separate memory channel(s).

Role Reactions

    Simple role reaction functionality for consent-channels (see config/config.json for configuration).
