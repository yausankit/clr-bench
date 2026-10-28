#!/bin/bash
# Text added to the update step of ACE and Dynamic Cheatsheet (hint arm), levels 1-4, scored on version 0.
# lessn: the whole lesson; convn: its convention part; procn: its procedure part -- all three under one neutral heading
# ("UPDATE NOTE:") instead of "VERIFIED LESSON (correct, from the task designers):".
# namem: the class name behind each label (CLASS_NAMES.txt) under "LABEL MEANINGS (correct, from the task designers):".
# Usage: run_variant2.sh <lessn|convn|procn|namem> <chain>
V=$1; C=$2
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_$V
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
mkdir -p $ROOT/logs
if [ ! -f $B/VARIANT_READY ]; then
  rsync -a --exclude 'runs_*' --exclude 'control_*' --exclude programs_scored --exclude executions --exclude '*.log' --exclude 'SCORES*' --exclude 'scores_*' $AG/baselines_fb/$C/ $B/
  cd $B
  case $V in
    lessn) HEAD="UPDATE NOTE:" ;;
    convn) cp LESSON_CONV.txt HINT_NC100.txt; HEAD="UPDATE NOTE:" ;;
    procn) cp LESSON_PROC.txt HINT_NC100.txt; HEAD="UPDATE NOTE:" ;;
    namem) cp CLASS_NAMES.txt HINT_NC100.txt; HEAD="LABEL MEANINGS (correct, from the task designers):" ;;
    *) echo "unknown variant $V"; exit 1 ;;
  esac
  for f in harness_hint_v0/methods_r3.py harness_hint_v0/evo_methods.py; do
    sed -i "s/VERIFIED LESSON (correct, from the task designers):/$HEAD/g" $f
    ! grep -q "VERIFIED LESSON" $f
  done
  python3 - <<PY
import json,re
from pathlib import Path
c=json.loads(Path('CONFIG.json').read_text()); c['levels']=[1,2,3,4]; Path('CONFIG.json').write_text(json.dumps(c,indent=2))
M="('ace','dc')"
for f,pat in (('run_stage_a.py',r"METHODS=\([^)]*\);MODES=\([^)]*\)"),('build_replay_plan.py',r"methods=\([^)]*\)"),('score_all.py',r"methods=\([^)]*\)")):
    s=Path(f).read_text()
    rep={"run_stage_a.py":f"METHODS={M};MODES=('hint',)"}.get(f,f"methods={M}")
    s,n=re.subn(pat,rep,s); assert n>=1,(f,n)
    s=s.replace("for mode in ('self','hint'):","for mode in ('hint',):").replace("for version in (0,1,2):","for version in (0,):")
    Path(f).write_text(s)
PY
  touch VARIANT_READY
fi
cd $B
export NC100_MAX_LEVEL=4
$PY run_stage_a.py > stage_a_$V.log 2>&1 || true
$PY build_replay_plan.py > build_plan_$V.log 2>&1
$PY run_stage_b.py > stage_b_$V.log 2>&1
$PY score_all.py > score_$V.log 2>&1
echo "DONE$V $C $(date)" >> $ROOT/logs/DONE.txt
