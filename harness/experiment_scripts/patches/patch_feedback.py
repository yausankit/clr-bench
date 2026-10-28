"""Explicit practice feedback (option 1): every changed value in a practice counterexample is told whether it belongs to
the level label like the rule example. Only practice-side values of version 0 appear (the revealed member m_0 and the
non-member N_p); the existing feedback already implies these facts, it just leaves the two-value inputs to be decoded.
Usage: patch_feedback.py <assembled baseline dir> <chain dir>"""
import json, sys
from pathlib import Path
B, CH = Path(sys.argv[1]), Path(sys.argv[2])
chain = json.loads((CH / "CHAIN.json").read_text())
vals = {}
for s in chain["slots"]:
    for v, member in [(s["P_M"][0], True), (s["N_p"], False)]:
        vals.setdefault(s["field"], {})[v] = dict(level=s["level"], label=s["label"], example=s["A"], member=member)
old = ("        text+=\x27\\nCompared with the example input, this input differs only in: \x27+\x27; \x27.join(\n"
       "            f\"{c[\x27field\x27]}: one value \x27{c[\x27from\x27]}\x27 was replaced by \x27{c[\x27to\x27]}\x27\" for c in changes)+\x27.\x27\n")
new = old + ("        for c in changes:\n"
             "            m=PRACTICE_VALUES.get(c[\x27field\x27],{}).get(c[\x27to\x27])\n"
             "            if m is None: continue\n"
             "            if m[\x27member\x27]: text+=f\"\\n\x27{c[\x27to\x27]}\x27 belongs to {m[\x27label\x27]}, like \x27{m[\x27example\x27]}\x27, so the record with this value is not counted.\"\n"
             "            else: text+=f\"\\n\x27{c[\x27to\x27]}\x27 does not belong to {m[\x27label\x27]}, so the record with this value is still counted.\"\n")
for arm in ("self", "hint"):
    h = B / f"harness_{arm}_v0"
    (h / "PRACTICE_VALUES.json").write_text(json.dumps(vals, ensure_ascii=False, indent=1, sort_keys=True))
    p = h / "feedback_m4.py"; s = p.read_text()
    if "PRACTICE_VALUES" in s:
        continue
    assert s.count(old) == 1, (p, s.count(old))
    s = s.replace(old, new)
    s = s.replace("from common import compact\n", "from common import compact\nimport json as _json\nfrom pathlib import Path as _Path\n"
                  "PRACTICE_VALUES=_json.loads((_Path(__file__).resolve().parent/\x27PRACTICE_VALUES.json\x27).read_text())\n", 1)
    p.write_text(s)
print("feedback patched", B)
