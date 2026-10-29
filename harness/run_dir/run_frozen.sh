#!/bin/bash
# Frozen agent: with an empty state, the solver writes each level's test program once, and the program is scored on
# the five cells. Usage: ./run_frozen.sh 1 2 3 4   (levels; run from the chain's run directory)
set -e
D="$(cd "$(dirname "$0")" && pwd)"
if [ -z "$PYTHON" ]; then PYTHON="$(python3 -c "import json;print(json.load(open('$D/CONFIG.json'))['python'])")"; fi
PY="$PYTHON"
COURSE="$("$PY" -c "import json;print(json.load(open('$D/CONFIG.json'))['course'])")"
GATEWAY="$("$PY" -c "import json;print(json.load(open('$D/CONFIG.json'))['gateway_url'])")"
cd "$D/harness_k1_test"
export PYTHONPATH="$PWD/sdk:$PWD"
export RSI_GATEWAY="$GATEWAY"
LEVELS="${*:-1 2 3 4 5}"
for level in $LEVELS; do
  export RSI_CONTEXT="$COURSE/L$level/Frozen"
  "$PY" replay_session.py $((level-1)) REPLAY_PLAN_K1_FROZEN.json
done
