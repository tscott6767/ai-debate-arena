"""
adapters.py — Unified adapter layer for AI Debate Arena (final UTF‑8‑safe version)
"""

import os, json, httpx, traceback
from abc import ABC, abstractmethod
from openai import AsyncOpenAI

# ---------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------
def exception_text(e: Exception) -> str:
    """
    Always return a printable UTF‑8 string for any exception, including SDK internals.
    """
    tb = "".join(traceback.format_exception(type(e), e, e.__traceback__))
    return tb.encode("utf-8", errors="replace").decode("utf-8", errors="replace")

_CLIENT_CACHE: dict[tuple, AsyncOpenAI] = {}

def get_client(base_url: str | None, api_key: str | None) -> AsyncOpenAI:
    key = (base_url or "", api_key or "")
    if key not in _CLIENT_CACHE:
        _CLIENT_CACHE[key] = AsyncOpenAI(base_url=base_url, api_key=api_key)
    return _CLIENT_CACHE[key]

# ---------------------------------------------------------------------
# Base adapter
# ---------------------------------------------------------------------
class BaseAdapter(ABC):
    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def stream(self, messages: list[dict]):
        pass

    async def close(self):
        pass

# ---------------------------------------------------------------------
# OpenAI‑compatible (OpenAI / Groq / Mistral / LMStudio)
# ---------------------------------------------------------------------
class OpenAICompatibleAdapter(BaseAdapter):
    def __init__(self, model, base_url=None, api_key=None):
        super().__init__(model)
        self.client = get_client(base_url, api_key)
        self.model = model

    async def stream(self, messages):
        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=0.8,
            )
            async for chunk in stream:
                if token := chunk.choices[0].delta.content:
                    yield token
        except Exception as e:
            yield f"\n[{self.name} Adapter Error → {exception_text(e)}]\n"

# ---------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------
class AnthropicAdapter(BaseAdapter):
    def __init__(self, model="claude-3-sonnet", api_key=None):
        super().__init__(model)
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")

    async def stream(self, messages):
        headers = {
            "x-api-key": str(self.api_key or ""),
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }
        payload = {
            "model": self.name,
            "max_tokens": 1024,
            "messages": messages,
            "stream": True,
        }
        try:
            async with httpx.AsyncClient(timeout=None) as c:
                async with c.stream("POST", "https://api.anthropic.com/v1/messages",
                                    headers=headers, json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip() or not line.startswith("data: "):
                            continue
                        try:
                            data = json.loads(line.removeprefix("data: ").strip())
                        except json.JSONDecodeError:
                            continue
                        token = data.get("delta", {}).get("text")
                        if token:
                            yield token
                        if "message_stop" in line:
                            break
        except Exception as e:
            yield f"\n[{self.name} Adapter Error → {exception_text(e)}]\n"

# ---------------------------------------------------------------------
# Ollama (local or remote)
# ---------------------------------------------------------------------
class OllamaAdapter(BaseAdapter):
    def __init__(self, model):
        super().__init__(model)
        self.base_url = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    async def stream(self, messages):
        payload = {
            "model": self.name,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.8},
        }
        async with httpx.AsyncClient(timeout=None) as c:
            url_primary = f"{self.base_url}/api/chat"
            url_fallback = f"{self.base_url}/chat"
            try:
                async with c.stream("POST", url_primary, json=payload) as resp:
                    if resp.status_code == 404:
                        print(f"[OllamaAdapter] {url_primary} → 404; trying {url_fallback}")
                        async with c.stream("POST", url_fallback, json=payload) as r2:
                            r2.raise_for_status()
                            async for token in self._iter_stream(r2):
                                yield token
                    else:
                        resp.raise_for_status()
                        async for token in self._iter_stream(resp):
                            yield token
            except Exception as e:
                yield f"\n[{self.name} Adapter Error → {exception_text(e)}]\n"

    async def _iter_stream(self, response):
        async for line in response.aiter_lines():
            if not line.strip():
                continue
            try:
                data = json.loads(line)
            except json.JSONDecodeError:
                continue
            if token := data.get("message", {}).get("content"):
                yield token
            if data.get("done"):
                break

# ---------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------
def get_adapter(provider: str, model: str) -> BaseAdapter:
    provider = provider.lower()
    mapping = {
        "openai":   ("https://api.openai.com/v1",   os.getenv("OPENAI_API_KEY")),
        "groq":     ("https://api.groq.com/openai/v1", os.getenv("GROQ_API_KEY")),
        "mistral":  ("https://api.mistral.ai/v1",   os.getenv("MISTRAL_API_KEY")),
        "lmstudio": ("http://localhost:1234/v1",    "lmstudio"),
    }

    if provider in mapping:
        base, key = mapping[provider]
        return OpenAICompatibleAdapter(model, base_url=base, api_key=key)
    elif provider == "anthropic":
        return AnthropicAdapter(model)
    elif provider == "ollama":
        return OllamaAdapter(model)
    else:
        raise ValueError(f"Unknown provider: {provider}")
