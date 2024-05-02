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
"""
import discord

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents,)

@client.event
async def on_ready():
    await client.change_presence(
        activity=discord.Game(name="Today's Wordle")
    )

@client.event
async def on_message(msg: discord.message.Message):
    # Bot shouldn't be responding to itself
    if msg.author == client.user:
        return
    if msg.content.lower() == "hello":
        await msg.channel.send(content="World")
    if "sleep" in msg.content.lower():
        await client.change_presence(
            status=discord.Status.do_not_disturb,
            activity=discord.Game(name="Sleeping...😴")
        )

client.run(TOKEN)
