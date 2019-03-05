# coding=utf-8

import re

from flask import Flask, jsonify, request
from lxml import etree
from requests import Session

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:65.0) Gecko/20100101 Firefox/65.0"
}
HOME_PAGE = "https://online.anidub.com"
MEDIA_LIST_PAGE = f"{HOME_PAGE}/page"
SEARCH_PAGE = f"{HOME_PAGE}/index.php?do=search"
EPISODES_LIST = f"{HOME_PAGE}/?newsid="
RANDOM_PAGE = f"{HOME_PAGE}/faq.html"
TOP_ONGOING_PAGE = f"{HOME_PAGE}/anime/anime_ongoing/"
TOP_FILM_PAGE = f"{HOME_PAGE}/anime_movie/"
TOP_TV_PAGE = f"{HOME_PAGE}/anime/"
TOP_OVA_PAGE = f"{HOME_PAGE}/anime_ova/"
TOP_DORAMA_PAGE = f"{HOME_PAGE}/dorama/"

session = Session()
app = Flask(__name__)


def sendRequest(method, url, data=[]):
    return session.request(method, url, data=data, headers=HEADERS, verify=False)


def getFile(file_name):
    with open(file_name) as file:
        return file.read()

@app.errorhandler(500)
def page_not_found(e):
    return getResponseAnswer(error=True, error_code=500, error_message="Страница временно не доступна")

@app.route("/app/update", methods=["GET"])
def appUpdate():
    data = []
    data.append(eval(getFile("update.json")))
    return getResponseAnswer(False, 0, "", data[0])


@app.route("/media/episodes", methods=["GET"])
def getMediaEpisodes():
    data = []
    news_id = request.args.get("news_id")
    response = sendRequest("GET", f"{EPISODES_LIST}{news_id}")
    parsed_html = etree.HTML(response.text)
    adult_content = True if "&#1085;&#1077; &#1080;&#1084;&#1077;&#1102;&#1090; &#1076;&#1086;&#1089;&#1090;&#1091;&#1087;&#1072;" in response.text else False
    media_players = parsed_html.xpath(
        './/div[@class="player"]/ul[@class="tabs"]/li/@id'
    )
    if "our" in media_players:
        anidub_player_contents = parsed_html.xpath('.//select[@id = "sel2"]')
        for v in anidub_player_contents:
            anidub_player_titles = v.xpath(".//option/text()")
            anidub_player_episodes = list(
                map(
                    lambda x: x.replace("index", "video").split("&url")[0],
                    v.xpath(".//option/@value"),
                )
            )
    data.append(
        {
            "adult" : adult_content,
            "episodes": {
                "title": anidub_player_titles,
                "url": {"Anidub": anidub_player_episodes},
            }
        }
    )

    return getResponseAnswer(False, 0, "", data[0])


@app.route("/media/top", methods=["GET"])
def getMediaTop():
    data = []
    category = request.args.get("category")

    if category == "ongoing":
        response = sendRequest("GET", TOP_ONGOING_PAGE)
    if category == "film":
        response = sendRequest("GET", TOP_FILM_PAGE)
    if category == "tv":
        response = sendRequest("GET", TOP_TV_PAGE)
    if category == "ova":
        response = sendRequest("GET", TOP_OVA_PAGE)
    if category == "dorama":
        response = sendRequest("GET", TOP_DORAMA_PAGE)

    parsed_html = etree.HTML(response.text)
    top_list = parsed_html.xpath('.//ul[@class = "top20"]')
    for v in top_list:
        top_title = list(map(lambda x: x.split("/")[0], v.xpath(".//li/a/@title")))
        top_news_id = list(
            map(lambda x: x.replace("(", "").replace(")", ""), v.xpath(".//li/a/@href"))
        )
        top_vote = v.xpath(".//li/small/text()")

        data.append({"title": top_title, "news_id": top_news_id, "vode": top_vote})

    return getResponseAnswer(False, 0, "", data)


@app.route("/media/random", methods=["GET"])
def getMediaRandom():
    data = []

    response = sendRequest("GET", RANDOM_PAGE)
    parsed_html = etree.HTML(response.text)
    news_id = (
        "".join(parsed_html.xpath('.//div[@class = "r_title"]/a/@href'))
        .split("/")[-1]
        .split("-")[0]
    )

    data.append({"news_id": news_id})

    return getResponseAnswer(False, 0, "", data)


@app.route("/media/search", methods=["GET"])
def getMediaSearch():
    data = []
    query = request.args.get("q")
    page = request.args.get("page")

    post_data = {
        "do": "search",
        "subaction": "search",
        "full_search": "0",
        "result_from": "1",
        "story": query,
        "search_start": page,
    }
    response = sendRequest("POST", SEARCH_PAGE, post_data)
    parsed_html = etree.HTML(response.text)
    news_head = parsed_html.xpath('.//div[@class = "newstitle"]')
    news_info = parsed_html.xpath('.//div[@class = "newsinfo"]')
    news_body = parsed_html.xpath('.//div[@class = "news_short"]')
    news_body.pop(0)

    for n_head, n_info, n_body in zip(news_head, news_info, news_body):
        title = "".join(n_head.xpath('.//div[@class="title"]/a/text()')).split("/")
        news_id = (
            "".join(n_head.xpath('.//div[@class="title"]/a/@href'))
            .split("/")[-1]
            .split("-")[0]
        )
        category = "".join(n_info.xpath('.//div[@style="background: none;"]/a/@href'))

        if (
            "anidub_news" not in category
            and "videoblog" not in category
            and "anons" not in category
        ):
            parsed_body = str(etree.tostring(n_body))
            rating = "".join(
                n_body.xpath('.//b[@itemprop = "ratingValue"]/text()')
                if 'itemprop="ratingValue"' in parsed_body
                else n_body.xpath('.//div[@class = "rate_view"]/b/text()')
                if 'class="rate_view"' in parsed_body
                else []
            )
            poster = "".join(n_body.xpath('.//div[@class = "poster_img"]/img/@src'))
            details = n_body.xpath('.//ul[@class="reset"]/li')
            for current_detail in details:
                detail = etree.tostring(current_detail).decode("utf-8")
                if "&#1043;&#1086;&#1076;:" in detail:
                    year = "".join(current_detail.xpath(".//span/text()"))
                if "&#1046;&#1072;&#1085;&#1088;:" in detail:
                    genre = ", ".join(current_detail.xpath(".//span/a/text()"))
                if "&#1057;&#1090;&#1088;&#1072;&#1085;&#1072;" in detail:
                    country = "".join(current_detail.xpath(".//span/text()"))
            episode_row = re.search(r"\[(.*?)\]", title[-1])
            episode = episode_row.group(1) if episode_row else "1 из 1"
            title_ru = title[0]
            title_en = title[-1].split("[")[0].lstrip()
            if "display:inline;" in parsed_body:
                description = "".join(
                    n_body.xpath('.//div[@style="display:inline;"]/text()')
                )

            data.append(
                {
                    "title": {"ru": title_ru, "en": title_en},
                    "news_id": news_id,
                    "rating": rating,
                    "poster": poster,
                    "year": year,
                    "country": country,
                    "genre": genre,
                    "episode": episode,
                    "description": description,
                }
            )

    return getResponseAnswer(False, 0, "", data)


@app.route("/media", methods=["GET"])
def getMedia():
    data = []
    page = request.args.get("page")

    response = sendRequest("GET", f"{MEDIA_LIST_PAGE}/{page}")
    parsed_html = etree.HTML(response.text)
    news_head = parsed_html.xpath('.//div[@class = "newstitle"]')
    news_info = parsed_html.xpath('.//div[@class = "newsinfo"]')
    news_body = parsed_html.xpath('.//div[@class = "news_short"]')

    for n_head, n_info, n_body in zip(news_head, news_info, news_body):
        title = "".join(n_head.xpath('.//h2[@class="title"]/a/text()')).split("/")
        news_id = (
            "".join(n_head.xpath('.//h2[@class="title"]/a/@href'))
            .split("/")[-1]
            .split("-")[0]
        )
        category = "".join(n_info.xpath('.//h4[@style="float: left;"]/a/@href'))

        if (
            "anidub_news" not in category
            and "videoblog" not in category
            and "anons" not in category
        ):
            parsed_body = str(etree.tostring(n_body))
            rating = "".join(
                n_body.xpath('.//b[@itemprop = "ratingValue"]/text()')
                if 'itemprop="ratingValue"' in parsed_body
                else n_body.xpath('.//div[@class = "rate_view"]/b/text()')
                if 'class="rate_view"' in parsed_body
                else []
            )
            poster = "".join(
                n_body.xpath('.//div[@class = "poster_img"]/a/img/@data-original')
            )
            details = n_body.xpath('.//ul[@class="reset"]/li')
            for current_detail in details:
                detail = etree.tostring(current_detail).decode("utf-8")
                if "&#1043;&#1086;&#1076;:" in detail:
                    year = "".join(current_detail.xpath(".//span/a/text()"))
                if "&#1046;&#1072;&#1085;&#1088;:" in detail:
                    genre = ", ".join(current_detail.xpath(".//span/a/text()"))
                if "&#1057;&#1090;&#1088;&#1072;&#1085;&#1072;" in detail:
                    country = "".join(current_detail.xpath(".//span/a/text()"))
            episode_row = re.search(r"\[(.*?)\]", title[-1])
            episode = episode_row.group(1) if episode_row else "1 из 1"
            title_ru = title[0]
            title_en = title[-1].split("[")[0].lstrip()
            if "display:inline;" in parsed_body:
                description = "".join(
                    n_body.xpath('.//div[@style="display:inline;"]/text()')
                )

            data.append(
                {
                    "title": {"ru": title_ru, "en": title_en},
                    "news_id": news_id,
                    "rating": rating,
                    "poster": poster,
                    "year": year,
                    "country": country,
                    "genre": genre,
                    "episode": episode,
                    "description": description,
                }
            )

    return getResponseAnswer(False, 0, "", data)


def getResponseAnswer(error=False, error_code=700, error_message="", data=0):
    if error:
        return jsonify(
            {
                "status": "error",
                "error": {"error_code": error_code, "error_message": error_message},
            }
        )
    return jsonify({"status": "success", "data": data})


@app.route("/", methods=["GET"])
def index():
    return "wat do u want?"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
