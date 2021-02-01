import os
import datetime
from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
import asyncio
from youtube import getWithSearch

load_dotenv()

TOKEN = os.getenv('TOKEN')
DIR = os.getcwd()
LOGFILE = os.path.join(DIR, "log.txt")

bot = commands.Bot(command_prefix="!")
voiceClient = None

def log(msg):
    if not os.path.isfile(LOGFILE):
        logfile = open(LOGFILE, 'w')
    else:
        logfile = open(LOGFILE, 'a')
    logfile.write(f"{datetime.datetime.today().strftime('[%Y-%m-%d %H:%M]')}: {msg}\n")
    logfile.close()

async def disconnect(ctx):
    if VoiceClient != None:
        global voiceClient
        log(f"leaving voice on channel {voiceClient.channel} by {ctx.message.author}")
        await voiceClient.disconnect()
        voiceClient = None
    return

async def playSound(ctx, audio):
    if VoiceClient == None:
        await ctx.channel.send("No voice channel")
        return
    if not voiceClient.is_connected() or voiceClient.is_playing():
        await ctx.channel.send("No voice channel")
        return
    voiceClient.play(audio)

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
    
    playSound(ctx, audio)
    
@bot.command(pass_context=True)
async def play(ctx, *args):
    if len(args) == 0:
        await ctx.channel.send("No name specified. Quitting...")
        return
    search = ' '.join(args)
    getWithSearch(search)
    audio = discord.FFmpegPCMAudio("/tmp/audio-from-yt")
    playSound(ctx, audio)

bot.run(TOKEN)