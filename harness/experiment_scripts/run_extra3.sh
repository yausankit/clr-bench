#!/bin/bash
# Class-name oracle (patch_extra3.py), self arm. Stage A runs at once; stage B waits until this chain's history+lesson
# run (run_extra2.sh) has finished, because both temporarily replace the replay plan. Usage: run_extra3.sh <chain>
C=$1
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_fb
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
cd $B
CH=$(grep -P "^$C\t" $AG/baselines_final/CHAINS.tsv | cut -f2)
python3 $ROOT/patch_extra3.py $B $CH
$PY run_stage_a_extra3.py > stage_a_extra3.log 2>&1 || true
until grep -q "DONEX2 $C " $ROOT/logs/DONEX2.txt 2>/dev/null; do sleep 30; done
$PY build_replay_extra3.py > build_plan_extra3.log 2>&1
$PY run_stage_b.py > stage_b_extra3.log 2>&1
cp REPLAY_PLAN_K1_TRAJ.main.json REPLAY_PLAN_K1_TRAJ.json; cp harness_k1_test/REPLAY_PLAN_K1_TRAJ.main.json harness_k1_test/REPLAY_PLAN_K1_TRAJ.json
$PY score_extra3.py > score_extra3.log 2>&1
echo "DONEX3 $C $(date)" >> $ROOT/logs/DONEX3.txt
