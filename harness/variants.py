#!/usr/bin/env python3
"""Variants of the text added to the update step (Table 8 of the paper), applied to a run directory.

usage: python harness/variants.py RUN_DIR VARIANT

RUN_DIR is a chain's run directory created by harness/setup_run.py. A variant changes only the +lesson arm
(harness_hint_v0/), so it is meant for the ('hint', 'ace') and ('hint', 'dc') conditions:

  lessn   the whole lesson under the neutral heading "UPDATE NOTE:"
  convn   the convention part of the lesson under "UPDATE NOTE:"
  procn   the procedure part of the lesson under "UPDATE NOTE:"
  namem   the class name behind each label, under "LABEL MEANINGS (correct, from the task designers):"
  convl1  the convention under "UPDATE NOTE:" at level 1 only, and no added text from level 2 on

harness/run_condition.sh calls this script when CLR_VARIANT is set.
"""
import sys
from pathlib import Path

HEADING = "VERIFIED LESSON (correct, from the task designers):"
TEXT_FILE = {"lessn": None, "convn": "LESSON_CONV.txt", "procn": "LESSON_PROC.txt", "namem": "CLASS_NAMES.txt",
             "convl1": "LESSON_CONV.txt"}
NEW_HEADING = {"lessn": "UPDATE NOTE:", "convn": "UPDATE NOTE:", "procn": "UPDATE NOTE:",
               "namem": "LABEL MEANINGS (correct, from the task designers):"}
UPDATE_FILES = ("harness_hint_v0/methods_r3.py", "harness_hint_v0/evo_methods.py")


def level1_only(run, path, function):
    """In one update function, add the text only at level 1, under the neutral heading."""
    old = '"\\n' + HEADING + '\\n" + HINT_TEXT'
    new = '(("\\nUPDATE NOTE:\\n" + HINT_TEXT) if int(level) == 1 else "")'
    f = run / path
    s = f.read_text()
    i = s.index("def " + function + "(")
    j = s.index("\ndef ", i + 5)
    body = s[i:j]
    if old not in body:
        raise SystemExit(f"{path}: {function} does not add the lesson as expected")
    f.write_text(s[:i] + body.replace(old, new) + s[j:])


def main():
    if len(sys.argv) != 3 or sys.argv[2] not in TEXT_FILE:
        raise SystemExit(__doc__)
    run, variant = Path(sys.argv[1]).resolve(), sys.argv[2]
    if TEXT_FILE[variant]:
        (run / "HINT_NC100.txt").write_text((run / TEXT_FILE[variant]).read_text())
    if variant == "convl1":
        level1_only(run, "harness_hint_v0/methods_r3.py", "ace_update")
        level1_only(run, "harness_hint_v0/evo_methods.py", "dc_update")
    else:
        for path in UPDATE_FILES:
            f = run / path
            s = f.read_text()
            if HEADING not in s:
                raise SystemExit(f"{path}: lesson heading not found")
            f.write_text(s.replace(HEADING, NEW_HEADING[variant]))
    (run / "VARIANT").write_text(variant + "\n")
    print(f"{run}: variant {variant} applied")


if __name__ == "__main__":
    main()
