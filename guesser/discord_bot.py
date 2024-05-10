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
import os

import discord
import discord.ext
import discord.ext.commands
import discord.ext.tasks
import pandas as pd
from dotenv import load_dotenv
from real_player import RealPlayer

# Set Discord intents (these are permissions that determine what the bot is allowed to observe)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

############### SET TIME HERE ###############
LOCAL_TZ = datetime.datetime.now().astimezone().tzinfo
SCH_TM = datetime.time(6, tzinfo=LOCAL_TZ)
BONUS_SCH = [datetime.time(12, tzinfo=LOCAL_TZ), datetime.time(6, tzinfo=LOCAL_TZ)]
#############################################

############ GET ENVIRONMENT VARIABLES ############
RTDIR = os.path.dirname(__file__)

load_dotenv(dotenv_path=f"{RTDIR}/.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
###################################################

# Default Channel to execute Wordle commands in
CTX = None
DF = pd.DataFrame(columns=["Time", "User", "Times Played", "Average Score", "Success Ratio", "Bot Win Ratio", "Guess 1", "Guess 2", "Guess 3", "Guess 4", "Guess 5", "Guess 6"])

# NOTE: I use commands.Bot because it extends features of the Client to allow things like commands
# Initialize Discord Bot
wordle_bot = discord.ext.commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=discord.ext.commands.HelpCommand()
)

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


@wordle_bot.command()
async def play(ctx: discord.ext.commands.context.Context, word: str, mode: int = 0):
    # Read user input

    # Delete user message

    # Send ephemeral message output
    await ctx.send(f"You played {word}! Only you can see this...", mention_author=True, ephemeral=True)

    # Send public message of results
    results = "21012"
    line = results.replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
    await ctx.send(f"{ctx.author.mention} Wordle # | Guess #: {line}")

@wordle_bot.command()
async def stats(ctx: discord.ext.commands.context.Context, user: discord.User=None):
    if user is None:
        user = ctx.author
    await ctx.send(f"Requesting stats for {user.mention}")

@wordle_bot.command()
async def leaderboards(ctx: discord.ext.commands.context.Context, scope: bool=False):
    await ctx.send(f"Requesting leaderboard stats...")

@wordle_bot.command()
async def challenge(ctx: discord.ext.commands.context.Context, user: discord.User):
    await ctx.send(f"{ctx.author.mention} is challenging {user.mention}!")


@discord.ext.tasks.loop(time=SCH_TM)
async def wordle_task():
    """ Play todays Wordle every day at 8am """
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

    for channel in wordle_bot.get_all_channels():
        if channel.name.lower() in ["wordle", "worldle", "nyt"]:
            await channel.send(response)

# @discord.ext.tasks.loop(time=BONUS_SCH)
# async def bonus_wordle_task():
#     """ Play todays Wordle every day at 8am """
#     first = datetime.date(2021, 6, 19)
#     number = (datetime.date.today() - first).days
#     response = f"Wordle {number:,} #\n\n"
#     guess_count = 0

#     cur = datetime.datetime.now(tz=LOCAL_TZ)
#     noon = datetime.datetime.combine(datetime.date.today(), BONUS_SCH[0])
#     eve = datetime.datetime.combine(datetime.date.today(), BONUS_SCH[1])
#     if noon <= cur:
#         nxt = nxt + datetime.timedelta(days=1)

@wordle_bot.event
async def on_ready():
    """ Runs when the DiscordBot has been initialized and is ready """
    # Set the Bot Rich Presence
    await wordle_bot.change_presence(
        activity=discord.Game(name="Today's Wordle")
    )

wordle_bot.run(DISCORD_TOKEN)
