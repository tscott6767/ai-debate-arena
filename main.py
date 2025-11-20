# main.py
"""
main.py — FastAPI entrypoint for the AI Debate Arena.

Serves the static web interface, lists available models, and coordinates
real‑time debate sessions between models via WebSocket.
"""

import uuid
import os
import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.staticfiles import StaticFiles
from controller import DebateController
from adapters import get_adapter
from schemas import DebateConfig
from logger import log_debate

# ─── Load environment variables ───────────────────────────────────────────────
load_dotenv()

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))

# ─── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(title="AI Debate Arena — Tribunal Edition")
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Root Ping ────────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {"message": "AI Debate Arena is running. Open /static/index.html"}


# ─── List Available Models (Ollama) ───────────────────────────────────────────
@app.get("/api/models")
async def list_models(provider: str = "ollama", host: str = OLLAMA_HOST):
    """
    Return available model names from the Ollama daemon (configurable via OLLAMA_HOST).
    Extendable later to support other providers.
    """
    if provider != "ollama":
        return {
            "provider": provider,
            "models": [],
            "error": "Only 'ollama' supported currently",
        }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(f"{host}/api/tags")
            r.raise_for_status()
            data = r.json()
            models = [m["name"] for m in data.get("models", [])]
        return {"provider": provider, "models": sorted(models)}
    except Exception as e:
        return {"provider": provider, "models": [], "error": str(e)}


# ─── Debate WebSocket ─────────────────────────────────────────────────────────
@app.websocket("/ws/debate")
async def debate_endpoint(
    ws: WebSocket,
    topic: str = Query(..., max_length=500),
    rounds: int = Query(6, ge=1, le=30),
    # ─ Side A
    provider_a: str = Query("ollama"),
    model_a: str = Query("llama3:latest"),
    # ─ Side B
    provider_b: str = Query("ollama"),
    model_b: str = Query("qwen3:8b"),
    # ─ Judge
    judge_provider: str = Query("ollama"),
    judge_model: str = Query("llama3:latest"),
):
    session_id = str(uuid.uuid4())[:8]
    await ws.accept()
    await ws.send_text(
        f"Session {session_id} | {rounds} rounds | Topic: {topic}\n\n"
    )

    # Build debate configuration
    config = DebateConfig(
        topic=topic,
        rounds=rounds,
        adapter_a=get_adapter(provider_a, model_a),
        adapter_b=get_adapter(provider_b, model_b),
        judge_provider=judge_provider,
        judge_model=judge_model,
    )

    controller = DebateController(config, session_id)
    full_transcript_parts: list[str] = []

    # ─── Debate Loop ───────────────────────────────────────────────
    try:
        async for chunk in controller.run():
            await ws.send_text(chunk)
            full_transcript_parts.append(chunk)

        transcript = "".join(full_transcript_parts)
        log_debate(session_id, topic, transcript)
        await ws.send_text("\n\nDebate saved to debates.db\n")

    except WebSocketDisconnect:
        print(f"[{session_id}] Client disconnected")
        transcript = "".join(full_transcript_parts) + "\n\n[CLIENT DISCONNECTED]"
        log_debate(session_id, topic, transcript)

    except Exception as e:
        err = f"\nSERVER ERROR: {e}"
        await ws.send_text(err)
        transcript = "".join(full_transcript_parts) + err
        log_debate(session_id, topic, transcript)

    finally:
        await ws.close()
