"""Web-lookup references (self arm). The solver prompt shows, for each label, the named groupings published on the Web
that contain the label's example value (SEARCH.txt, built by make_search.py from the domain's list library), as a
simulated set-expansion lookup; no convention or procedure is stated.
webonly = lookup results without feedback; histweb = lookup results plus the raw practice history.
Requires patch_extra.py .. patch_extra4.py. Writes run_stage_a_extra5.py, build_replay_extra5.py, score_extra5.py.
Usage: patch_extra5.py <assembled baseline dir>"""
import sys
from pathlib import Path

B = Path(sys.argv[1])
assert (B / "SEARCH.txt").exists(), "run make_search.py first"
PERSONA_OLD = " return text\n"
PERSONA_NEW = (" if method in ('webonly','histweb'):\n"
               "  text+='\\nWEB LOOKUP (named groupings published on the Web that include each label\\'s example value):\\n'+(ROOT.parent/'SEARCH.txt').read_text().strip()\n"
               "  if method=='histweb' and state.get('text'):text+='\\nYour earlier practice attempts and the feedback they received:\\n'+state['text']\n"
               " return text\n")
for h in ("harness_self_v0", "harness_hint_v0", "harness_k1_test"):
    p = B / h / "common.py"
    s = p.read_text()
    if "'webonly'" in s:
        continue
    assert "'histproc']" in s, "apply patch_extra4 first"
    s = s.replace("'histproc']", "'histproc','webonly','histweb']", 1)
    i = s.rindex(PERSONA_OLD)
    s = s[:i] + PERSONA_NEW + s[i + len(PERSONA_OLD):]
    p.write_text(s)
for h in ("harness_self_v0", "harness_k1_test"):
    p = B / h / "methods_r3.py"
    s = p.read_text()
    if '"webonly"' in s:
        continue
    s = s.replace('"hist": hist_update,', '"hist": hist_update, "histweb": hist_update, "webonly": oracle_update,', 1)
    assert '"webonly"' in s, p
    p.write_text(s)
M = "('webonly','histweb')"
s = (B / "run_stage_a_extra.py").read_text()
s = s.replace("METHODS=('hist','oracle')", f"METHODS={M}").replace("control_stage_a_extra", "control_stage_a_extra5")
assert M in s
(B / "run_stage_a_extra5.py").write_text(s)
s = (B / "build_replay_extra.py").read_text().replace("methods=('hist','oracle')", f"methods={M}")
assert M in s
(B / "build_replay_extra5.py").write_text(s)
s = (B / "score_extra.py").read_text().replace("methods=('hist','oracle')", f"methods={M}").replace("SCORES_EXTRA.json", "SCORES_EXTRA5.json")
assert M in s and "SCORES_EXTRA5.json" in s
(B / "score_extra5.py").write_text(s)
print("extra5 patched", B)
