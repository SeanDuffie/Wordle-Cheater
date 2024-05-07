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
import datetime

import discord
import discord.ext
import discord.ext.commands
import discord.ext.tasks
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from real_player import RealPlayer

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.ext.commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=discord.ext.commands.HelpCommand()
    )


@bot.event
async def on_ready():
    """_summary_
    """
    await bot.change_presence(
        activity=discord.Game(name="Today's Wordle")
    )

@bot.command()
async def send(ctx: discord.TextChannel, message: str):
    """ Sends a simple String message to the chat.

    Args:
        channel (discord.TextChannel): The channel that this was called from.
        message (str): The message to send to that channel.
    """
    await ctx.send(message)

@bot.command()
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



@bot.command(name="schedule")
async def schedule(ctx, time_str, date_str=None, channel_id=None):
    """ Schedule a message in current chat at a specific time

    Args:
        time_str (str): The time to send the message, HH:MM format, must still be today
        date_str (str): Date to send the first message. Must be in the future
        channel_id (str | OPTIONAL): The channel ID to send the message to. Default is the current channel.
    Usage:
        schedule <time>
    Example:
        schedule 16:00
    """

    # Get the date
    if date_str is None:
        date = datetime.datetime.now()
    else:
        date = datetime.datetime.strptime(date_str, "%d/%m/%Y")

    run_time = datetime.datetime.strptime(time_str, '%H:%M').replace(year=date.year, month=date.month, day=date.day)

    # Check if it's in the future
    now = datetime.datetime.now()
    delay = (run_time - now).total_seconds()
    assert delay > 0

    # Get the channel
    if channel_id is not None:
        channel = bot.get_channel(int(channel_id))
    else:
        channel = ctx.channel
    assert channel is not None

    # # Schedule the message
    # scheduler = AsyncIOScheduler()
    # scheduler.add_job(wordle, 'date', run_date=run_time, args=[channel])
    # scheduler.start()

    # # Confirm
    # print(f"Will post the Wordle results at {run_time} in channel {channel}")
    await ctx.channel.send(f"All set, Wordle results will be posted in {delay/60}{delay%60} minutes (unless this bot crashes in meantime)!")

bot.run(TOKEN)