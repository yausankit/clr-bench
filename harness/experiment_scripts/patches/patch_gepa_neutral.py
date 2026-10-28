"""GEPA neutral-note variant (no example of the test aggregation): one fixed note appended to every GEPA reflection input (self and hint identical).
The practice task asks for the largest entity total and the test task for the sum over entities; the original GEPA
folds the practice aggregation into its evolved policy, which then overrides the test task (79/160 L1-L4 test programs
returned a maximum). Everything else in the official GEPA search stays as it is."""
import sys
from pathlib import Path
NOTE = ("\\n\\nNote on the policy: it will also be used for this level\x27s test task, which has the same records and rules "
        "but may ask for a different output (for example a different aggregation over the entities). "
        "Keep the policy about which records count and which rules apply; do not state the output aggregation or "
        "format, and let each task\x27s own instructions decide them.")
old = "(prompt if isinstance(prompt, str) else compact(prompt)) + released_reference_blocks(history)"
new = "(prompt if isinstance(prompt, str) else compact(prompt)) + released_reference_blocks(history) + GEPA_FORMAT_NOTE"
for arm in ("self", "hint"):
    p = Path(sys.argv[1]) / f"harness_{arm}_v0/methods_r3.py"
    s = p.read_text()
    if "GEPA_FORMAT_NOTE" in s:
        continue
    assert s.count(old) == 1, (p, s.count(old))
    s = s.replace(old, new).replace("def gepa_update(", f"GEPA_FORMAT_NOTE = \"{NOTE}\"\n\n\ndef gepa_update(", 1)
    p.write_text(s)
print("patched", sys.argv[1])
