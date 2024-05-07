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

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

local_tz = datetime.datetime.now().astimezone().tzinfo
schedule_time = datetime.time(12, tzinfo=local_tz)

wordle_bot = discord.ext.commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=discord.ext.commands.HelpCommand()
    )

@wordle_bot.command()
async def send(ctx: discord.TextChannel, message: str):
    """ Sends a simple String message to the chat.

    Args:
        channel (discord.TextChannel): The channel that this was called from.
        message (str): The message to send to that channel.
    """
    await ctx.send(message)

@wordle_bot.command()
async def wordle(ctx: discord.TextChannel):
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

@discord.ext.tasks.loop(time=schedule_time)
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
    global CTX
    CTX = wordle_bot.get_channel(1237240699624226846)
    await CTX.send(response)


@wordle_bot.command(name="schedule")
async def schedule(ctx, time_str=None, channel_id=None):
    """ Schedule a message in current chat at a specific time

    Args:
        time_str (str): The time to send the message, HH:MM format, must still be today
        channel_id (str | OPTIONAL): The channel ID to send the message to. Default is the current channel.
    Usage:
        schedule <time> <channel_id>
    Example:
        schedule 13:00 0123456789123456789
    """
    # Update the scheduled runtime.
    global schedule_time
    local_tz = datetime.datetime.now().astimezone().tzinfo
    hr, mn = time_str.split(":")
    schedule_time = datetime.time(int(hr), int(mn), tzinfo=local_tz)

    # Update the channel to receive the notification.
    if channel_id is not None:
        global CTX
        CTX = wordle_bot.get_channel(int(channel_id))


    # Relaunch the task with the update time and channel
    # FIXME: This is very finnicky, please help
    if wordle_schedule.is_running():
        wordle_schedule.cancel()
    while wordle_schedule.is_running():
        print("Cancelling old schedule...")
        await asyncio.sleep(1)
    wordle_schedule.start()
    print("Started new schedule!")

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
