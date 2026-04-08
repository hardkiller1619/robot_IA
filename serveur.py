from flask import Flask, request, jsonify, send_file, render_template_string
import openai
import json
import os
import tempfile

app = Flask(__name__)
openai.api_key = os.environ.get("OPENAI_API_KEY")

memory = [
    {"role": "system", "content": "Tu es un robot physique sympa qui parle et bouge."}
]

# Action en attente pour le robot (depuis la page web)
pending_action = {"action": "NONE"}

# =========================
# PAGE WEB DE CONTRÔLE
# =========================
@app.route("/")
def index():
    return render_template_string('''
<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>🤖 Contrôle Robot</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Segoe UI', sans-serif;
      background: #0f0f1a;
      color: #fff;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 30px 20px;
    }
    h1 { font-size: 2rem; margin-bottom: 5px; }
    .subtitle { color: #888; margin-bottom: 30px; font-size: 0.9rem; }

    .status {
      background: #1a1a2e;
      border: 1px solid #333;
      border-radius: 12px;
      padding: 15px 25px;
      margin-bottom: 30px;
      text-align: center;
      width: 100%;
      max-width: 400px;
    }
    .status span { color: #4ade80; font-weight: bold; }

    .grid {
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 12px;
      width: 100%;
      max-width: 400px;
      margin-bottom: 20px;
    }
    .btn {
      background: #1e1e3f;
      border: 2px solid #3b3b6b;
      border-radius: 12px;
      color: #fff;
      font-size: 1.1rem;
      padding: 20px 10px;
      cursor: pointer;
      transition: all 0.2s;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 6px;
    }
    .btn:hover { background: #2e2e5f; border-color: #6c63ff; transform: scale(1.05); }
    .btn:active { transform: scale(0.97); }
    .btn.active { background: #6c63ff; border-color: #9d96ff; }
    .btn span { font-size: 0.75rem; color: #aaa; }
    .btn.empty { background: transparent; border: none; cursor: default; }

    .chat-section {
      width: 100%;
      max-width: 400px;
      margin-top: 10px;
    }
    .chat-section h2 { margin-bottom: 12px; font-size: 1.1rem; color: #aaa; }
    .chat-box {
      background: #1a1a2e;
      border: 1px solid #333;
      border-radius: 12px;
      padding: 15px;
      height: 180px;
      overflow-y: auto;
      margin-bottom: 12px;
      font-size: 0.9rem;
      line-height: 1.5;
    }
    .msg-robot { color: #6c63ff; margin-bottom: 8px; }
    .msg-user  { color: #4ade80; margin-bottom: 8px; text-align: right; }

    .input-row {
      display: flex;
      gap: 10px;
    }
    .input-row input {
      flex: 1;
      background: #1a1a2e;
      border: 1px solid #333;
      border-radius: 10px;
      color: #fff;
      padding: 12px 15px;
      font-size: 0.95rem;
      outline: none;
    }
    .input-row input:focus { border-color: #6c63ff; }
    .input-row button {
      background: #6c63ff;
      border: none;
      border-radius: 10px;
      color: #fff;
      padding: 12px 18px;
      cursor: pointer;
      font-size: 1rem;
      transition: background 0.2s;
    }
    .input-row button:hover { background: #9d96ff; }

    .notification {
      position: fixed;
      bottom: 20px;
      left: 50%;
      transform: translateX(-50%);
      background: #6c63ff;
      color: white;
      padding: 10px 20px;
      border-radius: 20px;
      font-size: 0.9rem;
      opacity: 0;
      transition: opacity 0.3s;
    }
    .notification.show { opacity: 1; }
  </style>
</head>
<body>
  <h1>🤖 Robot IA</h1>
  <p class="subtitle">Panneau de contrôle</p>

  <div class="status">
    Statut : <span id="status">En ligne ✅</span>
  </div>

  <!-- CONTRÔLE BRAS -->
  <p style="color:#888; margin-bottom:10px; font-size:0.85rem; align-self:flex-start; max-width:400px;">💪 BRAS</p>
  <div class="grid">
    <div class="btn empty"></div>
    <div class="btn" onclick="action('ARM_UP')">⬆️<span>Bras haut</span></div>
    <div class="btn empty"></div>
    <div class="btn" onclick="action('BASE_LEFT')">⬅️<span>Gauche</span></div>
    <div class="btn empty"></div>
    <div class="btn" onclick="action('BASE_RIGHT')">➡️<span>Droite</span></div>
    <div class="btn empty"></div>
    <div class="btn" onclick="action('ARM_DOWN')">⬇️<span>Bras bas</span></div>
    <div class="btn empty"></div>
  </div>

  <!-- CONTRÔLE PINCE -->
  <p style="color:#888; margin-bottom:10px; font-size:0.85rem; align-self:flex-start; max-width:400px; margin-top:10px;">🦾 PINCE</p>
  <div class="grid" style="max-width:400px;">
    <div class="btn" onclick="action('CLAW_OPEN')">🤲<span>Ouvrir</span></div>
    <div class="btn empty"></div>
    <div class="btn" onclick="action('CLAW_CLOSE')">✊<span>Fermer</span></div>
  </div>

  <!-- CHAT -->
  <div class="chat-section">
    <h2>💬 Envoyer un message</h2>
    <div class="chat-box" id="chatBox">
      <div class="msg-robot">🤖 Bonjour ! Je suis prêt.</div>
    </div>
    <div class="input-row">
      <input type="text" id="msgInput" placeholder="Dis quelque chose..." onkeydown="if(event.key==='Enter') sendMsg()" />
      <button onclick="sendMsg()">Envoyer</button>
    </div>
  </div>

  <div class="notification" id="notif"></div>

  <script>
    function notify(msg) {
      const n = document.getElementById('notif');
      n.textContent = msg;
      n.classList.add('show');
      setTimeout(() => n.classList.remove('show'), 2000);
    }

    async function action(name) {
      const btns = document.querySelectorAll('.btn');
      btns.forEach(b => b.classList.remove('active'));
      event.currentTarget.classList.add('active');
      setTimeout(() => event.currentTarget.classList.remove('active'), 500);

      await fetch('/action', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: name})
      });
      notify('Action : ' + name);
    }

    async function sendMsg() {
      const input = document.getElementById('msgInput');
      const text = input.value.trim();
      if (!text) return;

      const box = document.getElementById('chatBox');
      box.innerHTML += `<div class="msg-user">👤 ${text}</div>`;
      input.value = '';
      box.scrollTop = box.scrollHeight;

      const res = await fetch('/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({text: text})
      });
      const data = await res.json();
      box.innerHTML += `<div class="msg-robot">🤖 ${data.response}</div>`;
      box.scrollTop = box.scrollHeight;
    }
  </script>
</body>
</html>
    ''')

# =========================
# ACTION DEPUIS PAGE WEB
# =========================
@app.route("/action", methods=["POST"])
def set_action():
    global pending_action
    pending_action = request.json
    return jsonify({"ok": True})

@app.route("/getaction", methods=["GET"])
def get_action():
    global pending_action
    action = pending_action.copy()
    pending_action = {"action": "NONE"}  # Reset après lecture
    return jsonify(action)

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

# =========================
# SPEECH TO TEXT
# =========================
@app.route("/stt", methods=["POST"])
def stt():
    if "audio" not in request.files:
        return jsonify({"error": "Pas de fichier audio"}), 400

    audio_file = request.files["audio"]
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        audio_file.save(tmp.name)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="fr"
            )
        text = transcript.text.lower().strip()
        return jsonify({"text": text})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        os.remove(tmp_path)

# =========================
# POINT D'ENTRÉE
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
