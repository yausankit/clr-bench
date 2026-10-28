#!/bin/bash
# Rebuild universes/, lists/, salience/ and SPOTCHECK.tsv from raw/ (guide sections 1-3, 7).
# The salience tables are rebuilt from salience/raw/ and merged into lists/ by clrsynth.
set -euo pipefail
cd "$(dirname "$0")"
PY=../../venv/bin/python
$PY build_universe_tld.py
$PY build_universe_port.py
$PY build_universe_catalog.py
$PY build_lists.py
$PY build_add_lists.py
$PY build_tld_groups.py
$PY build_salience.py
(cd ../../code && ../venv/bin/python -m clrsynth salience LG --inputs-root ../inputs)
$PY build_spotcheck.py
$PY build_add_spotcheck.py
$PY apply_add_config.py
