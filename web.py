from flask import Flask, request, jsonify
import requests
from lxml import html as LH
# import lxml

app = Flask(__name__)

fakeHeaders = {
    'User-Agent' : 'Mozilla/5.0'
}

@app.route('/getAnimeEpisodes/<page>')
def getAnimeEpisodes(newsId):
    html = requests.get("http://anime.anidub.com/?newsid=" + newsId, headers=fakeHeaders).content
    tree = etree.HTML(html.decode("utf-8"))
    contents = tree.xpath('.//select[@id = "sel3"]')
    data = []
    for x in contents:
        for i in range(0, len(contents[0])):
            data.append({
                'episode' : x.xpath('.//option/text()')[i],
                'url' : x.xpath('.//option/@value')[i]
            })
            
    return jsonify(data)

@app.route('/getAnimeList/<page>')
def getAnimeList(page = 1):
    html = requests.get("https://anime.anidub.com/page/" + page, headers=fakeHeaders).content
    # tree = etree.HTML(html)
    tree = LH.document_fromstring(html)
    contents = tree.xpath('.//div[@class = "news_short"]')
    data = []
    for x in contents:
        # short_news = etree.tostring(x).decode("utf-8")
        short_news = LH.tostring(x)
        print(short_news)
        exit(1)

        if 'ratingValue' in short_news:
            rating = x.xpath('.//b[@itemprop = "ratingValue"]/text()')
        elif 'rate_view' in short_news:
            rating = x.xpath('.//div[@class = "rate_view"]/b/text()')
        else:
            rating = []
        ###########
        title = x.xpath('.//div[@class = "poster_img"]/a/img/@alt')
        ###########
        year = x.xpath('.//ul[@class = "reset"]/li[1]/span/a/text()')[0] if 'Год:' in short_news else []
        genres = x.xpath('.//ul[@class = "reset"]/li[2]/span/a/text()')[0] if 'Жанр:' in short_news else []
        country = x.xpath('.//ul[@class = "reset"]/li[3]/span/a/text()')[0] if 'Страна:' in short_news else []
        episodes = title[0].split('[')[-1].split(']')[0]
        description = x.xpath('.//div[@class = "maincont"]/div[@style="display:inline;"]/text()')[0][0:-1] if 'Описание:' in short_news else []
        news_id = x.xpath('.//div[@class="poster_img"]/a/@href')[0].split('/')[-1].split('-')[0]
        ###########
        data.append({
            'title' : title[0].split('Смотреть аниме ')[-1],
            'year' : year,
            'poster' : x.xpath('.//div[@class = "poster_img"]/a/img/@data-original')[0],
            'genres' : genres,
            'country' : country,
            'episodes' : title[0].split('[')[-1].split(']')[0],
            'description': description,
            'rating' : rating,
            'newsId' : news_id
        })

    return jsonify(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)