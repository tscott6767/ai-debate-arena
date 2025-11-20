class OllamaAdapter(BaseAdapter):
    def __init__(self, model: str):
        super().__init__(name=model)

    async def stream(self, messages):
        payload = {
            "model": self.name,
            "messages": messages,
            "stream": True,
            "options": {"temperature": 0.8}
        }
        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                async with client.stream("POST", "http://192.168.178.142:11434/api/chat", json=payload) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.strip():
                            continue
                        data = json.loads(line)
                        if token := data.get("message", {}).get("content"):
                            yield token
        except Exception as e:
            yield f"\n[OLLAMA ERROR: {e}]\n"
