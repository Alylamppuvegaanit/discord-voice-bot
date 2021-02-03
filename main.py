import os
import datetime
import asyncio
from enum import Enum

from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
from youtube import getWithSearch, getWithUrl

load_dotenv()

TOKEN = os.getenv('TOKEN')
DIR = os.getcwd()
LOGFILE = os.path.join(DIR, "log.txt")
YT_FILE = "/tmp/audio-from-yt.mp4"

bot = commands.Bot(command_prefix="!")
voiceClient = None

gameStarted = False

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
        log("playSound: no voice channel")
        await ctx.channel.send("No voice channel")
        return
    if not voiceClient.is_connected() or voiceClient.is_playing():
        log("error in playSound")
        await ctx.channel.send("error!")
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
    if voiceClient == None:
        await join(ctx)
    audio = discord.FFmpegPCMAudio(os.path.join(DIR, "seiska.wav"))
    await playSound(ctx, audio)

@bot.command(pass_context=True)
async def play(ctx, *args):
    if VoiceClient == None:
        await join(ctx)
    if not voiceClient.is_connected() or voiceClient.is_playing():
        log("error in playSound")
        await ctx.channel.send("error!")
        return
    if len(args) == 0:
        await ctx.channel.send("No name specified. Quitting...")
        return
    if len(args) == 1 and args[0].startswith("https://www.youtube.com/"):
        await getWithUrl(args[0])
    else:
        search = ' '.join(args)
        await getWithSearch(search)
    if not os.path.isfile(YT_FILE):
        await ctx.channel.send("No name specified. Quitting...")
        return
    audio = discord.FFmpegPCMAudio(YT_FILE)
    await playSound(ctx, audio)

@bot.command(pass_context=True)
async def villapaitapeli(ctx, *args):
    if len(args) != 1:
        log("villapaitapeli: bad arguments")
        return
    cmd = args[0]
    if cmd == "start":
        log("villapaitapeli started")
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "sakarin_villapaitapeli.mp3"))
        await playSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "pue_sakarille_villapaita.mp3"))
        await playSound(ctx, audio)
        global gameStarted
        gameStarted = True
        return
    elif gameStarted and cmd == "joo":
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "hihihi_kutittaa.mp3"))
        await playSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "voitit_pelin.mp3"))
        await playSound(ctx, audio)
        global gameStarted
        gameStarted = False
        return
    elif gameStarted and cmd == "ei":
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "hmm.mp3"))
        await playSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "hävisit_pelin.mp3"))
        await playSound(ctx, audio)
        global gameStarted
        gameStarted = False
        return
    else:
        await ctx.channel.send("wrong command. available commands are: start, joo, ei")
        return
    
    
bot.run(TOKEN)
