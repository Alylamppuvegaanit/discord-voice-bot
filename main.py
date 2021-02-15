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
import synthesizer
import soundfile as sf

model, vocoder_model, speaker_id, CONFIG, use_cuda, ap = synthesizer.setup()

def log(msg):
    if not os.path.isfile(LOGFILE):
        logfile = open(LOGFILE, 'w')
    else:
        logfile = open(LOGFILE, 'a')
    logfile.write(f"{datetime.datetime.today().strftime('[%Y-%m-%d %H:%M]')}: {msg}\n")
    logfile.close()

async def disconnect(ctx):
    voiceQueue = []
    if VoiceClient != None:
        global voiceClient
        log(f"leaving voice on channel {voiceClient.channel} by {ctx.message.author}")
        await voiceClient.disconnect()
        voiceClient = None

def playSound(error=""):
    global voiceQueue
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
    print(args)
    global filenameIndex
    filename = f"file-from-yt-{filenameIndex}"
    filenameIndex += 1
    log(f"playing file: {filename}")
    if VoiceClient == None:
        await join(ctx)
    if len(args) == 0:
        await ctx.channel.send("No name specified. Quitting...")
        return
    if len(args) == 1 and args[0].startswith("https://www.youtube.com/"):
        getWithUrl(args[0], filename)
    else:
        search = ' '.join(args)
        await getWithSearch(search, filename)
    if not os.path.isfile(os.path.join("/tmp", filename+".mp4")):
        await ctx.channel.send("error: File not found")
        return
    audio = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(os.path.join("/tmp", filename+".mp4")))
    audio.volume = 0.3
    await queueSound(ctx, audio)

@bot.command(pass_context=True)
async def playlist(ctx, *args):
    if len(args) == 0:
        with open(os.path.join(DIR, "playlist.txt"), 'r') as infile:
            lines = infile.readlines()
        for line in lines:
            play(ctx, line.replace('\n', ''))
    if len(args) > 0 and args[0] == "add":
        with open(os.path.join(DIR, "playlist.txt"), 'a') as outfile:
            outfile.write(" ".join(args[1:]))

@bot.command(pass_context=True)
async def skip(ctx):
    voiceClient.source = voiceQueue.pop(0)

@bot.command(pass_context=True)
async def stop(ctx):
    global voiceQueue
    voiceQueue = []
    voiceClient.stop()

@bot.command(pass_context=True)
async def pause(ctx):
    voiceClient.pause()

@bot.command(pass_context=True)
async def resume(ctx):
    voiceClient.resume()

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
    print("Say command")
    if len(args) < 0:
        log("No argument given to say")
        return
    sentence = ' '.join(args)
    log(f"saying {sentence}")

    if sentence[-1] != ".":
        sentence += "."
    print("Generating sentence:", sentence)
    align, mel, stops, wav = synthesizer.tts(sentence,
                                            model,
                                            vocoder_model,
                                            speaker_id,
                                            CONFIG,
                                            use_cuda,
                                            ap,
                                            use_gl=False,
                                            figures=True)

    sf.write(f'/tmp/say_{filenameIndex}.wav', wav, int(22050*1.0))
    audio = discord.FFmpegPCMAudio(f'/tmp/say_{filenameIndex}.wav')
    await queueSound(ctx, audio)
    filenameIndex += 1


bot.run(TOKEN)
