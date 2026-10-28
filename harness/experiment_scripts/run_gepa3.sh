#!/bin/bash
# GEPA under explicit practice feedback, two variants: orig (no note) and neutral (format note without naming the
# test aggregation). Usage: run_gepa3.sh <variant: orig|neutral> <chain>. Reuses Frozen from baselines_final.
V=$1; C=$2
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_gepa3
OLD=$AG/baselines_final/$C
PY=${PYTHON:-python3}
B=$ROOT/$V/$C
set -e
CH=$(grep -P "^$C\t" $AG/baselines_final/CHAINS.tsv | cut -f2)
GW=$(python3 -c "import json;print(json.load(open(\"$OLD/CONFIG.json\"))[\"gateway_url\"])")
P=$(echo $GW | sed -E "s#http://localhost:([0-9]+).*#\1#"); BP=$(echo $GW | sed -E "s#http://localhost:[0-9]+##")
mkdir -p $ROOT/$V
if [ ! -f "$B/CONFIG.json" ]; then
  $PY $AG/baseline_tool_v4/assemble.py $CH $B --gateway-url $GW --gateway-port $P --gateway-base-path $BP > $ROOT/logs/${V}_${C}_assemble.log 2>&1
  grep -q "\"pass_\": true" $ROOT/logs/${V}_${C}_assemble.log
  python3 $AG/baselines_fb/patch_feedback.py $B $CH
  [ "$V" = neutral ] && python3 $ROOT/patch_gepa_neutral.py $B
  cp -r $OLD/frozen_k1_v0 $B/
  for f in run_stage_a.py build_replay_plan.py score_all.py; do sed -i -E "s/(METHODS|methods)=\(([^)]*)\)/\1=('gepa',)/" $B/$f; done
fi
cd $B
$PY run_stage_a.py > stage_a.log 2>&1 || true
$PY build_replay_plan.py > build_plan.log 2>&1
$PY run_stage_b.py > stage_b.log 2>&1
$PY score_all.py > score_all.log 2>&1
echo "DONE $V $C $(date)" >> $ROOT/logs/DONE.txt
