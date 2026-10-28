#!/bin/bash
# Explicit practice feedback (patch_feedback.py): ACE, GEPA (format note) and Dynamic Cheatsheet, self and +lesson, on one
# final chain: assemble -> patch -> reuse the frozen agent -> stage A -> replay plan -> stage B -> score. Usage: run_fb.sh <chain>. Re-entrant.
C=$1
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_fb
OLD=$AG/baselines_final/$C
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
CH=$(grep -P "^$C\t" $AG/baselines_final/CHAINS.tsv | cut -f2)
GW=$(python3 -c "import json;print(json.load(open(\"$OLD/CONFIG.json\"))[\"gateway_url\"])")
P=$(echo $GW | sed -E "s#http://localhost:([0-9]+).*#\1#"); BP=$(echo $GW | sed -E "s#http://localhost:[0-9]+##")
if [ ! -f "$B/CONFIG.json" ]; then
  $PY $AG/baseline_tool_v4/assemble.py $CH $B --gateway-url $GW --gateway-port $P --gateway-base-path $BP > $ROOT/logs/${C}_assemble.log 2>&1
  grep -q "\"pass_\": true" $ROOT/logs/${C}_assemble.log
  python3 $ROOT/patch_feedback.py $B $CH
  python3 $AG/baselines_gepa2/patch_gepa.py $B
  diff <(grep -v HINT $B/harness_self_v0/methods_r3.py) <(grep -v HINT $B/harness_hint_v0/methods_r3.py) > $ROOT/logs/${C}_selfhint.diff || true
  cp -r $OLD/frozen_k1_v0 $B/
  for f in run_stage_a.py build_replay_plan.py score_all.py; do sed -i -E "s/(METHODS|methods)=\(([^)]*)\)/\1=('ace','gepa','dc')/" $B/$f; done
fi
cd $B
grep -n "METHODS=\|methods=" run_stage_a.py build_replay_plan.py score_all.py | head -3
$PY run_stage_a.py > stage_a.log 2>&1 || true
$PY build_replay_plan.py > build_plan.log 2>&1
$PY run_stage_b.py > stage_b.log 2>&1
$PY score_all.py > score_all.log 2>&1
echo "DONE $C $(date)" >> $ROOT/logs/DONE.txt
