#!/bin/bash
# Run learning conditions on one chain with the paper's protocol (levels 1-4, instance version 0):
#   setup_run.py -> stage A (practice: up to three attempts per level, the method updates its state after every
#   attempt) -> replay plan -> stage B (each learned state writes the level's test program) -> scoring with the chain's
#   scorer (level accuracy, single cells, value-level diagnostics; written to SCORES_ALL.json).
# Usage: harness/run_condition.sh <chain> <out root> "<python list of (mode, method) pairs>" [setup_run.py options]
#   mode:   self (learning from feedback alone) or hint (+ lesson: the lesson is appended to every update input)
#   method: ace gepa dc tfgrpo evoskill rb, or the method-free references
#           hist (raw practice history), histhint (history + lesson), histconv / histproc (history + one part of the
#           lesson), nameoracle (class-name oracle)
# Example: harness/run_condition.sh TR1 runs/luna "[('self','ace'),('hint','ace'),('self','hist')]" \
#            --gateway-url http://localhost:42802/CLR --model gpt-6-luna
# Environment:
#   CLRBENCH_GEPA_NOTE=neutral|explicit|none   GEPA format note (default neutral, as in the main results)
#   CLR_BUNDLE=bundle_k1_v0_rg                 rewarded practice: m1 also appears in practice from the second attempt
#   CLR_VARIANT=lessn|convn|procn|namem|convl1 text added to the update step (harness/variants.py), with hint pairs
# Start harness/gateway.py first. The script is re-entrant: finished sessions are reused.
set -e
C=$1; ROOT=$2; Q=$3; shift 3
REPO="$(cd "$(dirname "$0")/.." && pwd)"
B="$ROOT/$C"
PY=${PYTHON:-python3}
if [ ! -f "$B/LEARN_READY" ]; then
  "$PY" "$REPO/harness/setup_run.py" "$C" --out "$B" --python "$PY" "$@"
  cd "$B"
  "$PY" - "$Q" <<'PY'
import re, sys
from pathlib import Path
Q = sys.argv[1]
s = Path('run_stage_a.py').read_text()
s = re.sub(r"queue=\[\(mode,method\) for mode in MODES for method in METHODS\]", "queue=" + Q, s)
assert "queue=" + Q in s
Path('run_stage_a.py').write_text(s)
for f in ('build_replay_plan.py', 'score_all.py'):
    s = Path(f).read_text()
    a = "for mode in ('self','hint'):\n for method in methods:"
    assert a in s, f
    Path(f).write_text(s.replace(a, "for mode, method in " + Q + ":\n if True:"))
PY
  if [ -n "$CLR_VARIANT" ]; then "$PY" "$REPO/harness/variants.py" "$B" "$CLR_VARIANT"; fi
  touch LEARN_READY
fi
cd "$B"
"$PY" run_stage_a.py > stage_a.log 2>&1 || true   # CLR_BUNDLE (rewarded practice) applies to practice only
unset CLR_BUNDLE
"$PY" build_replay_plan.py > build_plan.log 2>&1
"$PY" run_stage_b.py > stage_b.log 2>&1
"$PY" score_all.py > score.log 2>&1
echo "DONE $C $(date)"
