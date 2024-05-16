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
import random
from typing import Dict, List, Tuple

import discord
import discord.ext
import discord.ext.commands
import discord.ext.tasks
import pandas as pd
from dotenv import load_dotenv
from real_player import RealPlayer
from word_bank import WordBank
from tester import Tester

# Set Discord intents (these are permissions that determine what the bot is allowed to observe)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

############### SET TIME HERE ###############
LOCAL_TZ = datetime.datetime.now().astimezone().tzinfo
TIMES = [
    datetime.time(6, tzinfo=LOCAL_TZ),
    datetime.time(12, tzinfo=LOCAL_TZ),
    datetime.time(18, tzinfo=LOCAL_TZ),
    datetime.time(0, tzinfo=LOCAL_TZ)
]

FIRST_WORDLE = datetime.date(2021, 6, 19)
WORDLE_NUMBER = (datetime.date.today() - FIRST_WORDLE).days
#############################################

############ GET ENVIRONMENT VARIABLES ############
RTDIR = os.path.dirname(__file__)

load_dotenv(dotenv_path=f"{RTDIR}/.env")
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
###################################################

# Default Channel to execute Wordle commands in
CTX = None
DF = pd.DataFrame(columns=["Time", "User", "Times Played", "Average Score", "Success Ratio", "Bot Win Ratio", "Guess 1", "Guess 2", "Guess 3", "Guess 4", "Guess 5", "Guess 6"])
history: Dict[discord.User, List[Tuple[str, str]]] = {}
solutions: List[str] = ["", "", ""]

# NOTE: I use commands.Bot because it extends features of the Client to allow things like commands
# Initialize Discord Bot
wordle_bot = discord.ext.commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=discord.ext.commands.HelpCommand()
)


def check(guess: str, solution: str) -> str:
    """ Generates a 'results' string from a guess when the solution is known

    Args:
        guess (str): the user or system generated guess
        solution (str): the known solution to the current puzzel iteration

    Returns:
        str: Formatted results string that compares the solution with the guess
    """
    result = "00000"

    # First, eliminate all letters known to be correct, mask the correct letters with whitespace
    for i in range(5):
        if guess[i] == solution[i]:
            result = result[:i] + "2" + result[i+1:]
            guess = guess[:i] + " " + guess[i+1:]
            solution = solution[:i] + " " + solution[i+1:]
        # print(f"{guess=} | {solution=} | {result=}")

    # Next, identify all the characters that are present but not in the correct spot
    # Doing it this way allows you to identify duplicate letters without looping on confirmed
    # Additionally, only one "possible" duplicate letter should be marked for each duplicate
    for i in range(5):
        if guess[i] != " " and guess[i] in solution:
            result = result[:i] + "1" + result[i+1:]

            # Replace the character in solution with whitespace to handle duplicates
            j = solution.index(guess[i])
            solution = solution[:j] + " " + solution[j+1:]
        # print(f"{guess=} | {solution=} | {result=}")

    return result

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

    # while True:
    #     try:
    with RealPlayer(url) as rp:
        for item in rp.run_generator():
            line = item[1].replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
            response += line + "\n"
            guess_count += 1

            if item[1] == "22222" or item[1].isalpha():
                solutions[0] = item[0]
                print(solutions)

        if guess_count > 6:
            guess_count = "x"
        response = response.replace("#", f"{guess_count}/6")
        #     break
        # except:
        #     pass

    await ctx.send(response)


@wordle_bot.command()
async def play(ctx: discord.ext.commands.context.Context, word: str, mode: int = 0):
    # # If the solution is not populated, it must be generated or retrieved
    if solutions[mode] == "":
        match mode:
            case 0:
                wordle(ctx)
            case _:
                wb = WordBank()
                solutions[mode] = wb.get_rand()

    # Check message for errors
    try:
        assert word.isalpha()
        assert len(word) == 5
    except AssertionError:
        await ctx.reply("Invalid Guess")
        return

    # Check mode for errors
    try:
        assert mode >= 0
        assert mode <= 3
    except AssertionError:
        await ctx.reply("Invalid Mode")
        return

    # If the user hasn't guessed today, assign them a spot
    if ctx.author not in history:
        history[ctx.author] = []

    # Check if the user has exceeded their guess count for the day
    if len(history[ctx.author]) >= 6:
        try:
            await ctx.reply("You've exceeded your maximum guesses :(")
        except discord.errors.HTTPException:
            await ctx.send(f"{ctx.author.mention} exceeded their maximum guesses :(", ephemeral=True)
        return

    # Send ephemeral message output of guess
    try:
        await ctx.reply(f"You played {word}! Only you can see this...", ephemeral=True)
    except discord.errors.HTTPException:
        await ctx.send(f"{ctx.author.mention} played {word}! Only you can see this...", ephemeral=True)

    # Send public message of results
    result = check(guess=word, solution=solutions[mode])
    result = result.replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
    history[ctx.author].append((word, result))
    await ctx.send(f"{ctx.author.mention} Wordle {WORDLE_NUMBER} | Guess {len(history[ctx.author])}: {result}")

    # Delete user message
    await ctx.message.delete()

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


@discord.ext.tasks.loop(time=TIMES[0])
async def wordle_task():
    """ Play todays Wordle every day at 8am """
    url = "https://www.nytimes.com/games/wordle/index.html"
    response = f"Wordle {WORDLE_NUMBER:,} #\n\n"
    guess_count = 0

    with RealPlayer(url) as rp:
        for item in rp.run_generator():
            line = item[1].replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
            response += line + "\n"
            guess_count += 1

            if item[1] == "22222" or item[1].isalpha():
                solutions[0] = item[0]

        if guess_count > 6:
            guess_count = "x"
        response = response.replace("#", f"{guess_count}/6")

    for channel in wordle_bot.get_all_channels():
        if channel.name.lower() in ["wordle", "worldle", "nyt"]:
            await channel.send(response)

@discord.ext.tasks.loop(time=TIMES[1])
async def wordle_noon():
    """ Resets the Noon Wordle at 12pm every day """
    response = f"Wordle {WORDLE_NUMBER:,} #\n\n"
    guess_count = 0

    wb = WordBank()
    solutions[1] = wb.get_rand()

    tester = 
    # FIXME: Update with Tester Generator for simulated solutions
    # with RealPlayer(url) as rp:
    #     for item in rp.run_generator():
    #         line = item[1].replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
    #         response += line + "\n"
    #         guess_count += 1

    #     if guess_count > 6:
    #         guess_count = "x"
    #     response = response.replace("#", f"{guess_count}/6")

    for channel in wordle_bot.get_all_channels():
        if channel.name.lower() in ["wordle", "worldle", "nyt"]:
            await channel.send("New Afternoon Wordle Available!")
            await channel.send(response)

@discord.ext.tasks.loop(time=TIMES[2])
async def wordle_evening():
    """ Resets the evening Wordle at 6pm every day """
    response = f"Wordle {WORDLE_NUMBER:,} #\n\n"
    guess_count = 0

    wb = WordBank()
    solutions[2] = wb.get_rand()

    # FIXME: Update with Tester Generator for simulated solutions
    # with RealPlayer(url) as rp:
    #     for item in rp.run_generator():
    #         line = item[1].replace("2", ":green_square:").replace("1", ":yellow_square:").replace("0", ":black_large_square:")
    #         response += line + "\n"
    #         guess_count += 1

    #     if guess_count > 6:
    #         guess_count = "x"
    #     response = response.replace("#", f"{guess_count}/6")

    for channel in wordle_bot.get_all_channels():
        if channel.name.lower() in ["wordle", "worldle", "nyt"]:
            await channel.send("New Evening Wordle Available!")
            await channel.send(response)

@discord.ext.tasks.loop(time=TIMES[3])
async def reset():
    """ Resets everything at midnight """
    global WORDLE_NUMBER
    WORDLE_NUMBER = (datetime.date.today() - FIRST_WORDLE).days

    for channel in wordle_bot.get_all_channels():
        if channel.name.lower() in ["wordle", "worldle", "nyt"]:
            await channel.send(f"Resetting the Wordle for Day {WORDLE_NUMBER:,}")

    global history
    history = {}

@wordle_bot.event
async def on_ready():
    """ Runs when the DiscordBot has been initialized and is ready """
    # Start the wordle schedule automatically
    if not wordle_task.is_running():
        wordle_task.start()
    if not wordle_noon.is_running():
        wordle_noon.start()
    if not wordle_evening.is_running():
        wordle_evening.start()
    # Set the Bot Rich Presence
    await wordle_bot.change_presence(
        activity=discord.Game(name="Today's Wordle")
    )

wordle_bot.run(DISCORD_TOKEN)
