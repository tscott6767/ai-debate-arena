#!/usr/bin/env bash
# ===============================================================
# continue_run.sh  —  Automatic Continuation / Re‑Injection Script
# ===============================================================
# Requirements: bash + curl + jq (sudo apt install jq)
# Usage: ./continue_run.sh [limit]
#
# limit = how many previous debates to merge (default 1)
#         e.g.  ./continue_run.sh 3
#
# This script:
#  1. Fetches the last N debates
#  2. Pre‑pends your Task + Rules text
#  3. Registers a new topic and prints token + length
#  4. Launches a new debate via WebSocket URL (shown at end)
# ---------------------------------------------------------------

LIMIT=${1:-1}
HOST="http://localhost:8000"

# === 1️⃣  Fetch the last N debates ===========================================
echo "Fetching last $LIMIT debate(s)…"
curl -s "$HOST/api/continuation?limit=$LIMIT" -o /tmp/_cont.json

# extract plain text of transcript
TRANSCRIPT=$(jq -r '.topic' /tmp/_cont.json)

# === 2️⃣  Your Task + Rules ==================================================
# Paste or read your long instructions from a separate file for convenience
TASK_RULES_FILE="./task_rules.txt"
if [ ! -f "$TASK_RULES_FILE" ]; then
  echo "Task + Rules file not found!  Create ./task_rules.txt first."
  exit 1
fi
TASK_RULES=$(cat "$TASK_RULES_FILE")

# === 3️⃣  Combine and register ==============================================
COMBINED="${TASK_RULES}\n\nContinuation from previous debate(s):\n\n${TRANSCRIPT}"
JSON=$(jq -Rs --arg topic "$COMBINED" '{topic:$topic}' <<< "")

echo "Registering combined topic with server…"
TOKEN_JSON=$(curl -s -X POST "$HOST/api/register_topic" \
              -H "Content-Type: application/json" \
              -d "$JSON")

TOKEN=$(echo "$TOKEN_JSON" | jq -r '.token')
LENGTH=$(echo "$TOKEN_JSON" | jq -r '.length')

echo "New topic registered: token=$TOKEN"
echo "Character length: $LENGTH"

# === 4️⃣  Display ready-to-use WebSocket URL ================================
WS_URL="ws://localhost:8000/ws/debate?token=$TOKEN&rounds=5"
echo
echo "✅  Launch your next debate using this URL:"
echo "   $WS_URL"
echo "   (Paste it into the 'Connect manually' box or modify index.html if needed.)"

