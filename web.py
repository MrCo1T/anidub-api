# coding=utf-8

import re
import requests
import rapidjson
from lxml import etree
from flask import Flask
from flask import abort
from flask import request
from flask import jsonify
from flask import Response
from urllib.parse import quote
from urllib.parse import urlparse
from flask import stream_with_context

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

@app.route("/anime/preview", methods=["GET"])
def whatsAnimePreview():
    resp = requests.get(f"https://trace.moe/preview.php?anilist_id={request.args.get('id')}&file={quote(request.args.get('file'))}&t={request.args.get('t')}&token={request.args.get('token')}", headers=HEADERS, stream=True)
    return Response(stream_with_context(resp.iter_content()), content_type = resp.headers['Content-Type'])

@app.route("/anime/find", methods=["POST"])
def whatsAnimeFromScreenshot():
    data = []
    image = request.form.get("image")
    response = session.post("https://trace.moe/api/search?token=4ad4c15520f90753d4f4d88f970323c5641cd9bb", headers=HEADERS, data={"image" : image}).text
    json_result = rapidjson.loads(response)

    anilist_id = json_result["docs"][0]["anilist_id"]
    filename = json_result["docs"][0]["filename"]
    prev_at = json_result["docs"][0]["at"]
    prev_to = json_result["docs"][0]["to"]
    tokenthumb = json_result["docs"][0]["tokenthumb"]
    preview = f"http://anidub.mrcolt.ru/anime/preview?id={anilist_id}&file={quote(filename)}&t={prev_at}&token={tokenthumb}"
    similarity_row = str(json_result["docs"][0]["similarity"])
    if "0." in similarity_row:
        similarity = similarity_row.replace("0.", "")[0:2] + "%"
    else:
        similarity = "100%"

    data.append({
        "title" : json_result["docs"][0]["title_english"],
        "episode" : json_result["docs"][0]["episode"],
        "similarity" : similarity,
        "hentai" : json_result["docs"][0]["is_adult"],
        "preview" : preview
    })

    return jsonify(data)

@app.route("/media/search", methods=["GET"])
def mediaSearch():
    result = []
    data = []
    search_text = request.args.get("q")
    search_page = request.args.get("page")

    post_data = {
        "do" : "search",
        "subaction" : "search",
        "search_start" : search_page,
        "full_search" : "0",
        "result_from" : "1",
        "story" : search_text
    }

    search_data = session.post("http://online.anidub.com/index.php?do=search", data=post_data, headers=HEADERS).text
    tree = etree.HTML(search_data)
    news_title = tree.xpath('.//div[@class = "newstitle"]')
    news_info = tree.xpath('.//div[@class = "newsinfo"]')
    news_short = tree.xpath('.//div[@class = "news_short"]')
    news_short.pop(0)
    for n_title, n_info, n_short in zip(news_title, news_info, news_short):
        pages = tree.xpath('.//span[@class = "navigation"]')
        last_page = pages[0].xpath(".//a/text()")[-1] if pages else 1
        title = ''.join(n_title.xpath('.//div[@class="title"]/a/text()')).rsplit("/", 1)
        news_id = ''.join(n_title.xpath('.//div[@class="title"]/a/@href')).split('/')[-1].split('-')[0]
        category = ''.join(n_info.xpath('.//div[@style="background: none;"]/a/@href'))

        if "anidub_news" not in category and "videoblog" not in category:
            main_content = etree.tostring(n_short).decode("utf-8")
            rating_row = ''.join(n_short.xpath('.//b[@itemprop = "ratingValue"]/text()')) if 'itemprop="ratingValue"' in main_content else ''.join(n_short.xpath('.//div[@class = "rate_view"]/b/text()')) if 'class="rate_view"' in main_content else []
            poster = ''.join(n_short.xpath('.//div[@class = "poster_img"]/img/@src'))
            details = n_short.xpath('.//ul[@class="reset"]/li')
            for current_detail in details:
                detail = etree.tostring(current_detail).decode("utf-8")
                if "&#1043;&#1086;&#1076;:" in detail: year = ''.join(current_detail.xpath('.//span/text()'))
                if "&#1046;&#1072;&#1085;&#1088;:" in detail: genre = ', '.join(current_detail.xpath('.//span/a/text()'))
                country = ''.join(current_detail.xpath('.//span/text()')) if "&#1057;&#1090;&#1088;&#1072;&#1085;&#1072;:" in detail else "неизвестная"
                pub_date = ''.join(current_detail.xpath('.//span/text()')) if "&#1044;&#1072;&#1090;&#1072; &#1074;&#1099;&#1087;&#1091;&#1089;&#1082;&#1072;:" in detail else "NaN"
                producer = ''.join(current_detail.xpath('.//span/a/text()')) if "&#1056;&#1077;&#1078;&#1080;&#1089;&#1089;&#1077;&#1088;:" in detail else "неизвестный"
                author = ''.join(current_detail.xpath('.//span/a/text()')) if "&#1057;&#1094;&#1077;&#1085;&#1072;&#1088;&#1080;&#1089;&#1090;:" in detail else "неизвестный"
                if "&#1054;&#1079;&#1074;&#1091;&#1095;&#1080;&#1074;&#1072;&#1085;&#1080;&#1077;:" in detail: voicer = ', '.join(current_detail.xpath('.//span/a/text()')) 
            episode_row = re.search(r"\[(.*?)\]", title[-1])
            episode = "1 из 1" if not episode_row else episode_row.group(1)
            title_ru = title[0]
            title_en = title[-1].split("[")[0].lstrip()
            if "display:inline;" in main_content: description = ''.join(n_short.xpath('.//div[@style="display:inline;"]/text()'))
            result.append({
                "title"    : {
                    "ru"     : title_ru,
                    "en"    : title_en
                },
                "newsID"   : news_id,
                "rating"   : rating_row,
                "poster"   : poster,
                "year"     : year,
                "genre"    : genre,
                "country"  : country,
                "episode"  : episode, 
                "pubDate"  : pub_date,
                "producer" : producer,
                "author"   : author,
                "voicer"   : voicer,
                "description" : description
            })

    data.append({
        "last_page" : last_page,
        "data" : result
    })

    return jsonify(data)

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
            print(data)

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
        data_players.append("Stormo")
        stormo_contents = tree.xpath('.//select[@id = "sel3"]')

        for _, v in enumerate(stormo_contents):
            stormo_player_titles.append(v.xpath('.//option/text()'))
            stormo_player_episodes.append(v.xpath('.//option/@value'))

    if "our" in media_player:
        data_players.append("Anidub")
        anidub_player_contents = tree.xpath('.//select[@id = "sel2"]')

        for _, v in enumerate(anidub_player_contents):
            anidub_player_titles.append(v.xpath('.//option/text()'))
            anidub_player_episodes.append(v.xpath('.//option/@value'))

    if "vk" in media_player:
        data_players.append("Sibnet")
        sibnet_player_contents = tree.xpath('.//select[@id = "sel"]')
        
        if sibnet_player_contents:
            for _, v in enumerate(sibnet_player_contents):
                sibnet_player_titles.append(v.xpath('.//option/text()'))
                sibnet_player_episodes.append(v.xpath('.//option/@value'))
        else:
            sibnet_player_titles.append(stormo_player_titles[0][0] if stormo_player_titles else anidub_player_titles[0][0] if anidub_player_titles else "")
            sibnet_player_episodes.append(tree.xpath('.//div[@id = "mcode_block"]/iframe/@src')[0].replace("//", "https://"))
				
    data.append({
        "players" : data_players,
        
        "episodes" : {
            "title" : stormo_player_titles[0] if stormo_player_titles else anidub_player_titles[0] if anidub_player_titles else sibnet_player_titles[0] if sibnet_player_titles else "",
            "url" : {
                "Stormo" if "Stormo" in data_players else "" : stormo_player_episodes[0],
                "Anidub" if "Anidub" in data_players else "" : anidub_player_episodes[0],
                "Sibnet" if "Sibnet" in data_players else "" : sibnet_player_episodes[0]
            }
        }
    })

    return jsonify(data)


@app.route("/media/list/<page>", methods=["GET"])
def getMediaList(page = 1):
    data = []
    result = []
    html = session.get("http://online.anidub.com/page/" + page, headers=HEADERS).text
    tree = etree.HTML(html)
    news_title = tree.xpath('.//div[@class = "newstitle"]')
    news_info = tree.xpath('.//div[@class = "newsinfo"]')
    news_short = tree.xpath('.//div[@class = "news_short"]')
    for n_title, n_info, n_short in zip(news_title, news_info, news_short):
        pages = tree.xpath('.//span[@class = "navigation"]')
        last_page = pages[0].xpath(".//a/text()")[-1] if pages else 1
        title = ''.join(n_title.xpath('.//h2[@class="title"]/a/text()')).rsplit("/", 1)
        news_id = ''.join(n_title.xpath('.//h2[@class="title"]/a/@href')).split('/')[-1].split('-')[0]
        category = ''.join(n_info.xpath('.//h4[@style="float: left;"]/a/@href'))

        if "anidub_news" not in category and "videoblog" not in category:
            main_content = etree.tostring(n_short).decode("utf-8")
            rating_row = ''.join(n_short.xpath('.//b[@itemprop = "ratingValue"]/text()')) if 'itemprop="ratingValue"' in main_content else ''.join(n_short.xpath('.//div[@class = "rate_view"]/b/text()')) if 'class="rate_view"' in main_content else []
            # rating = rating_row + u" из 100%" if "%" in rating_row else rating_row + u" из 5"
            poster = ''.join(n_short.xpath('.//div[@class = "poster_img"]/a/img/@data-original'))
            details = n_short.xpath('.//ul[@class="reset"]/li')
            for current_detail in details:
                detail = etree.tostring(current_detail).decode("utf-8")
                if "&#1043;&#1086;&#1076;:" in detail: year = ''.join(current_detail.xpath('.//span/a/text()'))
                if "&#1046;&#1072;&#1085;&#1088;:" in detail: genre = ', '.join(current_detail.xpath('.//span/a/text()'))
                country = ''.join(current_detail.xpath('.//span/a/text()')) if "&#1057;&#1090;&#1088;&#1072;&#1085;&#1072;:" in detail else "неизвестная"
                pub_date = ''.join(current_detail.xpath('.//span/text()')) if "&#1044;&#1072;&#1090;&#1072; &#1074;&#1099;&#1087;&#1091;&#1089;&#1082;&#1072;:" in detail else "NaN"
                producer = ''.join(current_detail.xpath('.//span/a/text()')) if "&#1056;&#1077;&#1078;&#1080;&#1089;&#1089;&#1077;&#1088;:" in detail else "неизвестный"
                author = ''.join(current_detail.xpath('.//span/a/text()')) if "&#1057;&#1094;&#1077;&#1085;&#1072;&#1088;&#1080;&#1089;&#1090;:" in detail else "неизвестный"
                if "&#1054;&#1079;&#1074;&#1091;&#1095;&#1080;&#1074;&#1072;&#1085;&#1080;&#1077;:" in detail: voicer = ', '.join(current_detail.xpath('.//span/a/text()')) 
            episode_row = re.search(r"\[(.*?)\]", title[-1])
            episode = "1 из 1" if not episode_row else episode_row.group(1)
            title_ru = title[0]
            title_en = title[-1].split("[")[0].lstrip()
            if "&#1054;&#1087;&#1080;&#1089;&#1072;&#1085;&#1080;&#1077;" in main_content: description = ''.join(n_short.xpath('.//div[@style="display:inline;"]/text()'))
            result.append({
                "title"    : {
                    "ru"     : title_ru,
                    "en"    : title_en
                },
                "newsID"   : news_id,
                "rating"   : rating_row,
                "poster"   : poster,
                "year"     : year,
                "genre"    : genre,
                "country"  : country,
                "episode"  : episode, 
                "pubDate"  : pub_date,
                "producer" : producer,
                "author"   : author,
                "voicer"   : voicer,
                "description" : description
            })

    data.append({
        "last_page" : last_page,
        "data" : result
    })

    return jsonify(data)

@app.route("/", methods=["GET"])
def index():
    return "wat do u want?"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
