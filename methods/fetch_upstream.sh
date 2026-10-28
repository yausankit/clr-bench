#!/bin/bash
# Clone the upstream method repositories into methods/upstream/{ace,gepa,EvoSkill} (imported at run time by the
# adapters). Checks out the last commit on or before the snapshot date unless *_REF is set.
set -e
D="$(cd "$(dirname "$0")" && pwd)/upstream"
DATE=${SNAPSHOT_DATE:-2026-09-18}
mkdir -p "$D"
fetch() {  # name url ref
  [ -d "$D/$1/.git" ] || git clone --quiet "$2" "$D/$1"
  ref=$3
  [ -n "$ref" ] || ref=$(git -C "$D/$1" rev-list -n 1 --before="$DATE 23:59:59" HEAD)
  git -C "$D/$1" checkout --quiet "$ref"
  echo "$1 $(git -C "$D/$1" rev-parse HEAD)"
}
fetch ace https://github.com/ace-agent/ace "${ACE_REF:-}"
fetch gepa https://github.com/gepa-ai/gepa "${GEPA_REF:-}"
fetch EvoSkill https://github.com/sentient-agi/EvoSkill "${EVOSKILL_REF:-}"
