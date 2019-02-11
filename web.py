# coding=utf-8

import re

import requests
from flask import Flask, current_app, jsonify, request, send_from_directory
from lxml import etree

import rapidjson

HEADERS = {"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.81 Safari/537.36"}
home_page = "https://anime.anidub.com"
media_list = f"{home_page}/page"
episodes_list = f"{home_page}/?newsid="

session = requests.session()
app = Flask(__name__)

def sendGetRequest(url):
    return session.request("get", url, headers=HEADERS, verify=False)

@app.route("/player/decode", methods=["GET"])
def playerDecode():
    return send_from_directory(directory="keys", filename="anidub", as_attachment=True)

@app.route("/media/episodes", methods=["GET"])
def getMediaEpisodes():
    data = []
    news_id = request.args.get("news_id")
    response = sendGetRequest(f"{episodes_list}{news_id}")
    parsed_html = etree.HTML(response.text)
    media_players = parsed_html.xpath('.//div[@class="player"]/ul[@class="tabs"]/li/@id')
    if "our" in media_players:
        anidub_player_contents = parsed_html.xpath('.//select[@id = "sel2"]')
        for v in anidub_player_contents:
            anidub_player_titles   = v.xpath('.//option/text()')
            anidub_player_episodes = list(map(lambda x: x.replace("index", "video").split("&url")[0], v.xpath('.//option/@value')))
    data.append({
        "episodes" : {
            "title" : anidub_player_titles,
            "url" : {
                "Anidub": anidub_player_episodes
            }
        }
    })

    return getResponseAnswer(False, "Ok", data[0])

@app.route("/media", methods=["GET"])
def getMedia():
    data = []
    page = request.args.get("page")

    response = sendGetRequest(f"{media_list}/{page}")
    parsed_html = etree.HTML(response.text)
    news_head = parsed_html.xpath('.//div[@class = "newstitle"]')
    news_info = parsed_html.xpath('.//div[@class = "newsinfo"]')
    news_body = parsed_html.xpath('.//div[@class = "news_short"]')
    
    for n_head, n_info, n_body in zip(news_head, news_info, news_body):
        title = ''.join(n_head.xpath('.//h2[@class="title"]/a/text()')).split("/")
        news_id = ''.join(n_head.xpath('.//h2[@class="title"]/a/@href')).split('/')[-1].split('-')[0]
        category = ''.join(n_info.xpath('.//h4[@style="float: left;"]/a/@href'))
        
        if "anidub_news" not in category and "videoblog" not in category and "anons" not in category:
            parsed_body = str(etree.tostring(n_body))
            rating = ''.join(n_body.xpath('.//b[@itemprop = "ratingValue"]/text()') if 'itemprop="ratingValue"' in parsed_body else n_body.xpath('.//div[@class = "rate_view"]/b/text()') if 'class="rate_view"' in parsed_body else []) 
            poster = ''.join(n_body.xpath('.//div[@class = "poster_img"]/a/img/@data-original'))
            details = n_body.xpath('.//ul[@class="reset"]/li')
            for current_detail in details:
                detail = etree.tostring(current_detail).decode("utf-8")
                if "&#1043;&#1086;&#1076;:" in detail: year = ''.join(current_detail.xpath('.//span/a/text()')) 
                if "&#1046;&#1072;&#1085;&#1088;:" in detail: genre = ', '.join(current_detail.xpath('.//span/a/text()'))
                if "&#1057;&#1090;&#1088;&#1072;&#1085;&#1072;" in detail: country = ''.join(current_detail.xpath('.//span/a/text()'))
            episode_row = re.search(r"\[(.*?)\]", title[-1])
            episode = "1 из 1" if not episode_row else episode_row.group(1)
            title_ru = title[0]
            title_en = title[-1].split("[")[0].lstrip()
            if "display:inline;" in parsed_body: description = ''.join(n_body.xpath('.//div[@style="display:inline;"]/text()'))

            data.append({
                "title"       : {"ru" : title_ru, "en" : title_en},
                "news_id"     : news_id,
                "rating"      : rating,
                "poster"      : poster,
                "year"        : year,
                "country"     : country,
                "genre"       : genre,
                "episode"     : episode,
                "description" : description
            })
        
    return getResponseAnswer(False, "Ok", data)

def getResponseAnswer(error = False, message = "Ok", data = 0):
    return jsonify({
        "status" : {
            "error" : False,
            "message" : "Ok"
        },
        "data" : data})


@app.route("/", methods=["GET"])
def index():
    return "wat do u want?"

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
