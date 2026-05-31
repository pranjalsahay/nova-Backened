"""
ai.py — Nova AI using Gemini (free tier)
Get your free key at: https://aistudio.google.com/app/apikey
"""

import os
import re
import google.generativeai as genai

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

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash",   # free, fast
    system_instruction="""You are Nova, a smart helpful AI voice assistant.
Keep responses short — maximum 2 to 4 sentences.
Speak naturally. No markdown. Friendly and confident."""
)

# ==================================================
# IMAGE GENERATION — disabled without OpenAI
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

        # Build Gemini-format history
        history = []
        if conversation_history:
            for msg in conversation_history:
                role = "user" if msg["role"] == "user" else "model"
                history.append({"role": role, "parts": [msg["content"]]})

        chat = model.start_chat(history=history)
        response = chat.send_message(prompt)

        reply = response.text

        # Strip markdown (voice doesn't need it)
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
