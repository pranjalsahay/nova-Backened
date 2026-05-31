import os
import sys
import webbrowser
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


def _open_app(win_cmd, mac_cmd, linux_cmd):
    """Open native app cross-platform."""
    if sys.platform == "win32":
        os.system(win_cmd)
    elif sys.platform == "darwin":
        os.system(mac_cmd)
    else:
        os.system(linux_cmd)


def perform_action(command):
    """
    Check if command matches known actions.
    Returns confirmation string if handled, None if not.
    """
    cmd = command.lower().strip()

    # ─────────────────────────────────────────
    # PERSONAL MEMORY
    # ─────────────────────────────────────────

    if cmd.startswith("remember "):
        text = cmd.replace("remember", "", 1).strip()
        if " is " in text:
            key, value = text.split(" is ", 1)
            key = key.strip()
            value = value.strip()
            save_personal_memory(key, value)
            return f"I will remember that {key} is {value}"
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

    # ─────────────────────────────────────────
    # YOUTUBE
    # ─────────────────────────────────────────

    if cmd.startswith("play "):
        search = cmd.replace("play", "", 1).strip()
        webbrowser.open(
            "https://www.youtube.com/results?search_query=" + quote(search)
        )
        return f"Playing {search} on YouTube"

    # ─────────────────────────────────────────
    # OPEN WEBSITES
    # ─────────────────────────────────────────

    sites = {
        "open youtube":    "https://youtube.com",
        "open google":     "https://google.com",
        "open whatsapp":   "https://web.whatsapp.com",
        "open gmail":      "https://mail.google.com",
        "open chatgpt":    "https://chat.openai.com",
        "open github":     "https://github.com",
        "open netflix":    "https://netflix.com",
        "open twitter":    "https://twitter.com",
        "open instagram":  "https://instagram.com",
        "open reddit":     "https://reddit.com",
    }

    for phrase, url in sites.items():
        if phrase in cmd:
            webbrowser.open(url)
            return f"Opening {phrase.replace('open ', '').title()}"

    if cmd.startswith("search "):
        query = cmd.replace("search", "", 1).strip()
        webbrowser.open(
            "https://www.google.com/search?q=" + quote(query)
        )
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