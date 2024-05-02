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

client = discord.Client()

@client.event
async def on_ready():
    print("The bot is ready!")
    await client.change_presence(game=discord.Game(name="Crushing today's Wordle"))

@client.event
async def on_message(message):
    # Bot shouldn't be responding to itself
    if message.author == client.user:
        return
    if message.content == "Hello":
        await client.send_message(message.channel, "World")

client.run(TOKEN)
