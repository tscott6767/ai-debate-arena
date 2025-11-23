# controller.py
import asyncio
import re  # NEW: For code extraction
from judge import run_judgment
from prompts import get_side_prompt  # NEW: Import modular prompts

MAX_HISTORY = 20  # UPDATED: Increased for longer coding sessions

class DebateController:
    """
    Orchestrates the back-and-forth debate rounds between two model adapters,
    then invokes the AI judge for the final verdict.
    """
    def __init__(self, config, session_id: str):
        self.config = config
        self.session_id = session_id
        self.history = []  # shared history context
        self.transcript_parts = [f"🧩 Topic: {config.topic}\n\n"]

    def extract_code_content(self, response: str) -> str:
        """NEW: Extract only code blocks from response to clean history."""
        # Simple regex for markdown code blocks (```java
        matches = re.findall(r'```(?:\w+)?\n(.*?)\n```', response, re.DOTALL)
        if matches:
            return '\n\n'.join(matches)
        # Fallback: If no code, return empty (will trigger correction)
        return ''

    async def run(self):
        """Main debate execution coroutine (async generator)."""
        yield f"Session {self.session_id}\n\n"
        # Define two participants
        speakers = [
            (self.config.adapter_a, "A", "for (Side A)"),
            (self.config.adapter_b, "B", "against (Side B)"),
        ]
        turn = 0
        # ── Debate Rounds ───────────────────────────────────────────────
        for r in range(1, self.config.rounds + 1):
            adapter, side, stance = speakers[turn]
            # UPDATED: Use modular prompt template
            role_instruction = get_side_prompt(self.config.topic, side, stance)
            round_messages = [{"role": "system", "content": role_instruction}]
            round_messages += self.history[-MAX_HISTORY:]
            yield f"\n{side} Round {r} — {adapter.name} (Side {side}) {stance}\n"
            tokens = []
            try:
                async for tok in adapter.stream(round_messages):
                    tokens.append(tok)
                    yield tok
            except Exception as e:
                err_msg = f"\n[{adapter.name} ERROR: {e}]\n"
                yield err_msg
                self.transcript_parts.append(err_msg)
                continue
            yield "\n\n"
            response = "".join(tokens)
            self.transcript_parts.append(response + "\n\n")
            # UPDATED: Extract code for cleaner history append
            code_content = self.extract_code_content(response)
            if not code_content:
                # NEW: Correct hallucinations with targeted user message
                user_msg = "Your previous response contained no valid code. Output ONLY complete, compiling source files as per the rules."
                self.history.extend([
                    {"role": "assistant", "content": response},  # Keep raw for transcript
                    {"role": "user", "content": user_msg},
                ])
            else:
                self.history.extend([
                    {"role": "assistant", "content": code_content},  # Clean code only
                    {"role": "user", "content": "Please improve the project code/structure with the next iteration of your reply."},
                ])
            self.history = self.history[-MAX_HISTORY:]
            turn = 1 - turn  # alternate sides
        # === FINAL WORKING JUDGMENT PHASE (USE THIS) ===
        yield "\n\nJUDGE SUMMONED... The AI Judge is deliberating...\n\n"

        try:
            full_transcript = "".join(self.transcript_parts)

            async for token in run_judgment(
                a=self.config.adapter_a,
                b=self.config.adapter_b,
                transcript=full_transcript,
                topic=self.config.topic,
                provider=self.config.judge_provider,
                model=self.config.judge_model
            ):
                yield token
                self.transcript_parts.append(token)

        except Exception as e:
            error_msg = f"\n[JUDGE ERROR: {e}]\n"
            yield error_msg
            self.transcript_parts.append(error_msg)

        yield "\n\nCase closed."
        # === END ===
