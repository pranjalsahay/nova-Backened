from flask import Flask, jsonify, request
from flask_cors import CORS

from state import assistant_state
from ai import ask_nova
from actions import perform_action

app = Flask(__name__)

# Replace "*" with your Vercel URL after deploying frontend
# e.g. CORS(app, origins=["https://nova-frontend.vercel.app"])
CORS(app)


@app.route("/")
def index():
    return jsonify({"message": "Nova backend is running."})


@app.route("/status")
def get_status():
    return jsonify(assistant_state)


@app.route("/command", methods=["POST"])
def command():
    data = request.json
    text = data.get("command", "")

    if not text:
        return jsonify({"response": "No command received."}), 400

    assistant_state["status"] = "Thinking"
    assistant_state["last_command"] = text

    action = perform_action(text)

    if action:
        response = action
    else:
        response = ask_nova(text)

    assistant_state["status"] = "Speaking"
    assistant_state["last_response"] = response

    return jsonify({"response": response})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)