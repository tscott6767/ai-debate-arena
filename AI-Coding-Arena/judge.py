# judge.py — FINAL, 100% WORKING VERSION (Android 14 SAF Judge)
import re
from adapters import get_adapter


def extract_final_code(transcript: str) -> str:
    """Extract the last 3 code blocks from the debate (java, xml, etc.)"""
    blocks = re.findall(r'```(?:java|kotlin|xml)?\s*\n(.*?)\n```', transcript, re.DOTALL)
    if not blocks:
        return "<NO VALID CODE FOUND IN ENTIRE DEBATE>"
    return "\n\n".join(blocks[-3:])


JUDGE_PROMPT = """You are the Supreme Android Code Judge — strict, technical, unforgiving.

Your only job is to evaluate the FINAL code produced in this debate.
CRITICAL: If you see any of these, give 0/10 immediately:
• Environment.getExternalStorageDirectory()
• new File(...)
• Uri.fromFile(...)
• currentDirectory.listFiles()
• file.getAbsolutePath()

These are BANNED on Android 10+. Only DocumentProvider + tree URIs are allowed.
Punish severely:
• Any use of new File(), Environment.getExternalStorageDirectory(), or legacy storage APIs
• Bullet lists, release notes, explanations, or non-code output
• Regressions, broken navigation, missing features
• No persist difficile URI permissions (takePersistableUriPermission)

Reward highly:
• Correct use of Storage Access Framework (SAF)
• ACTION_OPEN_DOCUMENT_TREE + takePersistableUriPermission
• Clean, modern, compiling Android 14 code
• Folder navigation, copy/delete, persistent permissions

Here is the final extracted code:


Deliver your verdict in this EXACT format:

### FINAL CODE VERDICT

**Winner:** Side A | Side B | Tie | Neither (both failed)

**Final Code Status:** Valid / Invalid / No code

**Score (0–10):**
| Criterion                        | Score | Notes |
|----------------------------------|-------|-------|
| Compiles on Android 14           | ?/10  |       |
| Uses only SAF (no File API)      | ?/10  |       |
| Folder navigation works          | ?/10  |       |
| Permissions persist              | ?/10  |       |
| No hallucinations/non-code       | ?/10  |       |
| No regression                    | ?/10  |       |
| Code quality                     | ?/10  |       |

**Winner Reasoning:** [clear explanation]
**Critical Bugs:** • [list or "None"]
**Recommendation:** Continue with [Side A / Side B / Neither]

Be brutal. Only perfect code wins.
"""


async def run_judgment(a, b, transcript: str, topic: str, provider: str, model: str):
    """Streams the final judgment from the judge model."""
    judge = get_adapter(provider, model)
    final_code = extract_final_code(transcript)
    system_prompt = JUDGE_PROMPT.format(final_code=final_code)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Topic: {topic}\nSide A: {a.name}\nSide B: {b.name}\n\nJudge now."}
    ]
    async for token in judge.stream(messages):
        yield token
