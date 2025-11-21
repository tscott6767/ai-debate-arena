
# ⚔️ AI Debate Arena — Tribunal Edition (v2.1)

> **Multi‑model, real‑time AI debate framework**  
> Debate any two models live in your browser with an impartial AI Judge and full streaming transcripts.

---

## 🚀 Overview

AI Debate Arena lets any combination of language models (OpenAI, Groq, Mistral, Anthropic Claude, Ollama, LM Studio, etc.) argue topics in real time through a FastAPI server while a Judge model scores each round.

It now includes:

- 🎯 **Multi‑model adapters** (OpenAI, Groq, Mistral, Anthropic, Ollama, LM Studio)
- ⚖️ **AI Judge & Scoring**
- 💬 **WebSocket streaming** with live UI in the browser
- 🧠 **multi_battle_test.py** for connectivity testing
- ⚙️ **Dynamic .env configuration**
- 🪶 **UTF‑8‑safe adapters** (no more ASCII errors)
- 💾 Automatic SQLite logging (`debates.db`)
- 🌐 **FastAPI + HTML frontend** served from `/static/index.html`

---

## 🧩 Project Structure


ai-debate-arena/
├── adapters.py              # Provider adapters (OpenAI/Groq/Mistral/Ollama/etc.)
├── controller.py            # Debate loop + judge integration
├── judge.py                 # AI judge logic
├── logger.py                # SQLite transcript logger
├── main.py                  # FastAPI entrypoint / websocket server
├── schemas.py               # Pydantic models
├── multi_battle_test.py     # Connectivity/self-test script
├── static/
│   └── index.html           # Live debate front-end
├── .env.example             # Environment template (safe to commit)
├── .gitignore
├── README.md
└── LICENSE

---

## ⚙️ Installation & Setup

```bash
git clone https://github.com/tscott6767/ai-debate-arena.git
cd ai-debate-arena
python -m venv venv
source venv/bin/activate  # (or .\venv\Scripts\activate on Windows)
pip install -r requirements.txt


🔧 Environment Variables
Copy the template and fill in your keys:
cp .env.example .env
nano .env

Example .env.example contents:
OPENAI_API_KEY=sk-your_openai_key
GROQ_API_KEY=gsk-your_groq_key
MISTRAL_API_KEY=sk-your_mistral_key
ANTHROPIC_API_KEY=sk-ant_your_claude_key

OLLAMA_HOST=http://<your Ollama IP>:11434
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
DEBATE_DB_PATH=debates.db
DEBUG_MODE=false

Never commit .env files—only .env.example stays tracked.

🧠 Quick Start
1️⃣ Launch the server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

Visit http://localhost:8000/static/index.html
2️⃣ Run a local connectivity test
python multi_battle_test.py

If every provider shows ✅ First token, all your API keys and hosts are working.

⚔️ Web Interface

Enter your debate topic
Choose models for Side A and Side B
Select a judge model
Pick round count
Click Start Debate

Watch tokens stream live.
At the end, the judge provides a verdict, summary, and scoring table.

💾 Database Logging
Each debate session (topic + transcript + scores) is automatically saved to debates.db.
Location configurable via DEBATE_DB_PATH in .env.

🧰 Connectivity Test Details
multi_battle_test.py verifies all API integrations independently.
python multi_battle_test.py

Sample output:
🔍 Testing ollama  →  llama3:latest
✅ First token: Hello!

🔍 Testing openai  →  gpt-4o-mini
✅ First token: Hi there 😊

If you see 404s, update your OLLAMA_HOST to the correct daemon endpoint
(e.g. http://<your Ollama IP>:11434/api/chat vs /api/generate).

🔒 Best Practices



Do
Don’t




Keep .env private
Never commit real API keys


Commit .env.example only



Use isolated Python venv



Backup debates.db if needed





🧮 Troubleshooting



Symptom
Cause
Fix




404 @ /chat
Wrong endpoint
Update OllamaAdapter or OLLAMA_HOST


Unauthorized / api_key must be set
Missing keys
Fill .env and load via load_dotenv()


ascii codec can't encode
Old adapters version
Replace with UTF‑8‑safe adapters.py (v2.1)


Connection refused @ 11434
Ollama daemon off
Start ollama serve or fix LAN IP




🧾 Version Control & GitHub Workflow
Push new changes
git add main.py adapters.py multi_battle_test.py README.md static/index.html .env.example
git commit -m "Update core files and environment template"
git push origin main

Tag a release
git tag -a v2.1 -m "Tribunal Edition stable release"
git push origin v2.1


🧱 Upcoming Features

🏆 Tournament brackets (auto play‑offs)
👥 Audience voting UI
🎙️ Voice narration via ElevenLabs / XTTS
🌐 Public gallery of past debates
🔐 User accounts + API keys per user


🤝 Contributing
Pull requests are welcome!
For major changes, open an issue first to discuss what you’d like to modify.

Fork this repo
Create your feature branch:
git checkout -b feature/amazing-update
Commit and push it
Open a PR against main


🪪 License
Released under the MIT License.
See LICENSE for details.

❤️ Acknowledgements
Thanks to the open‑source LLM community & contributors who test, troubleshoot, and push AI debates into the big arena.


