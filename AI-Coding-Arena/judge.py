# judge.py — UNFOOLABLE ANDROID 14 SAF JUDGE (FINAL EVOLUTION)
import re
from adapters import get_adapter

# INSTANT DEATH FOR ANY LEGACY FILE API
BANNED = [
    r'\bFile\s+', r'\.getExternalStorage', r'\.getAbsolutePath',
    r'\.listFiles\s*\(', r'\.getParentFile', r'Uri\.fromFile',
    r'\benvironment\.getExternalStorage', r'new File\s*\('
]

# REQUIRED FOR REAL SAF (at least 3 needed)
REQUIRED = [
    r'ACTION_OPEN_DOCUMENT_TREE',
    r'takePersistableUriPermission',
    r'DocumentFile\.fromTreeUri',
    r'DocumentFile.*\.listFiles',
    r'DocumentsContract'
]

def count_banned(code: str) -> int:
    return sum(len(re.findall(p, code, re.IGNORECASE)) for p in BANNED)

def count_required(code: str) -> int:
    return sum(bool(re.search(p, code, re.IGNORECASE)) for p in REQUIRED)

def extract_code(transcript: str) -> str:
    blocks = re.findall(r'```(?:java|kotlin|xml|python)?\s*\n(.*?)\n```', transcript, re.DOTALL)
    return "\n\n".join(blocks[-5:]) if blocks else "NO CODE"

JUDGE_PROMPT = """You are the Supreme Android SAF Judge.

MECHANICAL VERDICT FIRST:
BANNED legacy APIs detected: {banned}
REQUIRED SAF APIs found: {required}

If BANNED > 0 → INSTANT DEATH PENALTY (0/10 everything)
If REQUIRED < 3 → max 2/10 for SAF usage

Then give normal verdict.

Code:

Use exact table. Be brutal.
"""

async def run_judgment(a, b, transcript: str, topic: str, provider: str, model: str):
    code = extract_code(transcript)
    banned = count_banned(code)
    required = count_required(code)

    if banned > 0:
        verdict = f"""### FINAL CODE VERDICT
**INSTANT DEATH PENALTY** — {banned} legacy File API(s) detected
Winner: Neither
All scores: 0/10
Critical Bugs: • Used banned java.io.File / legacy storage APIs"""
        for word in verdict.split():
            yield word + " "
        return

    system_prompt = JUDGE_PROMPT.format(
        final_code=code,
        banned=banned,
        required=required
    )

    judge = get_adapter(provider, model)
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": f"Judge the final code. Side A: {a.name} | Side B: {b.name}"}
    ]

    async for token in judge.stream(messages):
        yield token
