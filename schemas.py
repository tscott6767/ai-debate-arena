# schemas.py
"""
schemas.py — Pydantic configuration container definitions.
"""
from pydantic import BaseModel
from typing import Any


class DebateConfig(BaseModel):
    """Runtime configuration schema for a debate session."""
    topic: str
    rounds: int
    adapter_a: Any
    adapter_b: Any
    judge_provider: str
    judge_model: str
