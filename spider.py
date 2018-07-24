import requests
import json
import pymongo
from multiprocessing import Pool
from bs4 import BeautifulSoup
from urllib.parse import urlencode
from requests.exceptions import ConnectionError
from config import *

client = pymongo.MongoClient(MONGO_URL, 27017)
db = client[MONGO_DB]


# 获得索引页的信息
def get_index(offset):
    base_url = 'http://www.guokr.com/apis/minisite/article.json?'
    data = {
        'retrieve_type': "by_subject",
        'limit': "20",
        'offset': offset
    }

    # params = urlencode(data)
    url = base_url + urlencode(data)
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        return None
    except ConnectionError:
        print('Error.')
        return None


# 解析json，获取文章url
def parse_json(text):
    try:
        result = json.loads(text)
        if result:
            for i in result.get('result'):
                yield i.get('url')
    except:
        pass


def get_page(url):
    try:
        r = requests.get(url)
        if r.status_code == 200:
            return r.text
        return None
    except ConnectionError:
        print('Error.')
        return None


# 解析文章页
def parse_page(text):
    try:
        soup = BeautifulSoup(text, 'lxml')
        context = soup.find('div', class_="content")
        title = context.find('h1', id="articleTitle").get_text()
        author = context.find('div', class_="content-th-info").find('a').get_text()
        article_content = context.find('div', class_="document").find_all('p')
        all_p = [i.get_text() for i in article_content if not i.find('img') and not i.find('a')]
        article = '\n'.join(all_p)
        data = {
            'title': title,
            'author': author,
            'article': article
        }
        return data
    except:
        pass


def save_database(data):
    if db[MONGO_TABLE].insert(data):
        print('Save to Database successful', data)
        return True
    return False


# 定义一个主函数
def main(offset):
    text = get_index(offset)
    all_url = parse_json(text)
    for url in all_url:
        r = get_page(url)
        data = parse_page(r)
        if data:
            save_database(data)


if __name__ == '__main__':
    pool = Pool()
    offsets = ([0] + [i * 20 + 18 for i in range(500)])
    pool.map(main, offsets)
    pool.close()
    pool.join()
