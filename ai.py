"""
ai.py — Nova AI using Grok (xAI)
Get your free key at: https://console.x.ai
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

XAI_API_KEY = os.getenv("XAI_API_KEY")

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

        # Build messages list
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]

        if conversation_history:
            for msg in conversation_history:
                messages.append({
                    "role": msg["role"],  # "user" or "assistant"
                    "content": msg["content"]
                })

        # Add current user message
        messages.append({"role": "user", "content": prompt})

        response = requests.post(
            "https://api.x.ai/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {XAI_API_KEY}"
            },
            json={
                "model": "grok-3-mini",
                "messages": messages,
                "max_tokens": 300
            }
        )

        data = response.json()
        reply = data["choices"][0]["message"]["content"] or ""

        # Strip markdown formatting (voice doesn't need it)
        reply = re.sub(r"[*_`#]", "", reply)
        reply = re.sub(r"\n+", " ", reply)
        return reply.strip()

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
