import os
import datetime
import asyncio
from time import sleep

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

bot = commands.Bot(command_prefix="!")
voiceClient = None

gameStarted = False
voiceQueue = []
filenameIndex = 0

# Setup TTS
import multivoice
import soundfile as sf
model, vocoder_model, CONFIG, use_cuda, ap, speaker_fileid, speaker_embedding = multivoice.setup() # Load module
speaker_embedding = multivoice.getSpeaker(26) # Set speaker
gst_style = {"0": 0.1, "1": 0.1, "2": 0, "3": -0.1, "4": -0.2} # Use custom gst style

def log(msg):
    if not os.path.isfile(LOGFILE):
        logfile = open(LOGFILE, 'w')
    else:
        logfile = open(LOGFILE, 'a')
    logfile.write(f"{datetime.datetime.today().strftime('[%Y-%m-%d %H:%M]')}: {msg}\n")
    logfile.close()

async def disconnect(ctx):
    global voiceClient, voiceQueue
    voiceQueue = []
    if VoiceClient != None:
        log(f"leaving voice on channel {voiceClient.channel} by {ctx.message.author}")
        await voiceClient.disconnect()
        voiceClient = None

def playSound(error=""):
    global voiceQueue
    if error != "":
        log(str(error))
    if VoiceClient == None:
        log("playSound: no voice channel")
        return
    if not voiceClient.is_connected():
        log("playSound: no voice channel")
        return
    if len(voiceQueue) == 0:
        log("queue is empty")
        return
    if voiceClient.is_playing():
        log("error: already playing sound")
        return
    log("playing next item from queue")
    voiceClient.play(voiceQueue.pop(0), after=playSound)

async def queueSound(ctx, audio):
    log("adding new audio clip to queue")
    global voiceQueue
    voiceQueue.append(audio)
    if voiceClient == None:
        await join(ctx)
    else:
        if voiceClient.is_playing():
            return
    playSound()

@bot.event
async def on_ready():
    print("[BOT READY]")
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
    log("SEVEN")
    if voiceClient == None:
        await join(ctx)
    audio = discord.FFmpegPCMAudio(os.path.join(DIR, "seiska.wav"))
    await queueSound(ctx, audio)

@bot.command(pass_context=True)
async def play(ctx, *args):
    if VoiceClient == None:
        await join(ctx)
    if len(args) == 0:
        await ctx.channel.send("No name specified. Quitting...")
        return
    global filenameIndex
    filename = f"file-from-yt-{filenameIndex}"
    filenameIndex += 1
    log(f"playing file: {filename}")
    if len(args) == 1 and args[0].startswith("https://www.youtube.com/"):
        await getWithUrl(args[0], filename)
    else:
        search = ' '.join(args)
        await getWithSearch(search, filename)
    if not os.path.isfile(os.path.join("/tmp", filename+".mp4")):
        await ctx.channel.send("error: File not found")
        return
    audio = discord.FFmpegPCMAudio(os.path.join("/tmp", filename+".mp4"))
    await queueSound(ctx, audio)

@bot.command(pass_context=True)
async def skip(ctx):
    if VoiceClient == None or len(voiceQueue) == 0:
        log("unable to skip")
        return
    log("skipping...")
    voiceClient.play(voiceQueue.pop(0), after=playSound)

@bot.command(pass_context=True)
async def villapaitapeli(ctx, *args):
    global gameStarted
    if len(args) != 1:
        log("villapaitapeli: bad arguments")
        await ctx.channel.send("Sakarin villapaitapeli: use argument 'start' to start the game. Use arguments 'joo' or 'ei' to answer the question. This requires the player to be on a voice channel")
        return
    if VoiceClient == None:
        await join(ctx)
    cmd = args[0]
    if cmd == "start":
        log("villapaitapeli: started")
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "sakarin_villapaitapeli.mp3"))
        await queueSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "pue_sakarille_villapaita.mp3"))
        await queueSound(ctx, audio)
        gameStarted = True
        return
    elif gameStarted and cmd == "joo":
        log("villapaitapeli: WIN")
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "hihihi_kutittaa.mp3"))
        await queueSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "voitit_pelin.mp3"))
        await queueSound(ctx, audio)
        gameStarted = False
        return
    elif gameStarted and cmd == "ei":
        log("villapaitapeli: LOSS")
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "hmm.mp3"))
        await queueSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "villapaitapeli", "hävisit_pelin.mp3"))
        await queueSound(ctx, audio)
        gameStarted = False
        return
    else:
        log("villapaitapeli: bad args")
        await ctx.channel.send("wrong command. available commands are: start, joo, ei")
        return

@bot.command(pass_context=True)
async def say(ctx, *args):
    global filenameIndex
    if voiceClient == None:
        await join(ctx)
    if len(args) < 0:
        log("No argument given to say")
        return
    sentence = ' '.join(args)
    log(f"saying {sentence}")
    wav = multivoice.tts(model,
                        vocoder_model,
                        sentence,
                        CONFIG,
                        use_cuda,
                        ap,
                        True,
                        speaker_fileid,
                        speaker_embedding,
                        gst_style=None)
    sf.write(f'/tmp/say_{filenameIndex}.wav', wav, int(22050))
    audio = discord.FFmpegPCMAudio(f'/tmp/say_{filenameIndex}.wav')
    await queueSound(ctx, audio)
    filenameIndex += 1

@bot.command(pass_context=True)
async def setSpeaker(ctx, *args):
    log("changing speaker")
    if len(args) != 1:
        log("No argument given to say")
        return
    try:
        voice = int(args[0])
        if voice > 96 or voice < 0:
            voice = 0
        global speaker_embedding
        speaker_embedding = multivoice.getSpeaker(voice) # Set speaker
        await ctx.channel.send(f"Voice changed to {voice}")
    except:
        print("Bad input")


bot.run(TOKEN)
