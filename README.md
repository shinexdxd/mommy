mommy

mommy is a discord bot designed for household management within the context of a home server and a light bdsm theme. it features a point system with rewards, tasks, reminders, and relationship/message uptimes.
Bot Setup

    clone the Repository
        clone the bot's repository to your local machine.

    install required packages
        navigate to the bot's directory and install the required packages listed in requirements.txt.

    setup Your .env File
        create a .env file in the bot's directory and include the following environment variables:
            BOT_TOKEN - Your bot token from Discord Developer Portal → Your application → Bot → Token
            BOT_CHANNEL - The channel where you don't need to use the prefix, as well as the bot's "online" message channel.
            REMINDER_CHANNEL - The channel for group reminders, usually the server's main or general channel.

    setup config.json
        See example config.

Run the Bot

    In the terminal, navigate to the bot's directory (mommybot) and run:

        python bot.py

Bot Functionality
Fun

    hello - greet the bot.
    treat? - ask mommy for a treat.

Points

    givepoints - cward a user points. Example: givepoints me/us/petname/@usermention 10 reason
    leaderboard - view the points leaderboard.
    resetpoints - reset points for a specified user e.g. resetpoints petname, resetpoints @user-mention
    viewpoints - get your own points.

Reminders

    clearallreminders - admin usage: Remove all pending reminders.
    clearreminder - clear a specific reminder by ID.
    remind - create a reminder. Example: remind [target] in 10m check laundry, remind [target] at 10pm +daily take pills!
    settimezone - cet a user's timezone. Example: settimezone America/Chicago
    viewreminders - ciew an embed listing all reminders.

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

    clearuptime - clear an uptime from the database. Example: clearuptime dating
    listcontexts - list uptime contexts. (Aliases: uptimes, viewuptimes, getuptimes, getalluptimes, alluptimes)
    resetuptimes - admin usage: Reset all uptime contexts.
    setuptime - reply to a message with setuptime [context name] to set an uptime context. Example: setuptime dating
    uptime - call uptime for a context. example: uptime dating

Memories

    emote react - React to a message to save its content to separate memory channel(s).

Role Reactions

    simple role reaction functionality for consent-channels (see config/config.json for configuration).
