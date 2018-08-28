from flask import Flask, request, jsonify
import requests
from lxml import etree
import rapidjson

app = Flask(__name__)

fakeHeaders = {
    'Host' : 'anime.anidub.com',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'
}

@app.route('/getAnimeEpisodes/<page>')
def getAnimeList(newsId):
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
    tree = etree.HTML(html.decode("utf-8"))
    contents = tree.xpath('.//div[@class = "news_short"]')
    data = []
    for x in contents:
        short_news = etree.tostring(x).decode("utf-8")
        try:
            rating = x.xpath('.//div[@class = "rate_view"]/b/text()')[0]
        except:
            try:
                rating = x.xpath('.//b[@itemprop = "ratingValue"]/text()')[0]
            except:
                rating = []
        title = x.xpath('.//div[@class = "poster_img"]/a/img/@alt')

        data.append({
            'title' : title[0].split('Смотреть аниме ')[-1],
            'year' : x.xpath('.//ul[@class = "reset"]/li[1]/span/a/text()')[0],
            'poster' : x.xpath('.//div[@class = "poster_img"]/a/img/@data-original')[0],
            'genres' : x.xpath('.//ul[@class = "reset"]/li[2]/span/a/text()')[0],
            'country' : x.xpath('.//ul[@class = "reset"]/li[3]/span/a/text()')[0],
            'episodes' : title[0].split('[')[-1].split(']')[0],
            'description' : x.xpath('.//div[@class = "maincont"]/div[@style="display:inline;"]/text()')[0][0:-1],
            'rating' : rating[0],
            'newsId' : x.xpath('.//div[@class="poster_img"]/a/@href')[0].split('/')[-1].split('-')[0]
        })

    return jsonify(data)

if __name__ == '__main__':
    app.run(host='127.0.0.1', debug=True)