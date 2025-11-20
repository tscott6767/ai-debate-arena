# judge.py
"""
judge.py – Handles evaluation of the debate transcript by a third model acting as the judge.
The judge compares the arguments of Side A and Side B and streams a verdict.
"""

from adapters import get_adapter


# ─── Template prompt fed to the judging model ───────────────────────────────
JUDGE_PROMPT = """
You are the Supreme AI Judge. Be fair, witty, and decisive.

Participants:
• Side A: {a_name}
• Side B: {b_name}
Topic: {topic}

Deliver your verdict in this exact format:

### FINAL VERDICT

**Winner:** [Name]

**Summary**
• {a_name} argued: [...]
• {b_name} argued: [...]

**Scores**
| Criterion            | {a_name} | {b_name} | Notes                    |
|----------------------|----------|----------|--------------------------|
| Logic & Reasoning    | ?/10     | ?/10     |                          |
| Clarity & Structure  | ?/10     | ?/10     |                          |
| Persuasiveness       | ?/10     | ?/10     |                          |
| Use of Evidence      | ?/10     | ?/10     |                          |

**Detailed Reasoning:** [Your full judgment]
"""


# ─── Main judgment coroutine ───────────────────────────────────────────────
async def run_judgment(a, b, transcript: str, topic: str, provider: str, model: str):
    """
    Stream the judge model’s evaluation of the completed debate.

    Args:
        a, b:          The two adapter instances (debaters)
        transcript:    Full debate transcript string
        topic:         Debate topic
        provider:      Provider name for the judge model
        model:         Model identifier for the judge
    """
    judge = get_adapter(provider, model)

    system_prompt = JUDGE_PROMPT.format(a_name=a.name, b_name=b.name, topic=topic)
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Here is the full debate transcript:\n\n{transcript}\n\nNow deliver your judgment.",
        },
    ]

    async for token in judge.stream(messages):
        yield token

