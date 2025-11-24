# main.py — AI Debate Arena (FINAL, UNBREAKABLE VERSION)
import uuid
import os
import httpx
import sqlite3                     ### NEW: for on-demand local query
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from controller import DebateController
from adapters import get_adapter
from schemas import DebateConfig
from logger import log_debate, DB_PATH
from dotenv import load_dotenv

### NEW: import the continuation helpers
from utils.continuation import get_last_debate, build_continuation_prompt

last = get_last_debate()
if last:
    past_transcript = last[4]  # fifth column is transcript text
    new_task = (
        "Expand the previous SAF single-file picker into a complete folder manager "
        "using ACTION_OPEN_DOCUMENT_TREE with create/read/write/delete support."
    )
    topic = build_continuation_prompt(past_transcript, new_task, round_no=13)
else:
    topic = "Round 13 — Start a new debate: implement a full SAF manager."

load_dotenv()

app = FastAPI(title="AI Debate Arena — Tribunal Edition")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {
        "message": "AI Debate Arena is running. Visit /static/index.html for the web UI."
    }


# ────────────────────────────────────────────
# Dynamic model listing (Ollama live + static fallbacks)
# ────────────────────────────────────────────
@app.get("/api/models")
async def list_models(provider: str | None = Query(None)):
    try:
        if provider and provider.lower() == "ollama":
            base = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            async with httpx.AsyncClient(timeout=8.0) as client:
                r = await client.get(f"{base}/api/tags")
                r.raise_for_status()
                data = r.json()
                models = [m["name"] for m in data.get("models", [])]
                return JSONResponse({"models": models})

        mapping = {
            "openai": ["gpt-4o-mini", "gpt-4-turbo", "gpt-4o"],
            "groq": ["llama3-70b-8192", "mixtral-8x7b-32768", "gemma-7b-it"],
            "anthropic": ["claude-3-haiku-20240307", "claude-3-sonnet-20240229"],
            "mistral": ["mistral-small", "mistral-medium"],
            "ollama": [],
        }
        if provider:
            return JSONResponse({"models": mapping.get(provider.lower(), [])})
        return JSONResponse(mapping)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ────────────────────────────────────────────
# NEW endpoint — build a continuation topic
# ────────────────────────────────────────────
@app.get("/api/continuation")
def generate_continuation_round(limit: int = 1, round_no: int = 13):
    """
    Returns a topic string that includes the latest N debate transcripts
    so the next run can 'build upon' previous work.
    Query parameters:
        limit  = number of rounds to pull from history
        round_no = label for the next round
    Example:
        http://localhost:8000/api/continuation?limit=1&round_no=13
    """
    last_rows = get_last_debate(limit)
    if not last_rows:
        return {"error": "No debates found."}

    # Join multiple transcripts if limit > 1
    if isinstance(last_rows, list):
        past_text = "\n\n".join(r[4] for r in reversed(last_rows))
    else:
        past_text = last_rows[4]

    new_task = (
        "Enhance the previous code into a complete SAF directory manager "
        "using ACTION_OPEN_DOCUMENT_TREE with full CRUD and persistable permissions."
    )
    topic = build_continuation_prompt(past_text, new_task, round_no)
    return {"topic": topic}


# ────────────────────────────────────────────
# WebSocket Debate — SAFE, DYNAMIC, UNBREAKABLE
# ────────────────────────────────────────────
@app.websocket("/ws/debate")
async def debate_endpoint(
    ws: WebSocket,
    topic: str = Query(..., max_length=3000),             # extended size for continuation prompts
    rounds: int = Query(6, ge=1, le=30),
    provider_a: str | None = Query(None),
    model_a: str | None = Query(None),
    provider_b: str | None = Query(None),
    model_b: str | None = Query(None),
    judge_provider: str | None = Query(None),
    judge_model: str | None = Query(None),
):
    await ws.accept()
    session_id = str(uuid.uuid4())[:8]

    provider_a = provider_a or "ollama"
    model_a = model_a or "llama3:latest"
    provider_b = provider_b or "ollama"
    model_b = model_b or "qwen2"
    judge_provider = judge_provider or "ollama"
    judge_model = judge_model or "qwen3-coder:30b"

    await ws.send_text(f"Session {session_id} | {rounds} rounds | Judge: {judge_model}\n\n")

    try:
        config = DebateConfig(
            topic=topic,
            rounds=rounds,
            adapter_a=get_adapter(provider_a, model_a),
            adapter_b=get_adapter(provider_b, model_b),
            judge_provider=judge_provider,
            judge_model=judge_model,
        )

        controller = DebateController(config, session_id)
        full_transcript = ""

        async for chunk in controller.run():
            full_transcript += chunk
            await ws.send_text(chunk)

        await ws.send_text("\n\nDebate saved to debates.db")
        log_debate(session_id, topic, full_transcript)

    except WebSocketDisconnect:
        print(f"[{session_id}] Client disconnected")
    except Exception as e:
        error_msg = f"\nSERVER ERROR: {e}\n"
        await ws.send_text(error_msg)
        full_transcript += error_msg
        log_debate(session_id, topic, full_transcript)
    finally:
        await ws.close()
