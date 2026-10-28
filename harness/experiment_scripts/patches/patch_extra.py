"""Two reference conditions on top of the explicit-feedback harness (self arm only).
hist:   method-free baseline. Its update makes no model call: the state is the full practice history so far (each
        attempt's program and the feedback message, inputs omitted), which goes verbatim into the solver prompt.
oracle: the correct lesson (HINT_NC100.txt, the same text the hint condition gives the update step) is placed directly
        in the solver prompt from the start and never changes: the ceiling for this model and task.
Also writes run_stage_a_extra.py, build_replay_extra.py and score_extra.py (self arm, hist and oracle only).
Usage: patch_extra.py <assembled baseline dir>"""
import re
import sys
from pathlib import Path

B = Path(sys.argv[1])

COMMON_INIT_OLD = " return dict(text='')\n"
COMMON_INIT_NEW = (" if method=='oracle':return dict(text=(ROOT.parent/'HINT_NC100.txt').read_text().strip())\n"
                   " return dict(text='')\n")
PERSONA_OLD = " return text\n"
PERSONA_NEW = (" if method=='hist' and state.get('text'):"
               "text+='\\nYour earlier practice attempts and the feedback they received:\\n'+state['text']\n"
               " if method=='oracle' and state.get('text'):"
               "text+='\\nVERIFIED LESSON (correct, from the task designers):\\n'+state['text']\n"
               " return text\n")
for h in ("harness_self_v0", "harness_hint_v0", "harness_k1_test"):
    p = B / h / "common.py"
    s = p.read_text()
    if "'oracle'" in s:
        continue
    s = s.replace("METHODS=['frozen','ace','gepa','evoskill','dc','rb','tfgrpo']",
                  "METHODS=['frozen','ace','gepa','evoskill','dc','rb','tfgrpo','hist','oracle']")
    assert s.count(COMMON_INIT_OLD) == 1 and s.rstrip().endswith("return text"), p
    s = s.replace(COMMON_INIT_OLD, COMMON_INIT_NEW)
    i = s.rindex(PERSONA_OLD)
    s = s[:i] + PERSONA_NEW + s[i + len(PERSONA_OLD):]
    p.write_text(s)

UPD = '''
def _history_text(history):
    import re as _re
    blocks = []
    for h in history:
        verdict = (h.get("feedback") or {}).get("verdict", "")
        verdict = _re.sub(r"Input:\\n.*?\\nExpected result", "Expected result", verdict, flags=_re.S)
        blocks.append(f"[Level {h.get('level')}, attempt {h.get('attempt')}]\\nYour program:\\n"
                      f"{h.get('assistant_final', '')}\\nFeedback:\\n{verdict}")
    return "\\n\\n".join(blocks)


def hist_update(native, sid, level, state, history, folder):
    new = {"text": _history_text(history)}
    dump(Path(folder) / "UPDATE.json", dict(method="hist", changed=new != state, mechanism="verbatim_history",
                                            reflection_calls=0))
    return new


def oracle_update(native, sid, level, state, history, folder):
    dump(Path(folder) / "UPDATE.json", dict(method="oracle", changed=False, mechanism="fixed_lesson",
                                            reflection_calls=0))
    return copy.deepcopy(state)


def update(method, native, sid, level, state, history, folder):'''
DEF = "\ndef update(method, native, sid, level, state, history, folder):"
for h in ("harness_self_v0", "harness_k1_test"):
    p = B / h / "methods_r3.py"
    s = p.read_text()
    if "hist_update" in s:
        continue
    assert s.count(DEF) == 1, p
    s = s.replace(DEF, UPD, 1)
    s = s.replace('"dc": dc_update, "rb": rb_update, "tfgrpo": tfgrpo_update}[',
                  '"dc": dc_update, "rb": rb_update, "tfgrpo": tfgrpo_update, "hist": hist_update, '
                  '"oracle": oracle_update}[')
    assert '"hist": hist_update' in s, p
    p.write_text(s)

# self-arm-only drivers for the two conditions
s = (B / "run_stage_a.py").read_text()
s = re.sub(r"METHODS=\([^)]*\);MODES=\([^)]*\)", "METHODS=('hist','oracle');MODES=('self',)", s)
s = s.replace("control=D/'control_stage_a'", "control=D/'control_stage_a_extra'")
assert "('hist','oracle')" in s
(B / "run_stage_a_extra.py").write_text(s)
s = (B / "build_replay_plan.py").read_text()
s = re.sub(r"methods=\([^)]*\)", "methods=('hist','oracle')", s).replace("for mode in ('self','hint'):",
                                                                         "for mode in ('self',):")
assert "for mode in ('self',):" in s
(B / "build_replay_extra.py").write_text(s)
s = (B / "score_all.py").read_text()
s = re.sub(r"methods=\([^)]*\)", "methods=('hist','oracle')", s).replace("for mode in ('self','hint'):",
                                                                         "for mode in ('self',):")
s = s.replace("for version in (0,1,2):", "for version in (0,):").replace("SCORES_ALL.json", "SCORES_EXTRA.json")
assert "SCORES_EXTRA.json" in s and "for version in (0,):" in s
(B / "score_extra.py").write_text(s)
print("extra patched", B)
