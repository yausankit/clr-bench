"""Append and verify ADD_SY_a2 SPOTCHECK rows (5 members + 5 non-members per new list).

Each row is checked against raw/add/official_members.json, the transcription of the stored
WHO PDF sections / DEA CFR XML / ATC pages; the evidence column names the entry index.  Rows for
a list that already has entries are not appended again.
"""
import json
from pathlib import Path

import build_lists_add_medicine as B

ROOT = Path(__file__).resolve().parent
UNIVERSE = "medicine"
CHECKS = 5


def main():
    values = B.universe_values()
    payload = json.loads((ROOT / "raw" / "add" / "official_members.json").read_text(encoding="utf-8"))
    path = ROOT / "SPOTCHECK.tsv"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    have = {ln.split("\t")[1] for ln in lines if ln.startswith(UNIVERSE + "\t")}
    new = []
    for item in payload:
        lid = item["id"]
        if lid in have:
            continue
        official = item["official"]
        canon_names = {B.canon(n): n for n in official}
        members = [v for v in values if B.canon(v) in canon_names]
        nonmembers = [v for v in values if B.canon(v) not in canon_names]
        if len(members) < CHECKS or len(nonmembers) < CHECKS:
            raise SystemExit(f"{lid}: not enough members/non-members for SPOTCHECK")
        picks = members[:CHECKS]
        nonpicks = [nonmembers[i * len(nonmembers) // CHECKS] for i in range(CHECKS)]
        for v in picks:
            n = canon_names[B.canon(v)]
            i = official.index(n)
            ev = (f"raw/add/official_members.json {lid} entry #{i + 1}: \"{n}\"; "
                  f"{item['source']}")
            new.append([UNIVERSE, lid, "member", v, ev])
        for v in nonpicks:
            ev = (f"raw/add/official_members.json {lid}: {len(official)} entries scanned, "
                  f"\"{v}\" has no matching official member; {item['source']}")
            new.append([UNIVERSE, lid, "nonmember", v, ev])
    if new:
        lines.extend("\t".join(r) for r in new)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    ids = {item["id"] for item in payload}
    by_id = {item["id"]: item for item in payload}
    checked = 0
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) != 5 or parts[0] != UNIVERSE or parts[1] not in ids:
            continue
        lid, kind, value = parts[1], parts[2], parts[3]
        official = by_id[lid]["official"]
        inside = B.canon(value) in {B.canon(n) for n in official}
        if kind == "member" and not inside:
            raise SystemExit(f"SPOTCHECK verification failed: {lid} member {value} not in raw")
        if kind == "nonmember" and inside:
            raise SystemExit(f"SPOTCHECK verification failed: {lid} nonmember {value} is in raw")
        checked += 1
    print(f"SPOTCHECK.tsv: {len(new)} rows appended, {checked} new-list rows verified")


if __name__ == "__main__":
    main()
