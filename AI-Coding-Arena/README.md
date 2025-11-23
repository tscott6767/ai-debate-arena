# AI Coding Arena — Android SAF Edition

A brutal, adversarial, self-improving multi-agent coding platform.

Two LLMs fight to produce the best Android 14 file explorer using **only** the Storage Access Framework (SAF).

A merciless judge executes anyone who:
- Uses deprecated `File` APIs
- Outputs bullet lists or release notes
- Regresses or hallucinates

Only perfect, modern, compiling code survives.

### Files

- `prompts.py` → Forces code-only output
- `judge.py` → Android 14 SAF judge (kills legacy storage instantly)
- `controller.py` → The arena engine
- `README.md` → This file

### How to adapt for other languages

1. Change the debate topic
2. Edit `prompts.py` rules for your language
3. Replace `judge.py` with a judge that knows your framework's best practices
4. After each run place the new judge verdict into the prompt for next run for real time evolution.
Example: Create a Rust judge that kills `println!` debugging and rewards `async` + tests.

### Run

```bash
python -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
