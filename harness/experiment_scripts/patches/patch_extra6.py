"""Web lookup without the gold grouping (histwebng): as histweb (patch_extra5.py), but the hidden class and any list
with the same members are removed from the lookup (SEARCH_NOGOLD.txt). Tests whether the lookup acts as an answer key.
Requires patch_extra.py .. patch_extra5.py. Writes run_stage_a_extra6.py, build_replay_extra6.py, score_extra6.py.
Usage: patch_extra6.py <assembled baseline dir>"""
import sys
from pathlib import Path

B = Path(sys.argv[1])
assert (B / "SEARCH_NOGOLD.txt").exists(), "run make_search.py first"
PERSONA_OLD = " return text\n"
PERSONA_NEW = (" if method=='histwebng':\n"
               "  text+='\\nWEB LOOKUP (named groupings published on the Web that include each label\\'s example value):\\n'+(ROOT.parent/'SEARCH_NOGOLD.txt').read_text().strip()\n"
               "  if state.get('text'):text+='\\nYour earlier practice attempts and the feedback they received:\\n'+state['text']\n"
               " return text\n")
for h in ("harness_self_v0", "harness_hint_v0", "harness_k1_test"):
    p = B / h / "common.py"
    s = p.read_text()
    if "'histwebng'" in s:
        continue
    assert "'histweb']" in s, "apply patch_extra5 first"
    s = s.replace("'histweb']", "'histweb','histwebng']", 1)
    i = s.rindex(PERSONA_OLD)
    s = s[:i] + PERSONA_NEW + s[i + len(PERSONA_OLD):]
    p.write_text(s)
for h in ("harness_self_v0", "harness_k1_test"):
    p = B / h / "methods_r3.py"
    s = p.read_text()
    if '"histwebng"' in s:
        continue
    s = s.replace('"hist": hist_update,', '"hist": hist_update, "histwebng": hist_update,', 1)
    assert '"histwebng"' in s, p
    p.write_text(s)
M = "('histwebng',)"
s = (B / "run_stage_a_extra.py").read_text()
s = s.replace("METHODS=('hist','oracle')", f"METHODS={M}").replace("control_stage_a_extra", "control_stage_a_extra6")
assert M in s
(B / "run_stage_a_extra6.py").write_text(s)
s = (B / "build_replay_extra.py").read_text().replace("methods=('hist','oracle')", f"methods={M}")
assert M in s
(B / "build_replay_extra6.py").write_text(s)
s = (B / "score_extra.py").read_text().replace("methods=('hist','oracle')", f"methods={M}").replace("SCORES_EXTRA.json", "SCORES_EXTRA6.json")
assert M in s and "SCORES_EXTRA6.json" in s
(B / "score_extra6.py").write_text(s)
print("extra6 patched", B)
