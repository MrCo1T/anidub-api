import re
import requests
from urllib.parse import urlparse

URL = "https://video.sibnet.ru/shell.php?videoid=2869062"

HEADERS = {
    "Referer" : "https://video.sibnet.ru/shell.php?videoid=2869062",
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36",
}

response_main = requests.get(URL, headers=HEADERS, allow_redirects=False).text
player_frame = "https://video.sibnet.ru" + re.search(r'src: "(.*?)", type:', response_main).group(1)
response_main = requests.get(player_frame, headers=HEADERS, allow_redirects=False)
print(response_main.headers["Location"])

# session = requests.Session()
# response_main = requests.get(URL, headers=HEADERS, allow_redirects=False)
# cdn_url = response_main.headers["Location"].replace("//", "https://")
# cdn_headers = HEADERS
# cdn_headers.update(({"Host" : urlparse(cdn_url).netloc}))
# print(HEADERS)
# print(cdn_headers)
# response_main1 = requests.get(cdn_url, headers=cdn_headers, allow_redirects=False)
# print(response_main1.headers)

# response_main1 = requests.get("http:"+response_main.headers["Location"], headers=HEADERS1, allow_redirects=True)
# print(response_main1.url)