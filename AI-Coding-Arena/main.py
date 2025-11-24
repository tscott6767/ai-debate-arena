import uuid
import os
import secrets
import httpx
import sqlite3
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from controller import DebateController
from adapters import get_adapter
from schemas import DebateConfig
from logger import log_debate, DB_PATH
from dotenv import load_dotenv
from utils.continuation import get_last_debate, build_continuation_prompt

# -------------------------------------------------------------------
# Startup preload
# -------------------------------------------------------------------
load_dotenv()

TOPIC_CACHE: dict[str, str] = {}   # short-term storage for large topics

app = FastAPI(title="AI Debate Arena")

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {"message": "AI Debate Arena running – open /static/index.html"}


# -------------------------------------------------------------------
# List models
# -------------------------------------------------------------------
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
            "openai": ["gpt-4o-mini", "gpt-4-turbo"],
            "groq": ["llama3-70b-8192", "mixtral-8x7b-32768"],
            "anthropic": ["claude-3-sonnet-20240229", "claude-3-haiku-20240307"],
            "mistral": ["mistral-small", "mistral-medium"],
            "ollama": [],
        }
        if provider:
            return JSONResponse({"models": mapping.get(provider.lower(), [])})
        return JSONResponse(mapping)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# -------------------------------------------------------------------
# Continuation builder  (unchanged)
# -------------------------------------------------------------------
@app.get("/api/continuation")
def generate_continuation_round(limit: int = 1, round_no: int = 13):
    last_rows = get_last_debate(limit)
    if not last_rows:
        return {"error": "No debates found."}

    if isinstance(last_rows, list):
        past_text = "\n\n".join([r[4] for r in reversed(last_rows)])
    else:
        past_text = last_rows[4]

    new_task = (
        "Enhance the previous code into a complete SAF directory manager "
        "with CRUD features using ACTION_OPEN_DOCUMENT_TREE."
    )
    topic = build_continuation_prompt(past_text, new_task, round_no)
    return {"topic": topic, "length": len(topic)}


# -------------------------------------------------------------------
# Register topic → returns short token
# -------------------------------------------------------------------
@app.post("/api/register_topic")
async def register_topic(payload: dict):
    topic_text = payload.get("topic")
    if not topic_text:
        return {"error": "missing topic"}
    token = secrets.token_hex(8)
    TOPIC_CACHE[token] = topic_text
    return {"token": token, "length": len(topic_text)}


# -------------------------------------------------------------------
# WebSocket debate
# -------------------------------------------------------------------
@app.websocket("/ws/debate")
async def debate_endpoint(
    ws: WebSocket,
    topic: str | None = Query(None),
    token: str | None = Query(None),
    rounds: int = Query(6, ge=1, le=30),
    provider_a: str | None = Query(None),
    model_a: str | None = Query(None),
    provider_b: str | None = Query(None),
    model_b: str | None = Query(None),
    judge_provider: str | None = Query(None),
    judge_model: str | None = Query(None),
):
    # --- retrieve large topic from cache if token provided
    if not topic and token:
        topic = TOPIC_CACHE.pop(token, "")
    if not topic:
        await ws.close(code=4000)
        return

    print("TOPIC length:", len(topic))
    print(topic[:500])

    await ws.accept()
    session_id = str(uuid.uuid4())[:8]

    provider_a = provider_a or "ollama"
    model_a = model_a or "llama3:latest"
    provider_b = provider_b or "ollama"
    model_b = model_b or "qwen3-coder:30b"
    judge_provider = judge_provider or "ollama"
    judge_model = judge_model or "qwen3-coder:30b"

    await ws.send_text(
        f"Session {session_id} | {rounds} rounds | Judge: {judge_model}\n\n"
    )

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

        await ws.send_text("\n\nDebate saved to debates.db")
        log_debate(session_id, topic, full_transcript)

    except WebSocketDisconnect:
        print(f"[{session_id}] Client disconnected")
    except Exception as e:
        error_msg = f"\nSERVER ERROR: {e}\n"
        await ws.send_text(error_msg)
        log_debate(session_id, topic, error_msg)
    finally:
        await ws.close()
