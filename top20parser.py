import re
import requests
import rapidjson
from lxml import etree

HEADERS = {
    "User-Agent" : "Mozilla/5.0 (Linux; Android 4.4.2; Nexus 4 Build/KOT49H) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/34.0.1847.114 Mobile Safari/537.36"
}

def getTopUrls() -> []:
    top_url = []

    top_page : str = requests.get("http://online.anidub.com/faq.html", headers=HEADERS).text
    tree = etree.HTML(top_page)
    top20 = tree.xpath('.//ul[@class = "top20"]')

    for top in top20:
        top_url.append(top.xpath(".//li/a/@href"))

    return top_url[0]

def parseTop(urls : []) -> []:
    data = []

    for url in urls:
        page_dom : str = requests.get(url, headers=HEADERS).text
        tree = etree.HTML(page_dom)
        title = tree.xpath('.//h1[@class="titlfull"]/text()')[0]
        short_news = etree.tostring(title).decode("utf-8")
        rating_dom = tree.xpath
        rating_row = tree.xpath('.//b[@itemprop = "ratingValue"]/text()')[0] if 'itemprop="ratingValue"' in short_news else tree.xpath('.//div[@class = "rate_view"]/b/text()')[0] if 'class="rate_view"' in short_news else []
        print(rating_row)
        rating = rating_row + " из 100%" if "%" in rating_row[0] else rating_row[0] + " из 5"
        ###########
        title = tree.xpath('.//div[@class = "poster_img"]/a/img/@alt')[0].replace("Смотреть аниме ", "").rsplit("/", 1)
        ###########
        year = tree.xpath('.//ul[@class = "reset"]/li[1]/span/a/text()')[0]
        genres = ", ".join(tree.xpath('.//ul[@class = "reset"]/li[2]/span/a/text()'))
        country = tree.xpath('.//ul[@class = "reset"]/li[3]/span/a/text()')[0]
        episodes_row = re.search(r"\[(.*?)\]", title[-1])
        episodes = [] if episodes_row is None else episodes_row.group(1)
        poster = tree.xpath('.//div[@class = "poster_img"]/a/img/@data-original')[0]
        description = tree.xpath('.//div[@class = "maincont"]/div[@style="display:inline;"]/text()')[0][0:-1]
        news_id = tree.xpath('.//div[@class="poster_img"]/a/@href')[0].split('/')[-1].split('-')[0]

        data.append({
                'title' : title[0],
                'year' : year,
                'poster' : poster,
                'genres' : genres,
                'country' : country,
                'episodes' : episodes,
                'description': description,
                'rating' : rating,
                'newsId' : news_id
            })

    return data

def main():
    urls : [] = getTopUrls()
    print(parseTop(urls))

if __name__ == "__main__":
    main()
