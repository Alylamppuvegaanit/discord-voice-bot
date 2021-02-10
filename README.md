# discord-voice-bot

This is a simple discord voice bot with main focus on text-to-speech and youtube integration

INSTALLATION:
install python dependencies with command
`pip install -r requirements.txt`

OTHER DEPENDENCIES:

- FFMPEG is required for audio playback. On ubuntu/debian, it can be installed with `sudo apt install ffmpeg`. For other operating systems and package managers, see [https://ffmpeg.org/](https://ffmpeg.org/)

- Chromium is required for youtube integration. On ubuntu/debian, it can be installed with `sudo apt install chromium`


Text to speech package is installed by running script `setup_multivoice.sh`.

The program also needs to be supplied a valid discord bot token, which should be stored in a file called .env, specidfied by a line `TOKEN=...`
