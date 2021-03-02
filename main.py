import os
import datetime
import asyncio
from time import sleep
import random
import json

from dotenv import load_dotenv
import discord
from discord.ext import commands
from discord.ext.commands import Bot
from discord.voice_client import VoiceClient
from youtube import getWithSearch, getWithUrl

load_dotenv()

PLAYLISTFILE = "/home/roope/dev/discord-voice-bot-web/data/playlists.json"
TOKEN = os.getenv('TOKEN')
DIR = os.getcwd()
LOGFILE = os.path.join(DIR, "log.txt")


bot = commands.Bot(command_prefix="!")

voiceClient = None
gameStarted = False
repeatFile = ""
repCount = 0
playList = []
voiceQueue = []
filenameIndex = 0
TASKS = []
CTX = None # This is spaghetti required to make things work, don't delete :-)

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

def reset():
    global voiceQueue, playList, repeatFile
    repeatFile = ""
    voiceQueue = []
    playList = []

def checkVoiceClient():
    if VoiceClient == None or str(type(voiceClient)) != "<class 'discord.voice_client.VoiceClient'>":
        return False
    if not voiceClient.is_connected():
        return False
    return True

def playSound(error=""):
    global voiceQueue, playList, CTX, TASKS
    try:
        if error != "":
            print(f"error: {str(error)}")
            log(str(error))
        if not checkVoiceClient():
            print("playSound: checkVoiceClient failed")
            return
        while len(voiceQueue) < 3 and len(playList) > 0:
            print(f"playSound: adding {playList[0]} to queue")
            playWithUrl(playList.pop(0))
        if len(voiceQueue) == 0:
            print("queue is empty")
            log("queue is empty")
            return
        if voiceClient.is_playing():
            print("voiceClient already playing")
            return
    except Exception as e:
        log(str(e))
        print(f"playSound: error '{str(e)}'")
        return
    print("playing next item from queue")
    voiceClient.play(voiceQueue.pop(0), after=playSound)

def repeat(error=""):
    global voiceQueue, CTX
    try:
        if error != "":
            log(str(error))
        if not checkVoiceClient():
            return
        if voiceClient.is_playing():
            log("error: already playing sound")
            return
        if repeatFile == "":
            print("no repeatfile, stopping")
            log("stopped repeating")
            return
        audio = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(repeatFile))
        audio.volume = 0.3
    except Exception as e:
        print(e)
        log(str(e))
        return
    voiceClient.play(audio, after=repeat)

async def disconnect(ctx):
    reset()
    if VoiceClient != None:
        global voiceClient
        if checkVoiceClient():
            await voiceClient.disconnect()
        voiceClient = None

async def queueSound(ctx, audio):
    log("adding new audio clip to queue")
    global voiceQueue
    print("adding to queue")
    voiceQueue.append(audio)
    if voiceClient == None:
        await join(ctx)
    playSound()

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
        if checkVoiceClient():
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
async def play(ctx, *args):
    global TASKS
    rep = False
    while len(TASKS) != 0:
        try:
            await TASKS[0]
        except:
            break
        TASKS.pop(0)
    if VoiceClient == None:
        await join(ctx)
    if len(args) == 0:
        print("no args")
        await ctx.channel.send("No name specified. Quitting...")
        return
    if args[0] == "-r":
        rep = True
    if args[-1].startswith("https://www.youtube.com/"):
        playWithUrl(args[-1], rep)
    else:
        if rep:
            search = ' '.join(args[1:])
        else:
            search = ' '.join(args)
        await playWithName(ctx, search, rep)

def playWithUrl(url, rep=False):
    global filenameIndex, voiceQueue, repeatFile
    filename = f"file-from-yt-{filenameIndex}"
    filenameIndex += 1
    print(f"getWithUrl({url}, {filename})")
    try:
        getWithUrl(url, filename)
    except:
        print("bad video url")
        return
    audioFile = os.path.join("/tmp", filename+".mp4")
    if not os.path.isfile(audioFile):
        print(f"file not found: {audioFile}")
        log(f"file not found: {audioFile}")
        return
    if rep:
        print("playWithUrl: repeat")
        repeatFile = audioFile
        repeat()
    else:
        audio = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audioFile))
        audio.volume = 0.3
        log("adding new audio clip to queue") 
        voiceQueue.append(audio)
        playSound()

async def playWithName(ctx, search, rep=False):
    global filenameIndex, voiceQueue, repeatFile
    filename = f"file-from-yt-{filenameIndex}"
    filenameIndex += 1
    print(f"getWithSearch({search}, {filename})")
    await getWithSearch(search, filename)
    audioFile = os.path.join("/tmp", filename+".mp4")
    if not os.path.isfile(audioFile):
        log(f"file not found: {audioFile}")
        await ctx.channel.send("error: File not found")
        return
    if rep:
        await stop(ctx)
        if voiceClient == None:
            await join(ctx)
        global repeatFile
        repeatFile = audioFile
        repeat()
    else:
        audio = discord.PCMVolumeTransformer(discord.FFmpegPCMAudio(audioFile))
        audio.volume = 0.3
        await queueSound(ctx, audio)

@bot.command(pass_context=True)
async def playlist(ctx, *args):
    global CTX, playList
    CTX = ctx
    name = ""
    shuffle = False
    if len(args) == 0:
        print("playlist: no args")
        await ctx.channel.send("no arguments given. valid arguments: play, add")
        return
    if args[0] == "-s":
        print("shuffle enabled")
        shuffle = True
        name = ' '.join(args[1:])
    else:
        name = ' '.join(args[0:])
    print(f"playlist {name}")
    with open(PLAYLISTFILE, 'r') as infile:
        data = infile.read()
    data = json.loads(data)
    for a in data:
        if a['id'] == name:
            for b in a['songs']:
                playList.append(b['title'])
    if playList == []:
        print("playlist not found")
        await ctx.channel.send(f"playlist '{name}' not found, empty playlist")
        return
    if shuffle:
        random.shuffle(playList)
    if voiceClient == None:
        await join(ctx)
    playSound()

@bot.command(pass_context=True)
async def skip(ctx):
    global voiceQueue, playList, repeatFile
    if voiceClient == None:
        return
    repeatFile = ""
    if len(voiceQueue) < 3 and len(playList) > 0:
        await play(ctx, playList.pop(0))
    if len(voiceQueue) == 0:
        if len(playList) == 0:
            await ctx.channel.send("Queue is empty")
            return
    voiceClient.source = voiceQueue.pop(0)

@bot.command(pass_context=True)
async def stop(ctx):
    reset()
    if voiceClient != None:
        voiceClient.stop()

@bot.command(pass_context=True)
async def pause(ctx):
    if voiceClient != None:
        voiceClient.pause()

@bot.command(pass_context=True)
async def resume(ctx):
    if voiceClient != None:
        voiceClient.resume()

@bot.command(pass_context=True)
async def villapaitapeli(ctx, *args):
    global gameStarted
    if len(args) != 1:
        await ctx.channel.send("Sakarin villapaitapeli: use argument 'start' to start the game. Use arguments 'joo' or 'ei' to answer the question. This requires the player to be on a voice channel")
        return
    if VoiceClient == None:
        await join(ctx)
    cmd = args[0]
    if cmd == "start":
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "data", "villapaitapeli", "sakarin_villapaitapeli.mp3"))
        await queueSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "data", "villapaitapeli", "pue_sakarille_villapaita.mp3"))
        await queueSound(ctx, audio)
        gameStarted = True
        return
    elif gameStarted and cmd == "joo":
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "data", "villapaitapeli", "hihihi_kutittaa.mp3"))
        await queueSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "data", "villapaitapeli", "voitit_pelin.mp3"))
        await queueSound(ctx, audio)
        gameStarted = False
        return
    elif gameStarted and cmd == "ei":
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "data", "villapaitapeli", "hmm.mp3"))
        await queueSound(ctx, audio)
        audio = discord.FFmpegPCMAudio(os.path.join(DIR, "data", "villapaitapeli", "hävisit_pelin.mp3"))
        await queueSound(ctx, audio)
        gameStarted = False
        return
    else:
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
    log(f"Generating sentence: {sentence}")
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

@bot.command(pass_context=True)
async def seven(ctx):
    log("SEVEN")
    if voiceClient == None:
        await join(ctx)
    audio = discord.FFmpegPCMAudio(os.path.join(DIR, "data", "seiska.wav"))
    await queueSound(ctx, audio)

@bot.event
async def on_ready():
    print("[BOT READY]")
    log("Started bot")

class helpCommand(commands.MinimalHelpCommand):
    async def send_pages(self):
        destination = self.get_destination()
        with open(os.path.join(DIR, "help.txt"), 'r') as infile:
            text = "```\n" + infile.read() + "\n```"
        await destination.send(text)

bot.help_command = helpCommand()

bot.run(TOKEN)
