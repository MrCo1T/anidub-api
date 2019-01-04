import re
import requests

URL = "https://video.sibnet.ru/shell.php?videoid=3511794"

HEADERS = {
    "Accept" : "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8",
    "Accept-Encoding" : "gzip, deflate, br",
    "Host" : "video.sibnet.ru",
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36",
    "Cookie" : "ampr=2; sib_userid=f8f8592a74bc5cfcedf47b80992671de; advast_user=fdb982a4ec3835024d13502aabe98994"
}


COOKIES = {
    "ampr" : "2",
    "sibuser_id" : "f8f8592a74bc5cfcedf47b80992671de",
    "advast_user" : "fdb982a4ec3835024d13502aabe98994"
}

session = requests.session()

response_main = requests.get(URL, headers=HEADERS)
# session.close
response_html = response_main.text
players_src = re.search('src: "(.*?)", type', response_html)
video_file = f"https://video.sibnet.ru{players_src.group(1)}"
print(video_file)

fh = {
    "Accept" : "*/*",
    "Accept-Encoding" : "identity;q=1, *;q=0",
    "Accept-Language" : "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
    "chrome-proxy" : "frfr",
    "Connection" : "keep-alive",
    "Cookie" : "sib_userid=f8f8592a74bc5cfcedf47b80992671de; advast_user=fdb982a4ec3835024d13502aabe98994",
    "Host" : "video.sibnet.ru",
    "Range" : "bytes=0-",
    "Referer" : "https://video.sibnet.ru/shell.php?videoid=3511794",
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36"
}
response_video_file = requests.get(video_file, headers=fh)
# print(response_video_file.status_code)
# session.close