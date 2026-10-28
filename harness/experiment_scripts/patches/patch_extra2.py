"""Third reference condition (self arm): histhint = the correct lesson plus the raw practice history in the solver
prompt, i.e. the hint text together with the feedback evidence it refers to. Upper reference for what the base model
can do with this evidence. Requires patch_extra.py to have been applied (reuses _history_text).
Also writes run_stage_a_extra2.py, build_replay_extra2.py and score_extra2.py.
Usage: patch_extra2.py <assembled baseline dir>"""
import re
import sys
from pathlib import Path

B = Path(sys.argv[1])
PERSONA_OLD = " return text\n"
PERSONA_NEW = (" if method=='histhint':\n"
               "  text+='\\nVERIFIED LESSON (correct, from the task designers):\\n'+(ROOT.parent/'HINT_NC100.txt').read_text().strip()\n"
               "  if state.get('text'):text+='\\nYour earlier practice attempts and the feedback they received:\\n'+state['text']\n"
               " return text\n")
for h in ("harness_self_v0", "harness_hint_v0", "harness_k1_test"):
    p = B / h / "common.py"
    s = p.read_text()
    if "'histhint'" in s:
        continue
    assert "'oracle'" in s, "apply patch_extra.py first"
    s = s.replace("'hist','oracle']", "'hist','oracle','histhint']")
    i = s.rindex(PERSONA_OLD)
    s = s[:i] + PERSONA_NEW + s[i + len(PERSONA_OLD):]
    p.write_text(s)
for h in ("harness_self_v0", "harness_k1_test"):
    p = B / h / "methods_r3.py"
    s = p.read_text()
    if '"histhint"' in s:
        continue
    assert '"hist": hist_update' in s, "apply patch_extra.py first"
    s = s.replace('"hist": hist_update,', '"hist": hist_update, "histhint": hist_update,')
    p.write_text(s)
s = (B / "run_stage_a_extra.py").read_text()
s = s.replace("METHODS=('hist','oracle')", "METHODS=('histhint',)").replace("control_stage_a_extra", "control_stage_a_extra2")
assert "('histhint',)" in s
(B / "run_stage_a_extra2.py").write_text(s)
s = (B / "build_replay_extra.py").read_text().replace("methods=('hist','oracle')", "methods=('histhint',)")
assert "('histhint',)" in s
(B / "build_replay_extra2.py").write_text(s)
s = (B / "score_extra.py").read_text().replace("methods=('hist','oracle')", "methods=('histhint',)")
s = s.replace("SCORES_EXTRA.json", "SCORES_EXTRA2.json")
assert "('histhint',)" in s and "SCORES_EXTRA2.json" in s
(B / "score_extra2.py").write_text(s)
print("extra2 patched", B)
