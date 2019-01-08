import re
from urllib.parse import urlparse
from flask import Flask, request, jsonify
import requests
from lxml import etree

HEADERS = {
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36"
}

HEADERS_ANIDUB_PLAYER = {
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36",
}

HEADERS_SIBNET_PLAYER = {
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36",
}

session = requests.session()

app = Flask(__name__)

# def anidubPlayerParseChunks(playlist : str) -> str:
#     response_main = requests.get(playlist, headers=HEADERS).text
#     chunk_file = playlist.replace("playlist.m3u8", response_main.splitlines()[-1])
#     response_chunk = requests.get(chunk_file, headers=HEADERS).text
#     chunk = response_chunk.replace("n_", playlist.replace("playlist.m3u8", "n_"))
#     return chunk

@app.route("/media/content", methods=["GET"])
def getMediaContent():
    media_url = request.args.get("media_url").split("|")[0]
    player_type = urlparse(media_url).netloc
    
    data = []
    if player_type == "www.stormo.tv":

        html = session.get(media_url, headers=HEADERS, allow_redirects=True).text
        quality_urls = re.search('file:"(.*?)",', html).group(1)
        devide_quality_urls = quality_urls.split(",")
        
        if len(devide_quality_urls) == 1:
            data.append({
                "SD" : devide_quality_urls[0]
            })
        else:
            for x in devide_quality_urls:
                current_quality = re.search(r"\[(.*?)\]", x).group(1)
                current_content_url = x.replace(f"[{current_quality}]", "")
                data.append({
                    current_quality : current_content_url
                })

    elif player_type == "anime.anidub.com":

        HEADERS_ANIDUB_PLAYER.update({"Referer" : media_url})
        response_main = requests.get(media_url, headers=HEADERS_ANIDUB_PLAYER, allow_redirects=True).text
        tree = etree.HTML(response_main)
        playlist = tree.xpath('.//video[@id = "hlsvideo"]/source/@src')[0]
        
        data.append({
            "SD" : playlist
        })

    elif player_type == "video.sibnet.ru":

        HEADERS_SIBNET_PLAYER.update({"Referer" : media_url})
        response_main = requests.get(media_url, headers=HEADERS_SIBNET_PLAYER).text
        player_frame = "https://video.sibnet.ru" + re.search(r"src: \"(.*?)\", type:", response_main).group(1)
        player_url = requests.get(player_frame, headers=HEADERS_SIBNET_PLAYER, allow_redirects=False)

        data.append({
            "SD" : player_url.headers["Location"].replace("//", "https://")
        })

    return jsonify(data)

@app.route("/media/episodes/<news_id>", methods=["GET"])
def getMediaEpisodes(news_id):
    html = session.get("http://online.anidub.com/?newsid=" + news_id, headers=HEADERS).text
    tree = etree.HTML(html)
    media_players_row = tree.xpath('.//div[@class="player"]/ul[@class="tabs"]')[0]
    media_player = media_players_row.xpath(".//li/@id")

    data = []
    data_players = []
    stormo_player_titles = []
    stormo_player_episodes = []
    anidub_player_titles = []
    anidub_player_episodes = []
    sibnet_player_titles = []
    sibnet_player_episodes = []
        
    if "ya" in media_player:
        data_players.append("stormo")
        stormo_contents = tree.xpath('.//select[@id = "sel3"]')
        
        for stormo_player in stormo_contents:
            for i in range(0, len(stormo_contents[0])):
                stormo_player_titles.append(stormo_player.xpath('.//option/text()')[i])
                stormo_player_episodes.append(stormo_player.xpath('.//option/@value')[i])

    if "our" in media_player:
        data_players.append("anidub_player")
        anidub_player_contents = tree.xpath('.//select[@id = "sel2"]')
        
        for anidub_player in anidub_player_contents:
            for i in range(0, len(anidub_player_contents[0])):
                anidub_player_titles.append(anidub_player.xpath('.//option/text()')[i])
                anidub_player_episodes.append(anidub_player.xpath('.//option/@value')[i])

    if "vk" in media_player:
        data_players.append("sibnet")
        sibnet_player_contents = tree.xpath('.//select[@id = "sel"]')
        
        for sibnet_player in sibnet_player_contents:
            for i in range(0, len(sibnet_player_contents[0])):
                sibnet_player_titles.append(sibnet_player.xpath('.//option/text()')[i])
                sibnet_player_episodes.append(sibnet_player.xpath('.//option/@value')[i])
    print(anidub_player_titles)
    data.append({
        "players" : data_players,
        
        "episodes" : {
            "title" : stormo_player_titles if stormo_player_titles else anidub_player_titles if anidub_player_titles else sibnet_player if sibnet_player else "",
            "url" : {
                "stormo" if "stormo" in data_players else "" : stormo_player_episodes,
                "anidub_player" if "anidub_player" in data_players else "" : anidub_player_episodes,
                "sibnet" if "sibnet" in data_players else "" : sibnet_player_episodes
            }
        }
    })

    return jsonify(data)


@app.route("/media/list/<page>", methods=["GET"])
def getMediaList(page = 1):
    html = session.get("http://online.anidub.com/page/" + page, headers=HEADERS).text
    tree = etree.HTML(html)
    contents = tree.xpath('.//div[@class = "news_short"]')
    data = []
    for x in contents:
        short_news = etree.tostring(x).decode("utf-8")
        if 'itemprop="year"' in short_news and 'itemprop="genre"' in short_news:
            rating_row = x.xpath('.//b[@itemprop = "ratingValue"]/text()')[0] if 'itemprop="ratingValue"' in short_news else x.xpath('.//div[@class = "rate_view"]/b/text()')[0] if 'class="rate_view"' in short_news else []
            rating = rating_row + " из 100%" if "%" in rating_row else rating_row + " из 5"
            ###########
            title = x.xpath('.//div[@class = "poster_img"]/a/img/@alt')[0].replace("Смотреть аниме ", "").rsplit("/", 1)
            ###########
            year = x.xpath('.//ul[@class = "reset"]/li[1]/span/a/text()')[0]
            genres = ", ".join(x.xpath('.//ul[@class = "reset"]/li[2]/span/a/text()'))
            country = x.xpath('.//ul[@class = "reset"]/li[3]/span/a/text()')[0]
            episodes_row = re.search(r"\[(.*?)\]", title[-1])
            episodes = [] if episodes_row is None else episodes_row.group(1)
            
            description = x.xpath('.//div[@class = "maincont"]/div[@style="display:inline;"]/text()')[0][0:-1]
            news_id = x.xpath('.//div[@class="poster_img"]/a/@href')[0].split('/')[-1].split('-')[0]
            ###########
            
            data.append({
                'title' : title[0],
                'year' : year,
                'poster' : x.xpath('.//div[@class = "poster_img"]/a/img/@data-original')[0],
                'genres' : genres,
                'country' : country,
                'episodes' : episodes,
                'description': description,
                'rating' : rating,
                'newsId' : news_id
            })

    return jsonify(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=False)