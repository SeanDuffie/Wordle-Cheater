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
from apscheduler.schedulers.asyncio import AsyncIOScheduler

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = discord.ext.commands.Bot(command_prefix="!", intents=intents,)


@bot.event
async def on_ready():
    """_summary_
    """
    await bot.change_presence(
        activity=discord.Game(name="Today's Wordle")
    )

@bot.command()
async def send(ctx, message):
    """_summary_

    Args:
        channel (_type_): _description_
        message (_type_): _description_
    """
    await ctx.send(message)

@bot.command()
async def hello(ctx):
    """_summary_

    Args:
        channel (_type_): _description_
        message (_type_): _description_
    """
    await ctx.send("Hello World")

@bot.group()
async def cool(ctx):
    """Says if a user is cool.

    In reality this just checks if a subcommand is being invoked.
    """
    if ctx.invoked_subcommand is None:
        await ctx.send(f'No, {ctx.subcommand_passed} is not cool')


@cool.command(name='bot')
async def _bot(ctx):
    """Is the bot cool?"""
    await ctx.send('Yes, the bot is cool.')

@bot.command(name="schedule")
# @discord.ext.commands.has_any_role("MODS", "ADMIN")
async def schedule(ctx, time_str, date_str=None, channel_id=None):
    """
    Schedule a message in current chat at a specific time
    @:param time_str: The time to send the message, HH:MM format, must still be today
    @:param message: Must be in quotation marks, the message you want to send
    Usage:
    -schedule <time> "<message>"
    Example:
    -schedule 16:00 "Hello there :)"
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

    # Schedule the message
    scheduler = AsyncIOScheduler()
    scheduler.add_job(send, 'date', run_date=run_time, args=[channel, message])
    scheduler.start()

    # Confirm
    print(f"Scheduled a message at {run_time} in channel {channel}: {message}")
    await ctx.channel.send(f"All set, message wil be sent in {delay / 60:.2f} minutes (unless this bot crashes in meantime)!")

bot.run(TOKEN)