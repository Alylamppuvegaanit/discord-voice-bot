import urllib.request
from requests_html import AsyncHTMLSession
from pytube import YouTube
from bs4 import BeautifulSoup

PATH = "/tmp"
FILENAME = "audio-from-yt"


async def getVideoUrls(searchTerm):
    query = urllib.parse.quote(searchTerm)
    url = "https://www.youtube.com/results?search_query=" + query
    session = AsyncHTMLSession()
    response = await session.get(url)

    # Execute JS
    await response.html.arender(sleep=1)
    
    soup = BeautifulSoup(response.html.html, "html.parser")
    hits = soup.findAll("a", attrs={"id": "video-title"})
    #hits = soup.findAll(attrs={"class:", "yt-simple-endpoint"})
    urls = []
    for vid in hits:
        urls.append('https://www.youtube.com' + vid["href"])
    return urls

def getWithUrl(url):
    # Download audio
    yt = YouTube(url)
    yt.streams.filter(only_audio=True, file_extension='mp4').first().download(output_path=PATH, filename=FILENAME)


async def getWithSearch(searchTerm):
    url = (await getVideoUrls(searchTerm))[0]
    getWithUrl(url)
