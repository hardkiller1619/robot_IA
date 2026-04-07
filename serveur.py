from flask import Flask, request, jsonify, send_file
import openai
import json

app = Flask(__name__)
openai.api_key = "TA_CLE_API"

memory = [
    {"role": "system", "content": "Tu es un robot physique sympa qui parle et bouge."}
]

# =========================
# CHAT + IA
# =========================
@app.route("/chat", methods=["POST"])
def chat():

    user_text = request.json["text"]
    memory.append({"role": "user", "content": user_text})

    prompt = """
    Réponds naturellement.

    Actions possibles:
    ARM_UP, ARM_DOWN, CLAW_OPEN, CLAW_CLOSE, BASE_LEFT, BASE_RIGHT, NONE

    Format JSON:
    {
      "response": "...",
      "action": "..."
    }
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=memory + [{"role": "system", "content": prompt}]
    )

    content = response.choices[0].message.content

    try:
        data = json.loads(content)
    except:
        data = {"response": "Je n'ai pas compris", "action": "NONE"}

    memory.append({"role": "assistant", "content": data["response"]})

    return jsonify(data)

# =========================
# TEXT TO SPEECH
# =========================
@app.route("/tts", methods=["POST"])
def tts():
    text = request.json["text"]

    speech = openai.audio.speech.create(
        model="gpt-4o-mini-tts",
        voice="alloy",
        input=text
    )

    file_path = "speech.wav"
    with open(file_path, "wb") as f:
        f.write(speech.content)

    return send_file(file_path, mimetype="audio/wav")

app.run(host="0.0.0.0", port=5000)