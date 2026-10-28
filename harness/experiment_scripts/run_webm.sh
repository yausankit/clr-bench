#!/bin/bash
# Methods with the Web lookup in their update step (second review round, both reviewers): the +lesson arm of ACE, GEPA
# (neutral note) and Dynamic Cheatsheet, with the lesson text replaced by the chain's SEARCH.txt and the heading
# "VERIFIED LESSON ..." replaced by a Web-lookup heading. Levels 1-4, scored on version 0. Usage: run_webm.sh <chain>
C=$1
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_webm
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
mkdir -p $ROOT/logs
if [ ! -f $B/WEBM_READY ]; then
  rsync -a --exclude 'runs_*' --exclude 'control_*' --exclude programs_scored --exclude executions --exclude '*.log' --exclude 'SCORES*' --exclude 'scores_*' $AG/baselines_fb/$C/ $B/
  cd $B
  cp SEARCH.txt HINT_NC100.txt
  for f in harness_hint_v0/methods_r3.py harness_hint_v0/evo_methods.py; do
    sed -i "s/VERIFIED LESSON (correct, from the task designers):/WEB LOOKUP (named groupings published on the Web that include each label's example value):/g" $f
    ! grep -q "VERIFIED LESSON" $f
  done
  sed -i "s/(for example the sum over all entities instead of the largest total)/(for example a different aggregation over the entities)/" harness_hint_v0/methods_r3.py
  grep -q "a different aggregation over the entities" harness_hint_v0/methods_r3.py
  python3 - <<PY
import json,re
from pathlib import Path
c=json.loads(Path('CONFIG.json').read_text()); c['levels']=[1,2,3,4]; Path('CONFIG.json').write_text(json.dumps(c,indent=2))
M="('ace','gepa','dc')"
for f,pat in (('run_stage_a.py',r"METHODS=\([^)]*\);MODES=\([^)]*\)"),('build_replay_plan.py',r"methods=\([^)]*\)"),('score_all.py',r"methods=\([^)]*\)")):
    s=Path(f).read_text()
    rep={"run_stage_a.py":f"METHODS={M};MODES=('hint',)"}.get(f,f"methods={M}")
    s=re.sub(pat,rep,s)
    s=s.replace("for mode in ('self','hint'):","for mode in ('hint',):").replace("for version in (0,1,2):","for version in (0,):")
    Path(f).write_text(s)
PY
  touch WEBM_READY
fi
cd $B
export NC100_MAX_LEVEL=4
$PY run_stage_a.py > stage_a_webm.log 2>&1 || true
$PY build_replay_plan.py > build_plan_webm.log 2>&1
$PY run_stage_b.py > stage_b_webm.log 2>&1
$PY score_all.py > score_webm.log 2>&1
echo "DONEWEBM $C $(date)" >> $ROOT/logs/DONE.txt
