#!/bin/bash
# Convention in the update step at level 1 only (neutral heading "UPDATE NOTE:"), nothing at levels 2-4; ACE and Dynamic
# Cheatsheet, hint arm, levels 1-4, scored on version 0. Usage: run_variant3.sh <chain>
V=convl1; C=$1
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_$V
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
mkdir -p $ROOT/logs
if [ ! -f $B/VARIANT_READY ]; then
  rsync -a --exclude "runs_*" --exclude "control_*" --exclude programs_scored --exclude executions --exclude "*.log" --exclude "SCORES*" --exclude "scores_*" $AG/baselines_fb/$C/ $B/
  cd $B
  cp LESSON_CONV.txt HINT_NC100.txt
  python3 - <<PY
import json,re
from pathlib import Path
OLD="\"\\\\nVERIFIED LESSON (correct, from the task designers):\\\\n\" + HINT_TEXT"
NEW="((\"\\\\nUPDATE NOTE:\\\\n\" + HINT_TEXT) if int(level) == 1 else \"\")"
for f,fn in (("harness_hint_v0/methods_r3.py","ace_update"),("harness_hint_v0/evo_methods.py","dc_update")):
    s=Path(f).read_text()
    i=s.index("def "+fn+"("); j=s.index("\ndef ",i+5)
    body=s[i:j]; n=body.count(OLD); assert n>=1,(f,n)
    s=s[:i]+body.replace(OLD,NEW)+s[j:]; Path(f).write_text(s); print(f,fn,"patched",n)
c=json.loads(Path("CONFIG.json").read_text()); c["levels"]=[1,2,3,4]; Path("CONFIG.json").write_text(json.dumps(c,indent=2))
M="(\"ace\",\"dc\")"
for f,pat in (("run_stage_a.py",r"METHODS=\([^)]*\);MODES=\([^)]*\)"),("build_replay_plan.py",r"methods=\([^)]*\)"),("score_all.py",r"methods=\([^)]*\)")):
    s=Path(f).read_text()
    rep={"run_stage_a.py":"METHODS="+M+";MODES=(\"hint\",)"}.get(f,"methods="+M)
    s,n=re.subn(pat,rep,s); assert n>=1,(f,n)
    s=s.replace("for mode in (\"self\",\"hint\"):","for mode in (\"hint\",):").replace("for mode in (\x27self\x27,\x27hint\x27):","for mode in (\x27hint\x27,):").replace("for version in (0,1,2):","for version in (0,):")
    Path(f).write_text(s)
PY
  sed -i "s/(for example the sum over all entities instead of the largest total)/(for example a different aggregation over the entities)/" harness_hint_v0/methods_r3.py
  grep -q "a different aggregation over the entities" harness_hint_v0/methods_r3.py
  sed -i "s/max(status.get(.completed_levels.,\[0\]))/max(status.get(\x27completed_levels\x27) or [0])/" run_stage_a.py
  touch VARIANT_READY
fi
cd $B
export NC100_MAX_LEVEL=4
$PY run_stage_a.py > stage_a_$V.log 2>&1 || true
$PY build_replay_plan.py > build_plan_$V.log 2>&1
$PY run_stage_b.py > stage_b_$V.log 2>&1
$PY score_all.py > score_$V.log 2>&1
echo "DONE$V $C $(date)" >> $ROOT/logs/DONE.txt
