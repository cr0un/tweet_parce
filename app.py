import time
from parsel import Selector
from playwright.sync_api import sync_playwright
from playwright.sync_api._generated import Page
import requests
import json
import logging


# Запись логов (по умолчанию в контейнер)
logging.basicConfig(level=logging.INFO)
# logging.basicConfig(filename='app.log', level=logging.INFO) # можно направить в файл


# Бот телеграм
chat_id = 'chat_id'
token = 'bot_tg_token'


def send_message(chat_id: str, tweet: dict, token: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    message_text = f"{tweet['text']}\n{tweet['url']}"
    payload = {
        'chat_id': chat_id,
        'text': message_text,
        'parse_mode': 'HTML'
    }
    response = requests.post(url, payload)

    # Проверка отправки
    if response.status_code != 200:
        print(f"Failed to send message. Response: {response.content}")


def parse_tweets(selector: Selector, tweets_list: list):
    tweets = selector.xpath("//article[@data-testid='tweet']")
    for i, tweet in enumerate(tweets):
        found = {
            "text": "".join(tweet.xpath(".//*[@data-testid='tweetText']//text()").getall()),
            "datetime": tweet.xpath(".//time/@datetime").get(),
            "url": "https://twitter.com" + tweet.xpath(".//time/../@href").get(),
        }
        if i == 0:
            found["datetime"] = tweet.xpath('.//span[contains(text(),"·")]/../@datetime').get()

        if found not in tweets_list:
            tweets_list.append(found)


# Фильтрация
def filter_tweets(tweets_list: list):
    filtered_tweets = []
    for tweet in tweets_list:
        if 'maintenan' in tweet['text'].lower():
            filtered_tweets.append(tweet)
    return filtered_tweets


# Парсим твиты
def scrape_tweets(url: str, page: Page):
    page.goto(url)
    page.wait_for_selector("//article[@data-testid='tweet']")

    tweets_list = []

    while len(tweets_list) < 10:
        html = page.content()
        selector = Selector(html)
        parse_tweets(selector, tweets_list)

        # Прокрутка страницы
        page.evaluate('window.scrollBy({top: window.innerHeight, behavior: "smooth"})')

        # Доп. задержка для загрузки твитов
        time.sleep(2)

    filtered_tweets = filter_tweets(tweets_list)
    return filtered_tweets[-10:]


def load_processed_urls():
    try:
        with open('processed_urls.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_processed_urls(urls):
    with open('processed_urls.json', 'w') as f:
        json.dump(urls, f)


with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=False)
    page1 = browser.new_page(viewport={"width": 960, "height": 540})
    page2 = browser.new_page(viewport={"width": 960, "height": 540})
    page3 = browser.new_page(viewport={"width": 960, "height": 540})

    processed_urls = load_processed_urls()

    while True:
        # Указываем источники с твитами
        tweets1 = scrape_tweets("https://twitter.com/binance", page1)
        tweets2 = scrape_tweets("https://twitter.com/krakenfx", page2)
        tweets3 = scrape_tweets("https://twitter.com/bitfinex", page3)

        all_tweets = tweets1 + tweets2 + tweets3
        unique_tweets = [tweet for tweet in all_tweets if tweet['url'] not in processed_urls]

        for tweet in unique_tweets:
            tweet['url'] = tweet['url'].replace('https://twitter.com/', 'https://twitter.com/')
            send_message(chat_id, tweet, token)

        print(unique_tweets)
        logging.info(unique_tweets)

        # Сохранение твитов в файл
        with open('tweets.json', 'a') as f:
            for tweet in unique_tweets:
                json.dump(tweet, f)
                f.write('\n')

        # Обновление обработанных ссылок
        processed_urls.extend([tweet['url'] for tweet in unique_tweets])
        save_processed_urls(processed_urls)

        # Время получения новых твитов (раз в час по умолчанию)
        time.sleep(3600)
