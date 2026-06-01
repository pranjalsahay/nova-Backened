import os
import sys
import requests
import webbrowser
from urllib.parse import quote
from memory import (
    save_personal_memory,
    get_personal_memory,
    get_all_memory
)

try:
    from vision import read_screen_text, detect_error
    VISION_AVAILABLE = True
except Exception:
    VISION_AVAILABLE = False
    def read_screen_text():
        return "Screen reading is not available in server mode."
    def detect_error():
        return "Screen error detection is not available in server mode."

# ==================================================
# API KEYS
# ==================================================
WEATHER_KEY = os.getenv("WEATHER_KEY")
NEWS_KEY    = os.getenv("NEWS_KEY")


def _open_app(win_cmd, mac_cmd, linux_cmd):
    if sys.platform == "win32":
        os.system(win_cmd)
    elif sys.platform == "darwin":
        os.system(mac_cmd)
    else:
        os.system(linux_cmd)


# ==================================================
# WEATHER
# ==================================================
WEATHER_TRIGGERS = ["weather", "temperature", "how hot", "how cold", "forecast"]

def get_weather(cmd):
    if not WEATHER_KEY:
        return "Weather is not available. The API key is missing."

    city = None
    for trigger in ["weather in ", "weather for ", "temperature in ", "forecast for ", "forecast in "]:
        if trigger in cmd:
            city = cmd.split(trigger, 1)[1].strip()
            break
    if not city:
        for trigger in ["weather ", "temperature ", "forecast "]:
            if cmd.startswith(trigger):
                city = cmd.replace(trigger, "", 1).strip()
                break
    if not city:
        return "Please say which city you want the weather for. For example: weather in London."

    try:
        response = requests.get(
            "https://api.openweathermap.org/data/2.5/weather",
            params={"q": city, "appid": WEATHER_KEY, "units": "metric"},
            timeout=10
        )
        data = response.json()
        if response.status_code != 200:
            return f"Sorry, I couldn't get the weather for {city}. {data.get('message', 'Unknown error')}."

        name     = data["name"]
        country  = data["sys"]["country"]
        temp     = round(data["main"]["temp"])
        feels    = round(data["main"]["feels_like"])
        desc     = data["weather"][0]["description"].capitalize()
        humidity = data["main"]["humidity"]

        return (
            f"The weather in {name}, {country} is {desc}. "
            f"It is {temp}°C and feels like {feels}°C. "
            f"Humidity is {humidity}%."
        )
    except requests.exceptions.Timeout:
        return "Sorry, the weather service took too long to respond."
    except Exception as e:
        print(f"[Weather Error] {type(e).__name__}: {e}")
        return "Sorry, I couldn't fetch the weather right now."


# ==================================================
# NEWS
# ==================================================
NEWS_TRIGGERS = ["news", "headlines", "what's happening", "latest news"]

def get_news(cmd):
    if not NEWS_KEY:
        return "News is not available. The API key is missing."

    topic = None
    for trigger in ["news about ", "news on ", "headlines about ", "headlines on ",
                    "latest news on ", "latest news about "]:
        if trigger in cmd:
            topic = cmd.split(trigger, 1)[1].strip()
            break

    try:
        if topic:
            response = requests.get(
                "https://newsapi.org/v2/everything",
                params={"q": topic, "apiKey": NEWS_KEY, "pageSize": 3,
                        "sortBy": "publishedAt", "language": "en"},
                timeout=10
            )
        else:
            response = requests.get(
                "https://newsapi.org/v2/top-headlines",
                params={"apiKey": NEWS_KEY, "pageSize": 3, "language": "en", "country": "us"},
                timeout=10
            )

        data = response.json()
        if response.status_code != 200 or data.get("status") != "ok":
            return f"Sorry, I couldn't get the news. {data.get('message', 'Unknown error')}."

        articles = data.get("articles", [])
        if not articles:
            return "I couldn't find any news articles right now."

        label  = f"top news about {topic}" if topic else "top headlines"
        result = f"Here are the {label}. "
        for i, article in enumerate(articles[:3], 1):
            title = article.get("title", "No title")
            if " - " in title:
                title = title.rsplit(" - ", 1)[0].strip()
            result += f"{i}. {title}. "
        return result.strip()

    except requests.exceptions.Timeout:
        return "Sorry, the news service took too long to respond."
    except Exception as e:
        print(f"[News Error] {type(e).__name__}: {e}")
        return "Sorry, I couldn't fetch the news right now."


# ==================================================
# MAIN ACTION HANDLER
# ==================================================
def perform_action(command):
    cmd = command.lower().strip()

    # WEATHER
    if any(t in cmd for t in WEATHER_TRIGGERS):
        return get_weather(cmd)

    # NEWS
    if any(t in cmd for t in NEWS_TRIGGERS):
        return get_news(cmd)

    # PERSONAL MEMORY
    if cmd.startswith("remember "):
        text = cmd.replace("remember", "", 1).strip()
        if " is " in text:
            key, value = text.split(" is ", 1)
            save_personal_memory(key.strip(), value.strip())
            return f"I will remember that {key.strip()} is {value.strip()}"
        return "Say it like this: Remember favorite editor is VS Code"

    if cmd.startswith("what is ") or cmd.startswith("who is "):
        key = cmd.replace("what is ", "").replace("who is ", "").strip()
        memory = get_personal_memory(key)
        if memory:
            return f"{key} is {memory}"

    if "what do you know about me" in cmd or "show personal memory" in cmd:
        memories = get_all_memory()
        if not memories:
            return "I don't know anything about you yet."
        result = "Here is what I know about you. "
        for key, value in memories:
            result += f"{key} is {value}. "
        return result

    # YOUTUBE
    if cmd.startswith("play "):
        search = cmd.replace("play", "", 1).strip()
        webbrowser.open("https://www.youtube.com/results?search_query=" + quote(search))
        return f"Playing {search} on YouTube"

    # OPEN WEBSITES
    sites = {
        "open youtube":   "https://youtube.com",
        "open google":    "https://google.com",
        "open whatsapp":  "https://web.whatsapp.com",
        "open gmail":     "https://mail.google.com",
        "open chatgpt":   "https://chat.openai.com",
        "open github":    "https://github.com",
        "open netflix":   "https://netflix.com",
        "open twitter":   "https://twitter.com",
        "open instagram": "https://instagram.com",
        "open reddit":    "https://reddit.com",
    }
    for phrase, url in sites.items():
        if phrase in cmd:
            webbrowser.open(url)
            return f"Opening {phrase.replace('open ', '').title()}"

    if cmd.startswith("search "):
        query = cmd.replace("search", "", 1).strip()
        webbrowser.open("https://www.google.com/search?q=" + quote(query))
        return f"Searching Google for {query}"

    # SCREEN VISION
    if "what is on my screen" in cmd or "read screen" in cmd:
        return read_screen_text()
    if "read this error" in cmd or "check error" in cmd:
        return detect_error()

    # DESKTOP ACTIONS
    if "open chrome" in cmd:
        return "Opening Chrome is only available when running locally."
    if "open vs code" in cmd or "open vscode" in cmd:
        return "Opening VS Code is only available when running locally."
    if "open spotify" in cmd:
        return "Opening Spotify is only available when running locally."
    if "take screenshot" in cmd or "screenshot" in cmd:
        return "Screenshots are only available when running locally."
    if "shutdown" in cmd or "restart" in cmd or "lock" in cmd:
        return "System controls are only available when running locally."

    return None
