""" @file discord_bot.py
    @author Sean Duffie
    @brief Discord bot interface

    Features
    - Automatically posts bot score from each wordle day
    - Allows people to request a new word
        - Users can guess and have results delivered back
        - User's guess is hidden, but results are visible
        - User results are specific to each person
        - Winner per day is recorded
        - Person with the most wins is given a new role

    Commands
        - guess [5 letter word]
        - reset - starts a new wordle game with a random word
        - mode ['nyt', 'rand']
        - schedule - sets the time every day that the wordle should be solved
        - stats [player] - 
"""
import asyncio
import datetime

import discord
import discord.ext
import discord.ext.commands
import discord.ext.tasks
from real_player import RealPlayer

# Set Discord intents (these are permissions that determine what the bot is allowed to observe)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

############### SET TIME HERE ###############
local_tz = datetime.datetime.now().astimezone().tzinfo
SCH_TM = datetime.time(8, tzinfo=local_tz)
#############################################

# Default Channel to execute Wordle commands in
CTX = None


# NOTE: I use commands.Bot because it extends features of the Client to allow things like commands
# Initialize Discord Bot
wordle_bot = discord.ext.commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=discord.ext.commands.HelpCommand()
)

@wordle_bot.command()
async def send(ctx: discord.ext.commands.context.Context, message: str):
    """ Sends a simple String message to the chat.

    Args:
        channel (discord.TextChannel): The channel that this was called from.
        message (str): The message to send to that channel.
    """
    await ctx.send(message)

@wordle_bot.command()
async def wordle(ctx: discord.ext.commands.context.Context):
    """ Play todays Wordle

    Args:
        ctx (discord.TextChannel): The channel that this was called from
    """
    url = "https://www.nytimes.com/games/wordle/index.html"
    first = datetime.date(2021, 6, 19)
    number = (datetime.date.today() - first).days
    response = f"Wordle {number:,} #\n\n"
    guess_count = 0

    with RealPlayer(url) as rp:
        for item in rp.run_generator():
            line = item[1].replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
            response += line + "\n"
            guess_count += 1

        if guess_count > 6:
            guess_count = "x"
        response = response.replace("#", f"{guess_count}/6")

    await ctx.send(response)

@discord.ext.tasks.loop(time=SCH_TM)
async def wordle_schedule():
    """ Play todays Wordle

    Args:
        ctx (discord.TextChannel): The channel that this was called from
    """
    url = "https://www.nytimes.com/games/wordle/index.html"
    first = datetime.date(2021, 6, 19)
    number = (datetime.date.today() - first).days
    response = f"Wordle {number:,} #\n\n"
    guess_count = 0

    with RealPlayer(url) as rp:
        for item in rp.run_generator():
            line = item[1].replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
            response += line + "\n"
            guess_count += 1

        if guess_count > 6:
            guess_count = "x"
        response = response.replace("#", f"{guess_count}/6")

    # TODO: Make this more sophisticated, it should be flexible and not hardcoded
    await CTX.send(response)


@wordle_bot.command(name="schedule")
async def schedule(ctx: discord.ext.commands.context.Context,
                   time_str: str=None):
    """ Schedule a message in current chat at a specific time

    Args:
        time_str (str): The time to send the message, HH:MM format, must still be today
        channel_id (str | OPTIONAL): The channel ID to send the message to. Default is the current channel.
    Usage:
        schedule <time> <channel_id>
    Example:
        schedule 13:00 0123456789123456789
    """
    # Parse the time string input
    hr, mn = time_str.split(":")

    # Update the scheduled runtime.
    global SCH_TM
    SCH_TM = datetime.time(int(hr), int(mn), tzinfo=local_tz)

    # Update the channel to receive the notification.
    global CTX
    CTX = ctx


    # Relaunch the task with the update time and channel
    # FIXME: This is very finnicky, please help
    if wordle_schedule.is_running():
        wordle_schedule.cancel()
    while wordle_schedule.is_running():
        print("Cancelling old schedule...")
        await asyncio.sleep(1)
        await ctx.send("Cancelling old schedule...")
    wordle_schedule.start()
    print("Started new schedule!")
    await ctx.send(f"Starting new schedule at {SCH_TM}")

    cur = datetime.datetime.now(tz=local_tz)
    nxt = datetime.datetime.combine(datetime.date.today(), SCH_TM)
    if nxt < cur:
        nxt = nxt + datetime.timedelta(days=1)

    await ctx.send(f"Next message in {nxt - cur}")

@wordle_bot.event
async def on_ready():
    """ Runs when the DiscordBot has been initialized and is ready """
    # Start the wordle schedule automatically
    if not wordle_schedule.is_running():
        wordle_schedule.start()
    # Set the Bot Rich Presence
    await wordle_bot.change_presence(
        activity=discord.Game(name="Today's Wordle")
    )

wordle_bot.run(TOKEN)
