#!/bin/bash
# Second base model (Claude Sonnet 5.5, low reasoning, via an OpenAI-compatible endpoint and harness/gateway.py):
# Frozen, ACE and Dynamic Cheatsheet (self and +lesson), and the history reference, explicit feedback, levels 1-4,
# scored on version 0. Usage: run_sonnet.sh <chain> <gateway port 42811|42812>
C=$1; PORT=$2
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_sonnet
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
mkdir -p $ROOT/logs
if [ ! -f $B/SONNET_READY ]; then
  rsync -a --exclude 'runs_*' --exclude 'control_*' --exclude programs_scored --exclude executions --exclude '*.log' \
        --exclude 'SCORES*' --exclude 'scores_*' --exclude frozen_k1_v0 $AG/baselines_fb/$C/ $B/
  cd $B
  python3 - <<PY
import json,re
from pathlib import Path
c=json.loads(Path('CONFIG.json').read_text())
c.update(levels=[1,2,3,4], gateway_url="http://localhost:$PORT/SONNET", gateway_port=$PORT, gateway_base_path="/SONNET",
         model="claude-sonnet-5-5", reasoning_effort="low")
Path('CONFIG.json').write_text(json.dumps(c,indent=2))
Q="[('self','ace'),('self','dc'),('self','hist'),('hint','ace'),('hint','dc')]"
s=Path('run_stage_a.py').read_text()
s=re.sub(r"queue=\[\(mode,method\) for mode in MODES for method in METHODS\]", "queue="+Q, s)
assert "queue="+Q in s
Path('run_stage_a.py').write_text(s)
for f in ('build_replay_plan.py','score_all.py'):
    s=Path(f).read_text()
    a="for mode in ('self','hint'):\n for method in methods:"
    assert a in s, f
    s=s.replace(a,"for mode, method in "+Q+":\n if True:").replace("for version in (0,1,2):","for version in (0,):")
    Path(f).write_text(s)
PY
  touch SONNET_READY
fi
cd $B
export NC100_MAX_LEVEL=4
# frozen agent with the new model
if [ ! -f FROZEN_DONE ]; then
  PYTHON=$PY bash run_frozen.sh 1 2 3 4 > frozen_sonnet.log 2>&1 && touch FROZEN_DONE
fi
$PY run_stage_a.py > stage_a_sonnet.log 2>&1 || true
$PY build_replay_plan.py > build_plan_sonnet.log 2>&1
$PY run_stage_b.py > stage_b_sonnet.log 2>&1
$PY score_all.py > score_sonnet.log 2>&1
echo "DONESONNET $C $(date)" >> $ROOT/logs/DONE.txt
