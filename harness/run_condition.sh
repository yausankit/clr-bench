#!/bin/bash
# Run learning conditions for one chain, levels 1-4, scored on version 0 (the protocol of the paper):
#   setup run dir -> stage A (practice, every method updates its state) -> replay plan -> stage B (test replay of each
#   learned state) -> scoring with the chain's score_k1_v3.py (writes SCORES_ALL.json).
# Usage: harness/run_condition.sh <chain> <out root> "<python list of (mode, method) pairs>" [setup_run.py options]
#   mode:   self (learning from feedback alone) or hint (+lesson appended to every update input)
#   method: ace gepa dc tfgrpo evoskill rb, or the method-free references hist (history), oracle, histhint
#           (history + lesson), histconv, histproc, nameoracle, nameproc, webonly, histweb, histwebng
# Example: harness/run_condition.sh TR1 runs/luna "[('self','ace'),('hint','ace'),('self','hist')]" \
#            --gateway-url http://localhost:42802/CLR --model gpt-6-luna
# Environment: CLRBENCH_GEPA_NOTE=neutral|explicit|none (default neutral); CLR_BUNDLE=bundle_k1_v0_rg for rewarded
# practice (stage A only). Start harness/gateway.py first. Re-entrant: finished sessions are reused.
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
  touch LEARN_READY
fi
cd "$B"
"$PY" run_stage_a.py > stage_a.log 2>&1 || true   # CLR_BUNDLE (rewarded practice) applies to practice only
unset CLR_BUNDLE
"$PY" build_replay_plan.py > build_plan.log 2>&1
"$PY" run_stage_b.py > stage_b.log 2>&1
"$PY" score_all.py > score.log 2>&1
echo "DONE $C $(date)"
