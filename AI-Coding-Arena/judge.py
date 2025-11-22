# judge.py
# Android 14 SAF-focused judge — kills deprecated APIs instantly
import re
from adapters import get_adapter

def extract_final_code(transcript: str) -> str:
    blocks = re.findall(r'```(?:java)?\s*\n(.*?)\n```', transcript, re.DOTALL)
    return "\n\n".join(blocks[-3:]) if blocks else "<NO VALID CODE FOUND>"

JUDGE_PROMPT = """You are the Supreme Android Code Judge — strict, technical, unforgiving.

Evaluate ONLY the final extracted code below.
Punish:
• Any use of new File(), Environment.getExternalStorageDirectory(), or legacy storage APIs
• Bullet lists, release notes, or non-code output
• Regressions or broken navigation
• Missing persistable URI permissions

Reward:
• Proper use of Storage Access Framework (SAF)
• ACTION_OPEN_DOCUMENT_TREE + takePersistableUriPermission
• Clean, compiling, modern Android 14 code

Here is the final code:
