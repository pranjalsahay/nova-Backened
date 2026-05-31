"""
ai.py — Nova AI using Groq (Free)
Get your free key at: https://console.groq.com
"""
import os
import re
import requests

# ==================================================
# LOAD .ENV (for local dev — Render uses env vars)
# ==================================================
def load_env():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if "=" in line and not line.startswith("#"):
                    key, _, val = line.partition("=")
                    os.environ[key.strip()] = val.strip()
load_env()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("[AI Error] GROQ_API_KEY is not set!")

# ==================================================
# SYSTEM PROMPT
# ==================================================
SYSTEM_PROMPT = """
You are Nova, a smart helpful AI voice assistant.
Rules:
Keep responses short.
Maximum 2 to 4 sentences.
Speak naturally.
No markdown.
Friendly and confident.
"""

# ==================================================
# IMAGE GENERATION — disabled
# ==================================================
DRAW_TRIGGERS = [
    "draw", "generate image", "create image",
    "make image", "paint", "sketch", "illustrate",
    "show me a picture of", "show me a drawing of"
]

def is_draw_request(command):
    return any(t in command.lower() for t in DRAW_TRIGGERS)

def generate_image(command):
    return "Image generation is not available right now. I can help with anything else!"

# ==================================================
# MAIN CHAT FUNCTION
# ==================================================
def ask_nova(prompt, conversation_history=None):
    try:
        if is_draw_request(prompt):
            return generate_image(prompt)

        if not GROQ_API_KEY:
            return "Sorry, my API key is missing. Please check the server configuration."

        # Build messages list
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })

        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GROQ_API_KEY}"
            },
            json={
                "model": "llama-3.3-70b-versatile",
                "messages": messages,
                "max_tokens": 300
            },
            timeout=15
        )

        data = response.json()
        print(f"[Groq Status] {response.status_code}")
        print(f"[Groq Response] {data}")

        if response.status_code != 200:
            error_msg = data.get("error", {}).get("message", "Unknown error")
            print(f"[AI Error] Groq API error: {error_msg}")
            return f"Sorry, I ran into an issue: {error_msg}"

        if "choices" not in data:
            print(f"[AI Error] No choices in response: {data}")
            return "Sorry, I got an unexpected response. Please try again."

        reply = data["choices"][0]["message"]["content"] or ""

        # Strip markdown formatting
        reply = re.sub(r"[*_`#]", "", reply)
        reply = re.sub(r"\n+", " ", reply)
        return reply.strip()

    except requests.exceptions.Timeout:
        print("[AI Error] Request timed out")
        return "Sorry, I took too long to respond. Please try again."

    except Exception as e:
        print(f"[AI Error] {type(e).__name__}: {e}")
        return "Sorry, something went wrong."

# ==================================================
# TEST MODE
# ==================================================
if __name__ == "__main__":
    print("\nNova started. Type 'exit' to quit.\n")
    while True:
        user = input("You: ")
        if user.lower() == "exit":
            break
        print("Nova:", ask_nova(user), "\n")
