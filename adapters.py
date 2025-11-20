# adapters.py
import json
import httpx
import os
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from dotenv import load_dotenv

# ─── Load environment variables ───────────────────────────────────
load_dotenv()

# Default fallbacks for local dev
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
FASTAPI_HOST = os.getenv("FASTAPI_HOST", "0.0.0.0")
FASTAPI_PORT = int(os.getenv("FASTAPI_PORT", "8000"))

# Cache of AsyncOpenAI clients (to avoid reconnect overhead)
_CLIENT_CACHE: dict[tuple, AsyncOpenAI] = {}


def get_client(base_url: str | None = None, api_key: str | None = None) -> AsyncOpenAI:
    """Return or create a cached AsyncOpenAI client."""
    key = (base_url or "", api_key or "")
    if key not in _CLIENT_CACHE:
        _CLIENT_CACHE[key] = AsyncOpenAI(base_url=base_url, api_key=api_key or "sk-")
    return _CLIENT_CACHE[key]


# ─────────────────────────────── Base Adapter ───────────────────────────────
class BaseAdapter(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def stream(self, messages: list[dict]):
        """Yield response chunks (tokens) asynchronously."""
        ...

    async def close(self):
        """Optional cleanup."""
        pass


# ─────────────────────────────── OpenAI‑Compatible Provider ───────────────────────────────
class OpenAICompatibleAdapter(BaseAdapter):
    """Generic adapter for any OpenAI‑compatible REST endpoint."""

    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None):
        super().__init__(model.split("/")[-1])
        self.model = model
        self.client = get_client(base_url, api_key)

    async def stream(self, messages: list[dict]):
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.8,
            )
            async for chunk in stream:
                token = chunk.choices[0].delta.content
                if token:
                    yield token
        except Exception as e:
            yield f"\n[ERROR {self.name}: {e}]\n"


# ─────────────────────────────── Ollama Daemon Adapter ───────────────────────────────
class OllamaAdapter(BaseAdapter):
    """Adapter for a local or remote Ollama server."""

    def __init__(self, model: str):
        super().__init__(model)
        self.base_url = OLLAMA_HOST  # taken from .env (default localhost)

    async def stream(self, messages: list[dict]):
        payload = {
            "model": self.name,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.8},
        }
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", f"{self.base_url}/api/chat", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        try:
                            data = json.loads(line)
                        except json.JSONDecodeError:
                            continue
                        token = data.get("message", {}).get("content")
                        if token:
                            yield token + " "
                        if data.get("done"):
                            break
        except Exception as e:
            yield f"\n[OLLAMA ERROR: {e}]\n"


# ─────────────────────────────── Provider Factory ───────────────────────────────
def get_adapter(provider: str, model: str) -> BaseAdapter:
    """Return the appropriate adapter for the given provider."""
    mapping = {
        "openai": ("https://api.openai.com/v1", os.getenv("OPENAI_API_KEY")),
        "groq": ("https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY")),
        "local": ("http://localhost:1234/v1", "lmstudio"),
        "lmstudio": ("http://localhost:1234/v1", "lmstudio"),
    }

    if provider in mapping:
        base, key = mapping[provider]
        return OpenAICompatibleAdapter(model, base, key)

    if provider == "ollama":
        return OllamaAdapter(model)

    raise ValueError(f"Unknown provider: {provider}")

