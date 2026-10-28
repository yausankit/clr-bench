"""Lesson ablations (self arm, second review round). Three method-free references:
nameproc = class-name oracle plus the lesson's procedure sentence (enumerate every described value and hard-code the
member set), so that the oracle and the lesson differ only in naming the class;
histconv = raw practice history plus only the convention part of the lesson (labels denote named groupings);
histproc = raw practice history plus only a procedure part without the named-grouping convention.
All lesson parts use the same header as History + lesson. Requires patch_extra.py, patch_extra2.py, patch_extra3.py.
Writes run_stage_a_extra4.py, build_replay_extra4.py, score_extra4.py (SCORES_EXTRA4.json).
Usage: patch_extra4.py <assembled baseline dir>"""
import sys
from pathlib import Path

B = Path(sys.argv[1])
CONV = ("When a level rule applies to a labelled class and the report gives only one example value, the class is a "
        "real-world category that the label does not name: a named grouping that exists in this domain, such as an "
        "organisation, an alliance, an official list or a standard classification. Feedback that another value is treated "
        "like the example, and that some other value is not, tells you which category it is: choose the best-known named "
        "grouping that contains the example and the confirmed value and excludes the rejected one. Do not construct a "
        "category from a property you read in the descriptions, such as a region, a type of government, a climate or a size.")
PROC = ("When a level rule applies to a labelled class and the report gives only one example value, decide which class "
        "the example and the feedback point to and write it into your notes together with the label. Then apply the rule "
        "to every value the report describes that belongs to that class, including values that never appeared in feedback, "
        "and leave out values that are not in it. Before coding, go through every described value, decide membership for "
        "each one, and hard-code the complete member set.")
NAMEPROC = ("Before coding, go through every described value, decide membership in the named grouping for each one, "
            "and hard-code the complete member set.")
(B / "LESSON_CONV.txt").write_text(CONV + "\n")
(B / "LESSON_PROC.txt").write_text(PROC + "\n")
PERSONA_OLD = " return text\n"
PERSONA_NEW = (" if method=='nameproc':\n"
               "  text+='\\nLABEL MEANINGS (correct, from the task designers):\\n'+(ROOT.parent/'CLASS_NAMES.txt').read_text().strip()\n"
               "  text+='\\nApply each rule to every described value that belongs to the named grouping, and to no other value. '\n"
               f"  text+={NAMEPROC!r}\n"
               " if method in ('histconv','histproc'):\n"
               "  f='LESSON_CONV.txt' if method=='histconv' else 'LESSON_PROC.txt'\n"
               "  text+='\\nVERIFIED LESSON (correct, from the task designers):\\n'+(ROOT.parent/f).read_text().strip()\n"
               "  if state.get('text'):text+='\\nYour earlier practice attempts and the feedback they received:\\n'+state['text']\n"
               " return text\n")
for h in ("harness_self_v0", "harness_hint_v0", "harness_k1_test"):
    p = B / h / "common.py"
    s = p.read_text()
    if "'nameproc'" in s:
        continue
    assert "'histhint']" in s and "'nameoracle'" in s, "apply patch_extra2/3 first"
    s = s.replace("'histhint']", "'histhint','nameproc','histconv','histproc']", 1)
    i = s.rindex(PERSONA_OLD)
    s = s[:i] + PERSONA_NEW + s[i + len(PERSONA_OLD):]
    p.write_text(s)
for h in ("harness_self_v0", "harness_k1_test"):
    p = B / h / "methods_r3.py"
    s = p.read_text()
    if '"nameproc"' in s:
        continue
    s = s.replace('"hist": hist_update,', '"hist": hist_update, "histconv": hist_update, "histproc": hist_update, '
                  '"nameproc": oracle_update,', 1)
    assert '"nameproc"' in s, p
    p.write_text(s)
M = "('nameproc','histconv','histproc')"
s = (B / "run_stage_a_extra.py").read_text()
s = s.replace("METHODS=('hist','oracle')", f"METHODS={M}").replace("control_stage_a_extra", "control_stage_a_extra4")
assert M in s
(B / "run_stage_a_extra4.py").write_text(s)
s = (B / "build_replay_extra.py").read_text().replace("methods=('hist','oracle')", f"methods={M}")
assert M in s
(B / "build_replay_extra4.py").write_text(s)
s = (B / "score_extra.py").read_text().replace("methods=('hist','oracle')", f"methods={M}").replace("SCORES_EXTRA.json", "SCORES_EXTRA4.json")
assert M in s and "SCORES_EXTRA4.json" in s
(B / "score_extra4.py").write_text(s)
print("extra4 patched", B)
