import uuid, os, httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Query
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from controller import DebateController
from adapters import get_adapter
from schemas import DebateConfig
from logger import log_debate
from dotenv import load_dotenv

# ───────────────────────────────
#  Load environment
# ───────────────────────────────
load_dotenv()

app = FastAPI(title="AI Debate Arena — Tribunal Edition")
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root():
    return {
        "message": "AI Debate Arena is running. Visit /static/index.html for the web UI."
    }


# ────────────────────────────────────────────
#  List available models per provider
# ────────────────────────────────────────────
@app.get("/api/models")
async def list_models(provider: str | None = Query(None)):
    """
    Returns available models per provider.
    For Ollama, fetches them live from the daemon defined in OLLAMA_HOST.
    For others, provides static defaults.
    """
    try:
        # ── Ollama dynamic discovery ─────────────────────────────────────
        if provider and provider.lower() == "ollama":
            base = os.getenv("OLLAMA_HOST", "http://localhost:11434")
            async with httpx.AsyncClient(timeout=5.0) as c:
                r = await c.get(f"{base}/api/tags")
                r.raise_for_status()
                data = r.json()
                models = [m["name"] for m in data.get("models", [])]
                return JSONResponse({"models": models})

        # ── Static provider → model map ──────────────────────────────────
        mapping = {
            "openai":   ["gpt-4o-mini", "gpt-4-turbo"],
            "groq":     ["mixtral-8x7b", "llama3-70b"],
            "mistral":  ["mistral-small", "mistral-medium"],
            "anthropic": ["claude-3-haiku", "claude-3-sonnet"],
            "ollama":   [],  # handled dynamically above
        }

        if provider:
            return JSONResponse({"models": mapping.get(provider.lower(), [])})
        return JSONResponse(mapping)

    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ────────────────────────────────────────────
#  WebSocket Debate Handler
# ────────────────────────────────────────────
@app.websocket("/ws/debate")
async def debate_endpoint(
    ws: WebSocket,
    topic: str = Query(..., max_length=500),
    rounds: int = Query(6, ge=1, le=30),
    # Side A
    provider_a: str = Query("ollama"),
    model_a: str = Query("llama3:latest"),
    # Side B
    provider_b: str = Query("openai"),
    model_b: str = Query("gpt-4o-mini"),
    # Judge
    judge_provider: str = Query("anthropic"),
    judge_model: str = Query("claude-3-sonnet"),
):
    session_id = str(uuid.uuid4())[:8]
    await ws.accept()
    await ws.send_text(f"Session {session_id} | {rounds} rounds | Judge: {judge_model}\n\n")

    # Initialize adapters
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

    try:
        async for chunk in controller.run():
            full_transcript += chunk
            await ws.send_text(chunk)

        await ws.send_text("\n\nDebate saved to debates.db")
        log_debate(session_id, topic, full_transcript)

    except WebSocketDisconnect:
        print(f"[{session_id}] Client disconnected")
    except Exception as e:
        msg = f"\nSERVER ERROR: {e}"
        await ws.send_text(msg)
        full_transcript += msg
        log_debate(session_id, topic, full_transcript)
    finally:
        await ws.close()
