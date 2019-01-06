import re
from urllib.parse import urlparse
from flask import Flask, request, jsonify
import requests
from lxml import etree

HEADERS = {
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36"
}

session = requests.session()

app = Flask(__name__)

@app.route("/media/content", methods=["GET"])
def getMediaContent():
    media_url = request.args.get("media_url").split("|")[0]
    player_type = urlparse(media_url).netloc
    
    if player_type == "www.stormo.tv":
        html = session.get(media_url, headers=HEADERS, allow_redirects=True).text
        quality_urls = re.search('file:"(.*?)",', html).group(1)
        devide_quality_urls = quality_urls.split(",")
        data = []
        if len(devide_quality_urls) == 1:
            data.append({
                "Unknown" : devide_quality_urls[0]
            })
        else:
            for x in devide_quality_urls:
                current_quality = re.search(r"\[(.*?)\]", x).group(1)
                current_content_url = x.replace(f"[{current_quality}]", "")
                data.append({
                    current_quality : current_content_url
                })
    return jsonify(data)

@app.route("/media/episodes/<news_id>", methods=["GET"])
def getMediaEpisodes(news_id):
    html = session.get("http://online.anidub.com/?newsid=" + news_id, headers=HEADERS).text
    tree = etree.HTML(html)
    contents = tree.xpath('.//select[@id = "sel3"]')
    data = []
    for x in contents:
        for i in range(0, len(contents[0])):
            data.append({
                'episode' : x.xpath('.//option/text()')[i],
                'url' : x.xpath('.//option/@value')[i]
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
            rating = x.xpath('.//b[@itemprop = "ratingValue"]/text()') if 'itemprop="ratingValue"' in short_news else x.xpath('.//div[@class = "rate_view"]/b/text()') if 'class="rate_view"' in short_news else []
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