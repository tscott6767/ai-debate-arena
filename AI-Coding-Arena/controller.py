# controller.py
import asyncio
import re
from judge import run_judgment
from prompts import get_side_prompt

MAX_HISTORY = 24  # Keeps context manageable without ballooning memory


class DebateController:
    def __init__(self, config, session_id: str):
        self.config = config
        self.session_id = session_id
        self.history = []
        self.transcript_parts = [
            f"DEBATE SESSION: {session_id}\n"
            f"TOPIC: {config.topic[:500]}{'...' if len(config.topic) > 500 else ''}\n"
            f"ROUNDS: {config.rounds} | JUDGE: {config.judge_model}\n"
            + "=" * 80 + "\n\n"
        ]

    # ------------------------------------------------------------------
    @staticmethod
    def extract_code_blocks(text: str) -> str:
        """Extract all code segments from markdown, even malformed ones."""
        blocks = re.findall(r"```[^\n]*\n(.*?)\n```", text, re.DOTALL)
        if not blocks:
            blocks = re.findall(r"```(.*?)```", text, re.DOTALL)
        if not blocks:
            if any(kw in text.lower() for kw in ["public class", "def ", "function ", "import ", "const ", "#include"]):
                lines = []
                for line in text.splitlines():
                    if (
                        line.startswith(("    ", "\t", "  "))
                        or any(line.strip().startswith(p)
                               for p in ["public", "class", "def", "import", "from", "const", "function", "#"])
                    ):
                        lines.append(line.strip())
                if lines:
                    return "\n".join(lines[:200])  # Avoid runaway transcripts
        return "\n\n".join(block.strip() for block in blocks) if blocks else ""

    # ------------------------------------------------------------------
    async def run(self):
        """Main debate loop. Streams output to websocket layer."""
        yield self.transcript_parts[0]

        speakers = [
            (self.config.adapter_a, "A", "FOR the solution — build and improve the code"),
            (self.config.adapter_b, "B", "AGAINST — critique, fix bugs, and propose better alternatives"),
        ]
        turn = 0
        last_a = ""
        last_b = ""

        for round_num in range(1, self.config.rounds + 1):
            adapter, side, stance = speakers[turn]
            prompt = get_side_prompt(self.config.topic, side, stance, round_num)

            messages = [{"role": "system", "content": prompt}] + self.history[-MAX_HISTORY:]
            yield f"\n{'='*20} ROUND {round_num} | SIDE {side} | {adapter.name.upper()} {'='*20}\n"

            full_response = ""
            try:
                async for chunk in adapter.stream(messages):
                    text_chunk = str(chunk)
                    full_response += text_chunk
                    yield text_chunk
                yield "\n\n"
            except Exception as e:
                error = f"\n[CRITICAL ERROR in {adapter.name}: {e}]\n"
                yield error
                self.transcript_parts.append(error)
                turn = 1 - turn
                continue

            self.transcript_parts.append(full_response + "\n\n")

            # ---------------------------------------------------------
            # Track final outputs per side for the judge
            if side == "A":
                last_a = full_response
            else:
                last_b = full_response

            # ---------------------------------------------------------
            # Extract & validate code
            code = self.extract_code_blocks(full_response)
            if not code.strip():
                correction = (
                    "WARNING: Your response contained NO valid code blocks.\n"
                    "You are in a coding debate. You MUST reply with full, syntax‑correct source code "
                    "inside ``` blocks. No explanations outside code. No apologies. Try again."
                )
                self.history.extend([
                    {"role": "assistant", "content": full_response},
                    {"role": "user", "content": f"{side}-MODEL CORRECTION:\n" + correction}
                ])
                yield "JUDGE INTERVENTION: Invalid response — model forced to correct.\n"
            else:
                self.history.extend([
                    {"role": "assistant", "content": code},
                    {"role": "user", "content": f"Round {round_num + 1}: Improve full project. Fix bugs, add features, enhance structure."}
                ])
                yield f"Valid code extracted ({len(code.splitlines())} lines). Project evolving...\n"

            self.history = self.history[-MAX_HISTORY:]
            turn = 1 - turn
            await asyncio.sleep(0.1)

        # =====================================================
        # Final judgment
        yield "\n\nJUDGE INVOKED — FINAL VERDICT INCOMING...\n" + "—"*60 + "\n"

        try:
            pre_judge_transcript = "".join(self.transcript_parts)

            # Pass the final outputs from A and B to the judge
            async for token in run_judgment(
                a=last_a,
                b=last_b,
                transcript=pre_judge_transcript,
                topic=self.config.topic,
                provider=self.config.judge_provider,
                model=self.config.judge_model
            ):
                yield str(token)
                self.transcript_parts.append(str(token))

            final_transcript = "".join(self.transcript_parts)
            self.transcript_parts = [final_transcript]
            yield "\n\nDEBATE COMPLETE. FINAL CODEBASE LOCKED. VERDICT RENDERED.\n"

        except Exception as e:
            err = f"\nJUDGE FAILED: {e}\nDEBATE ENDED WITHOUT FINAL VERDICT.\n"
            yield err
            self.transcript_parts.append(err)

        yield f"\n\nSession {self.session_id} — Archived.\n"
