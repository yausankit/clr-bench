#!/usr/bin/env python3
"""Recompute salience/medicine.tsv rows for the ADD_SY_a5 lists from salience/raw/."""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
STOP = {"the", "and", "for", "with", "from", "use", "code", "atc", "who", "model", "list",
        "essential", "medicines", "medicine", "group", "groups", "agents", "agent", "therapy",
        "therapies", "section", "supportive", "systemic", "children", "childhood", "drugs",
        "drug", "criteria", "activity", "alteration", "interactions"}


def words(text):
    text = re.sub(r"\([^)]*\)", " ", str(text).lower())
    return [word for word in re.findall(r"[a-z0-9]+", text)
            if len(word) >= 4 and word not in STOP]


def related(name, title):
    left, right = words(name), words(title)
    for word in left:
        for other in right:
            if word == other:
                return word
            shared = 0
            while shared < min(len(word), len(other)) and word[shared] == other[shared]:
                shared += 1
            if shared >= 5 or word in other or other in word:
                return word[:shared] if shared >= 5 else (word if word in other else other)
    return None


def main():
    with (ROOT / "add_lists_spec_r5.tsv").open(encoding="utf-8") as handle:
        spec = list(csv.DictReader(handle, delimiter="\t"))
    new_rows = []
    for row in spec:
        list_id = row["id"]
        search_path = RAW / f"search_medicine_{list_id}.json"
        hits = []
        if search_path.exists():
            hits = (json.loads(search_path.read_text()).get("query") or {}).get("search") or []
        if not hits:
            new_rows.append(f"{list_id}\t\t\tnone\t0\tno English Wikipedia article found")
            continue
        title = hits[0]["title"]
        why = related(row.get("search") or row["name"], title)
        if why is None:
            new_rows.append(f"{list_id}\t{title}\tnone\t0\tfirst hit not related to the list name")
            continue
        pageview_path = RAW / f"pageviews_medicine_{list_id}.json"
        views = 0
        note = f"search hit, shared '{why}'"
        if pageview_path.exists():
            try:
                items = json.loads(pageview_path.read_text()).get("items") or []
                views = sum(int(item.get("views", 0)) for item in items)
                note += f", {len(items)} monthly samples"
            except Exception:
                note += ", pageview response unreadable"
        new_rows.append(f"{list_id}\t{title}\tsearch\t{views}\t{note}")
    path = ROOT / "salience" / "medicine.tsv"
    lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    ids = {row["id"] for row in spec}
    keep = [line for line in lines if line.split("\t")[0] not in ids]
    path.write_text("\n".join(keep + new_rows) + "\n", encoding="utf-8")
    print(f"salience/medicine.tsv: {len(spec)} new rows")


if __name__ == "__main__":
    main()
