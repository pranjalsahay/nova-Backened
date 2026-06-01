import os
import sys
import re
import math
import requests
import webbrowser
import wikipedia
from datetime import datetime
from urllib.parse import quote
from memory import (
    save_personal_memory,
    get_personal_memory,
    get_all_memory
)

# vision.py uses screen capture (mss, cv2, pytesseract)
# These won't work on a server — safely disabled
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
# API KEYS (from environment — never hardcoded)
# ==================================================
WEATHER_KEY = os.getenv("WEATHER_KEY")
NEWS_KEY    = os.getenv("NEWS_KEY")
TMDB_KEY    = os.getenv("TMDB_KEY")


def _open_app(win_cmd, mac_cmd, linux_cmd):
    """Open native app cross-platform."""
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
# WIKIPEDIA
# ==================================================
WIKI_TRIGGERS = ["what is ", "who is ", "tell me about ", "wikipedia ", "wiki "]

def get_wikipedia(cmd):
    query = None
    for trigger in ["tell me about ", "wikipedia ", "wiki "]:
        if trigger in cmd:
            query = cmd.split(trigger, 1)[1].strip()
            break
    if not query:
        # "what is X" / "who is X" — only use Wikipedia if not in memory
        for trigger in ["what is ", "who is "]:
            if cmd.startswith(trigger):
                query = cmd.replace(trigger, "", 1).strip()
                break
    if not query:
        return None

    try:
        wikipedia.set_lang("en")
        summary = wikipedia.summary(query, sentences=2, auto_suggest=True)
        # Strip markdown/brackets
        summary = re.sub(r"\(.*?\)", "", summary).strip()
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"{query} could refer to many things. Try being more specific, like: {e.options[0]}."
    except wikipedia.exceptions.PageError:
        return f"I couldn't find a Wikipedia page for {query}."
    except Exception as e:
        print(f"[Wikipedia Error] {type(e).__name__}: {e}")
        return "Sorry, I couldn't fetch that from Wikipedia right now."


# ==================================================
# TMDB — MOVIES & TV
# ==================================================
TMDB_TRIGGERS = ["movie", "film", "trending movies", "popular movies",
                 "top movies", "recommend a movie", "what should i watch",
                 "tv show", "series", "trending shows"]

def get_tmdb(cmd):
    if not TMDB_KEY:
        return "Movie info is not available. The TMDB API key is missing."

    base = "https://api.themoviedb.org/3"
    params = {"api_key": TMDB_KEY, "language": "en-US"}

    try:
        # Search for a specific movie
        for trigger in ["search movie ", "find movie ", "movie about ", "film about "]:
            if trigger in cmd:
                query = cmd.split(trigger, 1)[1].strip()
                r = requests.get(f"{base}/search/movie",
                                 params={**params, "query": query}, timeout=10)
                results = r.json().get("results", [])
                if not results:
                    return f"I couldn't find a movie matching {query}."
                m = results[0]
                title   = m.get("title", "Unknown")
                year    = m.get("release_date", "")[:4]
                rating  = m.get("vote_average", 0)
                overview = m.get("overview", "No description available.")
                overview = overview[:120] + "..." if len(overview) > 120 else overview
                return f"{title} ({year}) — Rated {rating}/10. {overview}"

        # Trending movies
        if any(t in cmd for t in ["trending movie", "popular movie", "top movie",
                                   "what should i watch", "recommend a movie"]):
            r = requests.get(f"{base}/trending/movie/week", params=params, timeout=10)
            results = r.json().get("results", [])[:3]
            if not results:
                return "I couldn't find trending movies right now."
            reply = "Here are the trending movies this week. "
            for i, m in enumerate(results, 1):
                reply += f"{i}. {m['title']} ({m.get('release_date','')[:4]}), rated {m.get('vote_average',0)}/10. "
            return reply.strip()

        # Trending TV shows
        if any(t in cmd for t in ["trending show", "popular show", "tv show", "series"]):
            r = requests.get(f"{base}/trending/tv/week", params=params, timeout=10)
            results = r.json().get("results", [])[:3]
            if not results:
                return "I couldn't find trending shows right now."
            reply = "Here are the trending TV shows this week. "
            for i, s in enumerate(results, 1):
                reply += f"{i}. {s['name']} ({s.get('first_air_date','')[:4]}), rated {s.get('vote_average',0)}/10. "
            return reply.strip()

        return None

    except requests.exceptions.Timeout:
        return "Sorry, the movie service took too long to respond."
    except Exception as e:
        print(f"[TMDB Error] {type(e).__name__}: {e}")
        return "Sorry, I couldn't fetch movie info right now."


# ==================================================
# DATE & TIME
# ==================================================
DATETIME_TRIGGERS = ["what time", "what's the time", "current time",
                     "what day", "what's today", "today's date",
                     "what date", "current date", "what year", "what month"]

def get_datetime(cmd):
    now = datetime.now()
    if any(t in cmd for t in ["time", "clock"]):
        return f"The current time is {now.strftime('%I:%M %p')}."
    if any(t in cmd for t in ["date", "today", "day", "month", "year"]):
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    return f"It is {now.strftime('%A, %B %d, %Y')} and the time is {now.strftime('%I:%M %p')}."


# ==================================================
# CALCULATOR
# ==================================================
CALC_TRIGGERS = ["calculate", "what is", "compute", "how much is",
                 "what's", "solve", "math"]

# Safe math symbols allowed in eval
_SAFE_NAMES = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
_SAFE_NAMES.update({"abs": abs, "round": round})

def safe_eval(expr):
    """Evaluate a math expression safely."""
    # Only allow numbers and basic operators
    cleaned = re.sub(r"[^0-9+\-*/().%^ ]", "", expr).strip()
    cleaned = cleaned.replace("^", "**")  # support ^ for power
    if not cleaned:
        return None
    try:
        result = eval(cleaned, {"__builtins__": {}}, _SAFE_NAMES)
        return result
    except Exception:
        return None

def get_calculation(cmd):
    # Strip trigger words to get the expression
    expr = cmd
    for trigger in ["calculate ", "compute ", "what is ", "how much is ",
                    "what's ", "solve ", "math "]:
        if trigger in expr:
            expr = expr.split(trigger, 1)[1].strip()
            break

    # Check if it looks like a math expression
    if not re.search(r"[\d]", expr):
        return None

    result = safe_eval(expr)
    if result is None:
        return None

    # Clean up result display
    if isinstance(result, float) and result.is_integer():
        result = int(result)

    return f"The answer is {result}."


# ==================================================
# MAIN ACTION HANDLER
# ==================================================
def perform_action(command):
    """
    Check if command matches known actions.
    Returns confirmation string if handled, None if not.
    """
    cmd = command.lower().strip()

    # ─────────────────────────────────────────
    # DATE & TIME
    # ─────────────────────────────────────────
    if any(t in cmd for t in DATETIME_TRIGGERS):
        return get_datetime(cmd)

    # ─────────────────────────────────────────
    # CALCULATOR
    # ─────────────────────────────────────────
    if any(t in cmd for t in CALC_TRIGGERS):
        result = get_calculation(cmd)
        if result:
            return result

    # ─────────────────────────────────────────
    # WEATHER
    # ─────────────────────────────────────────
    if any(t in cmd for t in WEATHER_TRIGGERS):
        return get_weather(cmd)

    # ─────────────────────────────────────────
    # NEWS
    # ─────────────────────────────────────────
    if any(t in cmd for t in NEWS_TRIGGERS):
        return get_news(cmd)

    # ─────────────────────────────────────────
    # TMDB — MOVIES & TV
    # ─────────────────────────────────────────
    if any(t in cmd for t in TMDB_TRIGGERS):
        result = get_tmdb(cmd)
        if result:
            return result

    # ─────────────────────────────────────────
    # PERSONAL MEMORY
    # ─────────────────────────────────────────
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
        # Fall through to Wikipedia
        result = get_wikipedia(cmd)
        if result:
            return result

    if "what do you know about me" in cmd or "show personal memory" in cmd:
        memories = get_all_memory()
        if not memories:
            return "I don't know anything about you yet."
        result = "Here is what I know about you. "
        for key, value in memories:
            result += f"{key} is {value}. "
        return result

    # ─────────────────────────────────────────
    # WIKIPEDIA
    # ─────────────────────────────────────────
    if any(t in cmd for t in ["tell me about ", "wikipedia ", "wiki "]):
        return get_wikipedia(cmd)

    # ─────────────────────────────────────────
    # YOUTUBE
    # ─────────────────────────────────────────
    if cmd.startswith("play "):
        search = cmd.replace("play", "", 1).strip()
        webbrowser.open("https://www.youtube.com/results?search_query=" + quote(search))
        return f"Playing {search} on YouTube"

    # ─────────────────────────────────────────
    # OPEN WEBSITES
    # ─────────────────────────────────────────
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

    # ─────────────────────────────────────────
    # SCREEN VISION (server-safe)
    # ─────────────────────────────────────────
    if "what is on my screen" in cmd or "read screen" in cmd:
        return read_screen_text()

    if "read this error" in cmd or "check error" in cmd:
        return detect_error()

    # ─────────────────────────────────────────
    # DESKTOP ACTIONS (local only — no-ops on server)
    # ─────────────────────────────────────────
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
