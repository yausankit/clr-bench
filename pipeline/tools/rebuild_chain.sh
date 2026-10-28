#!/bin/bash
# Rebuild a released chain from its pinned slots (data/chains/<chain>/STATE.json) without any model call and compare
# every built file and every input file with the chain's MANIFEST.sha256.
# Usage: pipeline/tools/rebuild_chain.sh <chain> [work dir]     (run from the repository root)
set -e
C=$1; W=${2:-pipeline}
REPO="$(cd "$(dirname "$0")/../.." && pwd)"
mkdir -p "$W"; W="$(cd "$W" && pwd)"
ROW=$(awk -F'\t' -v c="$C" '$1==c' "$REPO/data/CHAINS.tsv")
[ -n "$ROW" ] || { echo "unknown chain $C"; exit 1; }
DS=$(echo "$ROW" | cut -f2); BID=$(echo "$ROW" | cut -f4); CFG=$(echo "$ROW" | cut -f5)
DSDIR=$(dirname "$(dirname "$CFG")")   # inputs/<DS> or inputs_alt/<DS>
if [ "$DS" = SY ] && [ ! -d "$REPO/pipeline/inputs/SY/sources/synthea" ]; then
  tar -xzf "$REPO/pipeline/inputs/SY/sources/synthea.tar.gz" -C "$REPO/pipeline/inputs/SY/sources"
fi
OUT="$W/out/$DS/$BID"
mkdir -p "$OUT"
python3 - "$REPO/data/chains/$C/STATE.json" "$OUT/STATE.json" <<'PY'
import json, sys
s = json.load(open(sys.argv[1])); s["_path"] = sys.argv[2]
json.dump(s, open(sys.argv[2], "w"), indent=1)
PY
(cd "$REPO/pipeline" && python3 -m clrsynth build "$CFG" --out-root "$W")
M="$REPO/data/chains/$C/MANIFEST.sha256"
(cd "$OUT" && grep -v " input:" "$M" | shasum -a 256 -c --quiet) && echo "$C: built files match the manifest"
# input files; those edited for release (pipeline/SANITIZED.md) are skipped
SKIP=$(grep -o "\`$DSDIR/[^\`]*\`" "$REPO/pipeline/SANITIZED.md" | tr -d '\`' | sed "s#^$DSDIR/##")
(cd "$REPO/pipeline/$DSDIR" && grep " input:" "$M" | sed 's# input:# #' | grep -v -F -x -f <(for f in $SKIP; do grep " input:$f\$" "$M" | sed 's# input:# #'; done) \
  | shasum -a 256 -c --quiet) && echo "$C: input files match the manifest (skipped as edited for release: $(echo ${SKIP:-none}))"
