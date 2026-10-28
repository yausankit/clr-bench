#!/bin/bash
# Rewarded-generalization practice (patch_rg.py already applied): ACE, GEPA (neutral note), Dynamic Cheatsheet and the
# history reference, self arm, levels 1-4, scored on version 0. Usage: run_rg.sh <chain>
C=$1
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_rg
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
cd $B
if [ ! -f RG_READY ]; then
  for h in harness_self_v0 harness_hint_v0; do
    sed -i "s/(for example the sum over all entities instead of the largest total)/(for example a different aggregation over the entities)/" $h/methods_r3.py
    grep -q "a different aggregation over the entities" $h/methods_r3.py
    sed -i "s/os.environ.get('CLR_BUNDLE','bundle_k1_v0')/os.environ.get('CLR_BUNDLE','bundle_k1_v0_rg')/" $h/evaluator.py
    grep -q "bundle_k1_v0_rg" $h/evaluator.py
  done
  python3 - <<PY
import json,re
from pathlib import Path
c=json.loads(Path('CONFIG.json').read_text()); c['levels']=[1,2,3,4]; Path('CONFIG.json').write_text(json.dumps(c,indent=2))
M="('ace','gepa','dc','hist')"
for f,pat in (('run_stage_a.py',r"METHODS=\([^)]*\);MODES=\([^)]*\)"),('build_replay_plan.py',r"methods=\([^)]*\)"),('score_all.py',r"methods=\([^)]*\)")):
    s=Path(f).read_text()
    rep={"run_stage_a.py":f"METHODS={M};MODES=('self',)"}.get(f,f"methods={M}")
    s=re.sub(pat,rep,s)
    s=s.replace("for mode in ('self','hint'):","for mode in ('self',):").replace("for version in (0,1,2):","for version in (0,):")
    Path(f).write_text(s)
PY
  touch RG_READY
fi
export NC100_MAX_LEVEL=4
$PY run_stage_a.py > stage_a_rg.log 2>&1 || true
$PY build_replay_plan.py > build_plan_rg.log 2>&1
$PY run_stage_b.py > stage_b_rg.log 2>&1
$PY score_all.py > score_rg.log 2>&1
echo "DONERG $C $(date)" >> $ROOT/logs/DONE.txt
