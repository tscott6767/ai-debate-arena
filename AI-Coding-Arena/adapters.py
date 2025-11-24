# adapters.py — The Ultimate Multi-Provider Streaming Adapter (2025 Edition)
import os
import json
import httpx
import traceback
from abc import ABC, abstractmethod
from openai import AsyncOpenAI
from typing import AsyncGenerator

# ---------------------------------------------------------------------
# UTF-8 Safe Exception Printer (Critical for Ollama/Claude crashes)
# ---------------------------------------------------------------------
def exception_text(e: Exception) -> str:
    tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    return tb.encode("utf-8", errors="replace").decode("utf-8")

# ---------------------------------------------------------------------
# Client Cache — Prevent Connection Leaks
# ---------------------------------------------------------------------
_CLIENT_CACHE: dict[tuple[str | None, str | None], AsyncOpenAI] = {}

def get_openai_client(base_url: str | None, api_key: str | None) -> AsyncOpenAI:
    key = (base_url or "", api_key or "")
    if key not in _CLIENT_CACHE:
        _CLIENT_CACHE[key] = AsyncOpenAI(base_url=base_url, api_key=api_key or "sk-no-key-needed")
    return _CLIENT_CACHE[key]

# ---------------------------------------------------------------------
# Base Adapter
# ---------------------------------------------------------------------
class BaseAdapter(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def stream(self, messages: list[dict]) -> AsyncGenerator[str, None]:
        pass

    async def close(self):
        pass  # For future cleanup if needed


# ---------------------------------------------------------------------
# OpenAI-Compatible (OpenAI, Groq, Mistral, Together, Fireworks, LMStudio, etc.)
# ---------------------------------------------------------------------
class OpenAICompatibleAdapter(BaseAdapter):
    def __init__(self, model: str, base_url: str | None = None, api_key: str | None = None):
        super().__init__(model.split("/")[-1])  # Clean display name
        self.client = get_openai_client(base_url, api_key)
        self.model = model

    async def stream(self, messages):
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.8,
                top_p=0.9,
                max_tokens=4096,
            )
            async for chunk in stream:
                if (delta := chunk.choices[0].delta.content):
                    yield delta
        except Exception as e:
            yield f"\n[{self.name} ERROR]: {exception_text(e)}\n"


# ---------------------------------------------------------------------
# Anthropic (Claude) — Raw Streaming
# ---------------------------------------------------------------------
class AnthropicAdapter(BaseAdapter):
    def __init__(self, model: str):
        super().__init__(model)
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY not set")

    async def stream(self, messages):
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.name,
            "max_tokens": 4096,
            "temperature": 0.8,
            "messages": messages,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=None) as client:
                async with client.stream("POST", "https://api.anthropic.com/v1/messages", headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        line = line.strip()
                        if not line or not line.startswith("data: "):
                            continue
                        if line == "data: [DONE]":
                            break
                        try:
                            data = json.loads(line[6:])
                            if token := data.get("delta", {}).get("text"):
                                yield token
                        except json.JSONDecodeError:
                            continue
        except Exception as e:
            yield f"\n[Claude ERROR]: {exception_text(e)}\n"


# ---------------------------------------------------------------------
# Ollama — Works with Ollama, OpenWebUI, anything
# ---------------------------------------------------------------------
class OllamaAdapter(BaseAdapter):
    def __init__(self, model: str):
        super().__init__(model)
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

    async def stream(self, messages):
        payload = {
            "model": self.name,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.8, "top_p": 0.9},
        }
        urls_to_try = [
            f"{self.base_url}/api/chat",
            f"{self.base_url}/chat",
            f"{self.base_url}/v1/chat/completions",  # OpenWebUI compatibility
        ]
        last_error = None
        for url in urls_to_try:
            try:
                async with httpx.AsyncClient(timeout=None) as c:
                    async with c.stream("POST", url, json=payload) as resp:
                        if resp.status_code == 404:
                            continue
                        resp.raise_for_status()
                        async for line in resp.aiter_lines():
                            if not line.strip():
                                continue
                            try:
                                data = json.loads(line)
                                if token := data.get("message", {}).get("content"):
                                    yield token
                                if data.get("done"):
                                    return
                            except json.JSONDecodeError:
                                continue
                        return
            except Exception as e:
                last_error = e
                continue
        yield f"\n[Ollama ERROR]: Could not connect. Tried: {', '.join(urls_to_try)}\nLast error: {exception_text(last_error or 'Unknown')}\n"


# ---------------------------------------------------------------------
# Factory — Clean, Secure, Extensible
# ---------------------------------------------------------------------
def get_adapter(provider: str, model: str) -> BaseAdapter:
    provider = provider.lower().strip()

    # OpenAI-compatible endpoints
    compat_map = {
        "openai": ("https://api.openai.com/v1", os.getenv("OPENAI_API_KEY")),
        "groq": ("https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY")),
        "mistral": ("https://api.mistral.ai/v1", os.getenv("MISTRAL_API_KEY")),
        "together": ("https://api.together.xyz/v1", os.getenv("TOGETHER_API_KEY")),
        "fireworks": ("https://api.fireworks.ai/inference/v1", os.getenv("FIREWORKS_API_KEY")),
        "lmstudio": ("http://localhost:1234/v1", "lm-studio"),
        "local": ("http://localhost:8080/v1", "local"),
    }

    if provider in compat_map:
        base_url, api_key = compat_map[provider]
        if not api_key and provider != "lmstudio":
            raise ValueError(f"{provider.upper()}_API_KEY not set")
        return OpenAICompatibleAdapter(model, base_url, api_key)

    elif provider == "anthropic":
        return AnthropicAdapter(model)

    elif provider == "ollama":
        return OllamaAdapter(model)

    else:
        raise ValueError(f"Unsupported provider: {provider}\nSupported: {', '.join(compat_map.keys())}, anthropic, ollama")
