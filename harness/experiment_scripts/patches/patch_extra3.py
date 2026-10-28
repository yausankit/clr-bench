"""Class-name oracle (self arm): the solver prompt names the hidden class behind every label ("review queue B8 stands for:
Founding member airlines of Star Alliance"), with no feedback history. It measures the knowledge ceiling: the base model
applying a class it is told by name, which is what the screening probe certifies it can list.
Writes CLASS_NAMES.txt from the chain's CHAIN.json and CONCEPTS.json, patches the three harness copies, and writes
run_stage_a_extra3.py, build_replay_extra3.py, score_extra3.py. Requires patch_extra.py (for the self-arm drivers).
Usage: patch_extra3.py <assembled baseline dir> <chain dir>"""
import json
import sys
from pathlib import Path

B, CH = Path(sys.argv[1]), Path(sys.argv[2])
chain = json.loads((CH / "CHAIN.json").read_text())
concepts = json.loads((CH / "CONCEPTS.json").read_text())
lines = [f"{s['label']} stands for: {concepts['L' + str(s['level'])]['name']}" for s in chain["slots"]]
(B / "CLASS_NAMES.txt").write_text("\n".join(lines) + "\n")

PERSONA_OLD = " return text\n"
PERSONA_NEW = (" if method=='nameoracle':\n"
               "  text+='\\nLABEL MEANINGS (correct, from the task designers):\\n'+(ROOT.parent/'CLASS_NAMES.txt').read_text().strip()\n"
               "  text+='\\nApply each rule to every described value that belongs to the named grouping, and to no other value.'\n"
               " return text\n")
for h in ("harness_self_v0", "harness_hint_v0", "harness_k1_test"):
    p = B / h / "common.py"
    s = p.read_text()
    if "'nameoracle'" in s:
        continue
    assert "'oracle'" in s, "apply patch_extra.py first"
    s = s.replace("'hist','oracle'", "'hist','oracle','nameoracle'", 1)
    i = s.rindex(PERSONA_OLD)
    s = s[:i] + PERSONA_NEW + s[i + len(PERSONA_OLD):]
    p.write_text(s)
for h in ("harness_self_v0", "harness_k1_test"):
    p = B / h / "methods_r3.py"
    s = p.read_text()
    if '"nameoracle"' in s:
        continue
    s = s.replace('"oracle": oracle_update}[', '"oracle": oracle_update, "nameoracle": oracle_update}[')
    assert '"nameoracle"' in s, p
    p.write_text(s)
s = (B / "run_stage_a_extra.py").read_text()
s = s.replace("METHODS=('hist','oracle')", "METHODS=('nameoracle',)").replace("control_stage_a_extra", "control_stage_a_extra3")
assert "('nameoracle',)" in s
(B / "run_stage_a_extra3.py").write_text(s)
s = (B / "build_replay_extra.py").read_text().replace("methods=('hist','oracle')", "methods=('nameoracle',)")
assert "('nameoracle',)" in s
(B / "build_replay_extra3.py").write_text(s)
s = (B / "score_extra.py").read_text().replace("methods=('hist','oracle')", "methods=('nameoracle',)")
s = s.replace("SCORES_EXTRA.json", "SCORES_EXTRA3.json")
assert "('nameoracle',)" in s
(B / "score_extra3.py").write_text(s)
print("extra3 patched", B)
