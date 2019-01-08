import re
import requests
from lxml import etree


URL = "https://anime.anidub.com/player/index.php?vid=/s1/10235/1/1.mp4&url=/anime/full/10245-geymery-gamers-01-iz-12.html"

HEADERS = {
    "Referer" : "https://online.anidub.com/",
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36",
}

def parsePlaylist(dom : str) -> str:
    tree = etree.HTML(dom)
    playlist = tree.xpath('.//video[@id = "hlsvideo"]/source/@src')[0]
    return playlist

def parseChunks(playlist : str) -> str:
    response_main = requests.get(playlist, headers=HEADERS).text
    chunk_file = playlist.replace("playlist.m3u8", response_main.splitlines()[-1])
    response_chunk = requests.get(chunk_file, headers=HEADERS).text
    chunk = response_chunk.replace("n_", playlist.replace("playlist.m3u8", "n_"))
    return chunk

session = requests.session()

response_main = requests.get(URL, headers=HEADERS).text
media_playlist = parsePlaylist(response_main)
media_chunks = parseChunks(media_playlist)
# print(response_main)
print(media_playlist)
print(media_chunks)