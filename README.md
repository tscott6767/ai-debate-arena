# ⚔️ AI Debate Arena — Tribunal Edition

AI Debate Arena is a **FastAPI‑based real‑time debate simulator** that lets multiple LLMs (via Ollama or OpenAI‑compatible APIs) argue any topic in a live browser UI.  
It streams tokens as they’re generated and concludes each round with an optional **AI Judge** scoring panel.

---

## 🧠 Features

- 💬 Two (models) debate in real time — fully streamed to the browser  
- 🧑‍⚖️ Third model acts as a judge with logical & persuasion scores  
- 🔄 Supports Ollama (local LLMs), OpenAI, Groq, LM Studio, etc.  
- 💾 Transcripts automatically logged to SQLite (`debates.db`)  
- 🌐 Simple browser interface with model dropdown selection  
- ⚙️ Configurable via `.env` environment file  

---

## ⚡️ Quick Start (Local Ollama)

```bash
# 1. Clone the repo
git clone https://github.com/<youruser>/ai-debate-arena.git
cd ai-debate-arena

# 2. Create & activate a virtual environment
python3 -m venv venv
source venv/bin/activate     # (Windows: venv\Scripts\activate)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Copy the environment template
cp .env.example .env
# (default assumes Ollama runs locally on port 11434)

# 5. Launch Ollama in another terminal
ollama serve

# 6. Start the debate arena
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

Then open
👉 http://localhost:8000/static/index.html

🌐 Using a Remote Ollama Server
If your LLMs run on another machine:
1. Edit .env on the FastAPI host:
OLLAMA_HOST=http://<remote‑ip>:11434
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000

2. Make sure Ollama is listening on that IP and firewall allows TCP 11434.
3. Restart the FastAPI server → models from that server will appear automatically.

🖥️ UI Guide



Section
Purpose




Topic Field
Enter any debate subject


Side A / Side B / Judge
Choose models (populated from /api/models)


START DEBATE
Begins a real‑time exchange between the chosen models


Log Window
Streams live tokens and the judge’s final verdict



All debates are stored in debates.db with timestamps.
To view saved logs:
sqlite3 debates.db "SELECT id, ts, topic, length(transcript) FROM debates;"


⚙️ Configuration (.env)
# Edit and rename .env.example → .env
OLLAMA_HOST=http://localhost:11434
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
DEBATE_DB_PATH=debates.db


🧭 REST Endpoints



HTTP Method
Route
Description




GET
/
Health‑check / welcome message


GET
/api/models
Returns available Ollama models


WS
/ws/debate
Bi‑directional WebSocket stream for debates




🧑‍💻 Development Tips

Test model connectivity manually:
curl http://<OLLAMA_HOST>/api/tagscurl -X POST http://<OLLAMA_HOST>/api/chat \   -H "Content-Type: application/json" \   -d '{"model":"llama3:latest","messages":[{"role":"user","content":"Hello"}]}'

Restart uvicorn after editing .py files (CTRL+C → rerun).
Use python -m py_compile *.py to validate syntax before committing.


🛡️ Security Notes

Never commit your personal .env. Commit only .env.example.
If exposing publicly, proxy through NGINX with HTTPS (Let’s Encrypt) or Cloudflare Tunnel.
Use Proxmox LXC or Docker for process isolation.


🧱 Folder Structure
ai-debate-arena/
│
├── adapters.py       # model interfaces (Ollama / OpenAI)
├── controller.py     # debate orchestrator
├── judge.py          # judge logic
├── logger.py         # SQLite logger
├── main.py           # FastAPI entrypoint
├── schemas.py        # Pydantic classes
├── static/           # web UI (index.html + JS)
├── .env.example
├── debates.db
└── venv/             # virtual environment (local)


🧪 Known Tested Setups

✅ Ubuntu 22.04 LXC on Proxmox
✅ Ollama 0.1.40 (remote & local)
✅ Python 3.10 → 3.12
✅ FastAPI + Uvicorn + httpx


📜 License
MIT License © 2025 Antony L Scott
See LICENSE for full text.

❤️ Contributing
1. Fork this repo
2. Create a feature branch  →  git checkout -b feature/some‑idea
3. Commit changes
4. Push and open a Pull Request

### ✨ Example Topics

Should AI be open source?
Can machines ever truly understand consciousness?
Is time an illusion?



"The best way to test an idea is to argue with an equal."
— AI Debate Arena Team

