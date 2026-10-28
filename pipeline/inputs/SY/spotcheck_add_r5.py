#!/usr/bin/env python3
"""Append and verify five member and five non-member checks for each ADD_SY_a5 list."""
import json
from pathlib import Path

import build_lists_add_r5 as B

ROOT = Path(__file__).resolve().parent
UNIVERSE = "medicine"
CHECKS = 5


def normalized_official(item):
    records = {}
    for record in item["official"]:
        records.setdefault(B.name_key(record["term"]), record)
    return records


def main():
    values = B.universe_values()
    payload = json.loads((ROOT / "raw" / "add" / "r5" / "manifests" /
                          "official_members.json").read_text(encoding="utf-8"))
    path = ROOT / "SPOTCHECK.tsv"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    present = {line.split("\t")[1] for line in lines
               if line.startswith(UNIVERSE + "\t") and len(line.split("\t")) > 1}
    new = []
    for item in payload:
        list_id = item["id"]
        if list_id in present:
            continue
        records = normalized_official(item)
        members = [value for value in values if B.name_key(value) in records]
        nonmembers = [value for value in values if B.name_key(value) not in records]
        if len(members) < CHECKS or len(nonmembers) < CHECKS:
            raise SystemExit(f"{list_id}: not enough members/non-members for SPOTCHECK")
        picks = members[:CHECKS]
        nonpicks = [nonmembers[index * len(nonmembers) // CHECKS]
                    for index in range(CHECKS)]
        for value in picks:
            record = records[B.name_key(value)]
            raw_path = ROOT / record["raw"]
            if not raw_path.is_file():
                raise SystemExit(f"{list_id}: missing raw evidence {record['raw']}")
            evidence = (f"{record['raw']}: {record['evidence']}; {item['source']}")
            new.append([UNIVERSE, list_id, "member", value, evidence])
        for value in nonpicks:
            evidence = (f"{item['official'][0]['raw']}: {len(records)} normalized entries scanned, "
                        f"\"{value}\" has no matching official member; {item['source']}")
            new.append([UNIVERSE, list_id, "nonmember", value, evidence])
    if new:
        lines.extend("\t".join(row) for row in new)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    ids = {item["id"] for item in payload}
    by_id = {item["id"]: normalized_official(item) for item in payload}
    checked = 0
    for line in lines:
        parts = line.split("\t")
        if len(parts) != 5 or parts[0] != UNIVERSE or parts[1] not in ids:
            continue
        list_id, kind, value = parts[1], parts[2], parts[3]
        inside = B.name_key(value) in by_id[list_id]
        if kind == "member" and not inside:
            raise SystemExit(f"SPOTCHECK verification failed: {list_id} member {value} not in raw")
        if kind == "nonmember" and inside:
            raise SystemExit(f"SPOTCHECK verification failed: {list_id} nonmember {value} is in raw")
        checked += 1
    print(f"SPOTCHECK.tsv: {len(new)} rows appended, {checked} new-list rows verified")


if __name__ == "__main__":
    main()
