#!/bin/bash
# Additional backbone models (frozen agent and class-name oracle), explicit-feedback harness, levels 1-4.
# Usage: run_models.sh <model tag> <gateway port> <chain>
TAG=$1; PORT=$2; C=$3
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_models/$TAG
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
mkdir -p $ROOT/logs
if [ ! -f $B/MODEL_READY ]; then
  rsync -a --exclude 'runs_*' --exclude 'control_*' --exclude programs_scored --exclude executions --exclude '*.log' \
        --exclude 'SCORES*' --exclude 'scores_*' --exclude frozen_k1_v0 $AG/baselines_fb/$C/ $B/
  cd $B
  python3 - <<PY
import json
from pathlib import Path
c=json.loads(Path('CONFIG.json').read_text())
c.update(levels=[1,2,3,4], gateway_url="http://localhost:$PORT/MODELS", gateway_port=$PORT, gateway_base_path="/MODELS", model="$TAG")
Path('CONFIG.json').write_text(json.dumps(c,indent=2))
PY
  cp REPLAY_PLAN_K1_TRAJ.main.json REPLAY_PLAN_K1_TRAJ.json 2>/dev/null || true
  touch MODEL_READY
fi
cd $B
export NC100_MAX_LEVEL=4
[ -f FROZEN_DONE ] || { PYTHON=$PY bash run_frozen.sh 1 2 3 4 > frozen.log 2>&1 && touch FROZEN_DONE; }
$PY run_stage_a_extra3.py > stage_a_oracle.log 2>&1 || true
$PY build_replay_extra3.py > build_plan_oracle.log 2>&1
$PY run_stage_b.py > stage_b_oracle.log 2>&1
$PY score_extra3.py > score_oracle.log 2>&1
echo "DONE $TAG $C $(date)" >> $ROOT/logs/DONE.txt
