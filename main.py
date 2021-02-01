import os
import datetime
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
import asyncio


load_dotenv()
TOKEN = os.getenv('TOKEN')

DIR = os.getcwd()
LOGFILE = os.path.join(DIR, "log.txt")

bot = commands.Bot(command_prefix="!")
voiceClient = None

def log(msg):
    if not os.path.isfile(LOGFILE):
        with open(LOGFILE, 'w') as logfile:
            logfile.write(f"{datetime.datetime.today().strftime('[%Y-%m-%d %H:%M]')}: {msg}\n")
            return
    else:
        with open(LOGFILE, 'a') as logfile:
            logfile.write(f"{datetime.datetime.today().strftime('[%Y-%m-%d %H:%M]')}: {msg}\n")

async def disconnect(ctx):
    if VoiceClient != None:
        global voiceClient
        log(f"leaving voice on channel {voiceClient.channel} by {ctx.message.author}")
        await voiceClient.disconnect()
        voiceClient = None
    return

@bot.event
async def on_ready():
    log("Started bot")

@bot.command(pass_context=True)
async def join(ctx):
    author = ctx.message.author
    try:
        channel = author.voice.channel
        if channel == None:
            log("Failed joining voice channel")
            await ctx.channel.send("No voice channel found!")
            return
        global voiceClient
        if voiceClient != None:
            disconnect(ctx)
        voiceClient = await channel.connect()
    except Exception as e:
        log(f"Failed joining voice channel: {e}")
        await ctx.channel.send("No voice channel found!")
        return
    log(f"Joining voice on channel {channel} by {author}")

@bot.command(pass_context=True)
async def leave(ctx):
    await disconnect(ctx)

@bot.command(pass_context=True)
async def seven(ctx):
    if VoiceClient == None:
        await ctx.channel.send("No voice channel")
        return
    if not voiceClient.is_connected() or voiceClient.is_playing():
        await ctx.channel.send("No voice channel")
        return
    audio = discord.FFmpegPCMAudio(os.path.join(DIR, 'seiska.wav'))
    voiceClient.play(audio)

bot.run(TOKEN)