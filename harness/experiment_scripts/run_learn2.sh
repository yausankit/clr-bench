#!/bin/bash
# Learning conditions with a chosen queue of (mode, method) pairs on any backbone; GEPA uses the neutral format note
# (as in the paper); the frozen agent is not run. Levels 1-4, scored on version 0.
# Usage: run_learn2.sh <out dir name> <chain> <gateway url> <model tag> "<python list of (mode,method) pairs>"
OUT=$1; C=$2; GW=$3; TAG=$4; Q=$5
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/$OUT
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
mkdir -p $ROOT/logs
if [ ! -f $B/LEARN_READY ]; then
  rsync -a --exclude 'runs_*' --exclude 'control_*' --exclude programs_scored --exclude executions --exclude '*.log' \
        --exclude 'SCORES*' --exclude 'scores_*' --exclude frozen_k1_v0 $AG/baselines_fb/$C/ $B/
  cd $B
  for f in harness_self_v0/methods_r3.py harness_hint_v0/methods_r3.py; do
    sed -i "s/(for example the sum over all entities instead of the largest total)/(for example a different aggregation over the entities)/" $f
    grep -q "a different aggregation over the entities" $f
  done
  python3 - <<PY
import json,re
from pathlib import Path
c=json.loads(Path('CONFIG.json').read_text())
c['levels']=[1,2,3,4]
port=int(re.search(r":(\d+)/","$GW").group(1)); c.update(gateway_url="$GW", gateway_port=port, gateway_base_path="/"+"$GW".rsplit("/",1)[1], model="$TAG")
Path('CONFIG.json').write_text(json.dumps(c,indent=2))
Q='''$Q'''
s=Path('run_stage_a.py').read_text()
s=re.sub(r"queue=\[\(mode,method\) for mode in MODES for method in METHODS\]", "queue="+Q, s); assert "queue="+Q in s
Path('run_stage_a.py').write_text(s)
for f in ('build_replay_plan.py','score_all.py'):
    s=Path(f).read_text(); a="for mode in ('self','hint'):\n for method in methods:"; assert a in s, f
    s=s.replace(a,"for mode, method in "+Q+":\n if True:").replace("for version in (0,1,2):","for version in (0,):")
    Path(f).write_text(s)
PY
  cp REPLAY_PLAN_K1_TRAJ.main.json REPLAY_PLAN_K1_TRAJ.json 2>/dev/null || true
  cp harness_k1_test/REPLAY_PLAN_K1_TRAJ.main.json harness_k1_test/REPLAY_PLAN_K1_TRAJ.json 2>/dev/null || true
  touch LEARN_READY
fi
cd $B
export NC100_MAX_LEVEL=4
$PY run_stage_a.py > stage_a.log 2>&1 || true
$PY build_replay_plan.py > build_plan.log 2>&1
$PY run_stage_b.py > stage_b.log 2>&1
$PY score_all.py > score.log 2>&1
echo "DONE $C $(date)" >> $ROOT/logs/DONE.txt
