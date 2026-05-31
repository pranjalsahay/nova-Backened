import os
import requests
import wikipedia
import xml.etree.ElementTree as ET


# =========================================
# API KEYS
# =========================================

WEATHER_KEY = os.getenv("WEATHER_KEY")
NEWS_KEY = os.getenv("NEWS_KEY")
OCR_KEY = os.getenv("OCR_KEY")
TMDB_KEY = os.getenv("TMDB_KEY")


# =========================================
# WEATHER
# =========================================

def get_weather(city):

    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}"
        f"&appid={WEATHER_KEY}"
        f"&units=metric"
    )

    data = requests.get(url).json()

    return (
        f"{city}: "
        f"{data['main']['temp']}°C, "
        f"{data['weather'][0]['description']}"
    )


# =========================================
# NEWS
# =========================================

def get_news():

    url=(
        f"https://newsapi.org/v2/top-headlines"
        f"?country=in"
        f"&apiKey={NEWS_KEY}"
    )

    data=requests.get(url).json()

    headlines=[]

    for article in data["articles"][:5]:

        headlines.append(
            article["title"]
        )

    return "\n".join(headlines)


# =========================================
# WIKIPEDIA
# =========================================

def search_wikipedia(query):

    return wikipedia.summary(
        query,
        sentences=3
    )


# =========================================
# GITHUB
# =========================================

def github_user(username):

    url=f"https://api.github.com/users/{username}"

    data=requests.get(url).json()

    return (
        f"Name: {data['name']}\n"
        f"Repos: {data['public_repos']}"
    )


# =========================================
# CRYPTO
# =========================================

def crypto_price(coin):

    url=(
        f"https://api.coingecko.com/api/v3/simple/price"
        f"?ids={coin}"
        f"&vs_currencies=usd"
    )

    data=requests.get(url).json()

    return (
        f"{coin}: "
        f"${data[coin]['usd']}"
    )


# =========================================
# GOOGLE BOOKS
# =========================================

def search_book(book):

    url=(
        f"https://www.googleapis.com/books/v1/volumes"
        f"?q={book}"
    )

    data=requests.get(url).json()

    item=data["items"][0]

    return (
        item["volumeInfo"]["title"]
        + " by "
        + item["volumeInfo"]["authors"][0]
    )


# =========================================
# arXiv
# =========================================

def research_paper(topic):

    url=(
        f"http://export.arxiv.org/api/query"
        f"?search_query=all:{topic}"
    )

    xml=requests.get(url)

    root=ET.fromstring(xml.content)

    title=root[1][3].text

    return title


# =========================================
# TMDB
# =========================================
