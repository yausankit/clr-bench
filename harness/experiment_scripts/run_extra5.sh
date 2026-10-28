#!/bin/bash
# Web-lookup references (patch_extra5.py), self arm. Usage: run_extra5.sh <chain>. Replaces the replay plan temporarily, so
# it must not run alongside another run_extra*.sh on the same chain.
C=$1
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_fb
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
cd $B
python3 $ROOT/patch_extra5.py $B
$PY run_stage_a_extra5.py > stage_a_extra5.log 2>&1 || true
$PY build_replay_extra5.py > build_plan_extra5.log 2>&1
$PY run_stage_b.py > stage_b_extra5.log 2>&1
cp REPLAY_PLAN_K1_TRAJ.main.json REPLAY_PLAN_K1_TRAJ.json; cp harness_k1_test/REPLAY_PLAN_K1_TRAJ.main.json harness_k1_test/REPLAY_PLAN_K1_TRAJ.json
$PY score_extra5.py > score_extra5.log 2>&1
echo "DONEX5 $C $(date)" >> $ROOT/logs/DONEX5.txt
