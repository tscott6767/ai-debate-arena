controller.py
import asyncio
from judge import run_judgment
MAX_HISTORY = 10
class DebateController:
"""
Orchestrates the back‑and‑forth debate rounds between two model adapters,
then invokes the AI judge for the final verdict.
"""
def __init__(self, config, session_id: str):
    self.config = config
    self.session_id = session_id
    self.history = []  # shared history context
    self.transcript_parts = [f"🧩 Topic: {config.topic}\n\n"]

async def run(self):
    """Main debate execution coroutine (async generator)."""
    yield f"Session {self.session_id}\n\n"

    # Define two participants
    speakers = [
        (self.config.adapter_a, "A", "for (Side A)"),
        (self.config.adapter_b, "B", "against (Side B)"),
    ]
    turn = 0

    # ── Debate Rounds ───────────────────────────────────────────────
    for r in range(1, self.config.rounds + 1):
        adapter, side, stance = speakers[turn]

        # --- capture the opponent's previous message for visibility ---
        if turn and len(self.history) >= 2:
            # last "assistant" message before newer "user" prompt ≈ opponent's text
            last_opponent = self.history[-2]["content"][:2000]
            opponent_ref = f"Opponent's last response:\n{last_opponent}\n"
        else:
            opponent_ref = ""

        # Explicit system prompt per side (now includes opponent_ref)
        role_instruction = (
            f"You are Side A arguing IN FAVOR of the topic: {self.config.topic}.\n"
            f"{opponent_ref}"
            "Provide a persuasive argument supporting the topic. "
            "Do NOT invent your opponent’s lines, questions, or moderator comments."
            if side == "A"
            else f"You are Side B arguing AGAINST the topic: {self.config.topic}.\n"
                 f"{opponent_ref}"
                 "Provide a rebuttal or counter‑argument. "
                 "Do NOT create or imitate the opponent’s dialogue."
        )

        round_messages = [{"role": "system", "content": role_instruction}]
        round_messages += self.history[-MAX_HISTORY:]

        yield f"\n{side} Round {r} — {adapter.name} (Side {side}) {stance}\n"

        tokens = []
        try:
            async for tok in adapter.stream(round_messages):
                tokens.append(tok)
                yield tok
        except Exception as e:
            err_msg = f"\n[{adapter.name} ERROR: {e}]\n"
            yield err_msg
            self.transcript_parts.append(err_msg)
            continue

        yield "\n\n"

        response = "".join(tokens)
        self.transcript_parts.append(response + "\n\n")

        # --- add side labels and direct instruction for the next speaker ---
        self.history.extend([
            {"role": "assistant", "content": f"SIDE {side} OUTPUT:\n{response}"},
            {"role": "user", "content":
                f"Please rebut or improve upon the previous message from "
                f"Side {'A' if side=='B' else 'B'} succinctly."},
        ])
        self.history = self.history[-MAX_HISTORY:]

        turn = 1 - turn  # alternate sides

    # ── Judgment Phase ───────────────────────────────────────────────
    transcript = "".join(self.transcript_parts)
    yield "\n\n⚖️ JUDGE SUMMONED...\n"
    await asyncio.sleep(1)
    yield "🧑‍⚖️ The AI Judge is deliberating...\n\n"

    try:
        async for tok in run_judgment(
            self.config.adapter_a,
            self.config.adapter_b,
            transcript,
            self.config.topic,
            self.config.judge_provider,
            self.config.judge_model,
        ):
            yield tok
            self.transcript_parts.append(tok)
    except Exception as e:
        err_msg = f"\n[JUDGE ERROR: {e}]\n"
        yield err_msg
        self.transcript_parts.append(err_msg)

    yield "\n\n🏛️ Case closed."
    self.transcript_parts.append("\n\n🏛️ Case closed.")

    # Clean up adapters
    await self.config.adapter_a.close()
    await self.config.adapter_b.close()
