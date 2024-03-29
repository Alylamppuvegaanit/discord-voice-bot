import urllib.request
from requests_html import AsyncHTMLSession
from pytube import YouTube
from bs4 import BeautifulSoup

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

def getWithUrl(url, path, filename):
    # Download audio
    yt = YouTube(url)
    print(yt)
    yt.streams.filter(only_audio=True, file_extension='mp4').first().download(output_path=path, filename=filename)

async def getWithSearch(searchTerm, path, filename="audio-from-yt.mp4"):
    url = (await getVideoUrls(searchTerm))[0]
    getWithUrl(url, path, filename)
