#!/bin/bash
# Two reference conditions under explicit practice feedback, self arm only: hist (the practice history verbatim in the
# solver prompt) and oracle (the correct lesson in the solver prompt). Usage: run_extra.sh <chain>. Re-entrant.
C=$1
AG=${CLRBENCH_RUNS:?set CLRBENCH_RUNS to the directory that holds the run roots}
ROOT=$AG/baselines_fb
PY=${PYTHON:-python3}
B=$ROOT/$C
set -e
cd $B
python3 $ROOT/patch_extra.py $B
[ -f REPLAY_PLAN_K1_TRAJ.main.json ] || { cp REPLAY_PLAN_K1_TRAJ.json REPLAY_PLAN_K1_TRAJ.main.json; cp harness_k1_test/REPLAY_PLAN_K1_TRAJ.json harness_k1_test/REPLAY_PLAN_K1_TRAJ.main.json; }
$PY run_stage_a_extra.py > stage_a_extra.log 2>&1 || true
$PY build_replay_extra.py > build_plan_extra.log 2>&1
$PY run_stage_b.py > stage_b_extra.log 2>&1
cp REPLAY_PLAN_K1_TRAJ.main.json REPLAY_PLAN_K1_TRAJ.json; cp harness_k1_test/REPLAY_PLAN_K1_TRAJ.main.json harness_k1_test/REPLAY_PLAN_K1_TRAJ.json
$PY score_extra.py > score_extra.log 2>&1
echo "DONEX $C $(date)" >> $ROOT/logs/DONEX.txt
