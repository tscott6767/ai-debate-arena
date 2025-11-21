"""
multi_battle_test.py
Quick connectivity test for all configured LLM providers.

Usage:
  python multi_battle_test.py
Make sure you 'source .env' or have your API keys exported first.
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import builtins

_old_print = print
def print(*args, **kwargs):
    # universal defensive printer
    msg = ' '.join(str(a).encode('utf-8', errors='replace').decode('utf-8', errors='replace') for a in args)
    _old_print(msg, **kwargs)

builtins.print = print
import asyncio, os
from adapters import get_adapter
from dotenv import load_dotenv
load_dotenv()

# Models to test per provider (edit freely)
PROVIDERS = {
    "ollama":   "llama3:latest",
    "openai":   "gpt-4o-mini",
    "groq":     "mixtral-8x7b",
    "mistral":  "mistral-small",
    "anthropic": "claude-3-sonnet"
}

TEST_MESSAGE = [{"role": "user", "content": "Hello World"}]


async def check_provider(provider, model):
    print(f"\n🔍 Testing {provider}  →  {model}")
    adapter = None
    try:
        adapter = get_adapter(provider, model)
        async for token in adapter.stream(TEST_MESSAGE):
            print("✅ First token:", token[:50])
            break
    except Exception as e:
        print(f"❌ {provider}: {e}")
    finally:
        if adapter:
            await adapter.close()


async def main():
    tasks = [check_provider(p, m) for p, m in PROVIDERS.items()]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

