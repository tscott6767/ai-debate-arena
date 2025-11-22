# controller.py
# Only the important parts — the rest of your original file stays the same

from judge import run_judgment          # ← THIS LINE MUST BE EXACT
from prompts import get_side_prompt
import re

# ... rest of your DebateController class ...

# Inside your run() method, after all rounds:
async for token in run_judgment(a, b, transcript, topic, judge_provider, judge_model):
    yield token
    self.transcript_parts.append(token)
