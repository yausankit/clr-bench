"""Recompute salience/medicine.tsv rows for the ADD_SY_a2 lists from salience/raw/.

Same rule as build_salience.py: the first English-Wikipedia search hit counts only when its title
is lexically related to the list name; pageviews_12m is the sum of monthly all-access user
pageviews for 2025-10 .. 2026-09.  Existing rows of other lists are preserved.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
STOP = {"the", "and", "for", "with", "from", "use", "code", "atc", "who", "model", "list",
        "essential", "medicines", "medicine", "group", "groups", "agents", "agent", "therapy",
        "therapies", "section", "supportive", "systemic", "children", "childhood"}


def words(text):
    text = re.sub(r"\([^)]*\)", " ", str(text).lower())
    return [w for w in re.findall(r"[a-z0-9]+", text) if len(w) >= 4 and w not in STOP]


def related(name, title):
    a, b = words(name), words(title)
    for x in a:
        for y in b:
            if x == y:
                return sorted({x})[0]
            n = 0
            while n < min(len(x), len(y)) and x[n] == y[n]:
                n += 1
            if n >= 5 or x in y or y in x:
                return x[:n] if n >= 5 else (x if x in y else y)
    return None


def main():
    spec = list(csv.DictReader((ROOT / "add_lists_spec_medicine.tsv").open(encoding="utf-8"), delimiter="\t"))
    new_rows = []
    for row in spec:
        lid = row["id"]
        sp = RAW / f"search_medicine_{lid}.json"
        hits = []
        if sp.exists():
            hits = (json.loads(sp.read_text()).get("query") or {}).get("search") or []
        if not hits:
            new_rows.append(f"{lid}\t\t\tnone\t0\tno English Wikipedia article found")
            continue
        title = hits[0]["title"]
        why = related(row.get("search") or row["name"], title)
        if why is None:
            new_rows.append(f"{lid}\t{title}\tnone\t0\tfirst hit not related to the list name")
            continue
        pp = RAW / f"pageviews_medicine_{lid}.json"
        views = 0
        note = f"search hit, shared '{why}'"
        if pp.exists():
            try:
                items = json.loads(pp.read_text()).get("items") or []
                views = sum(int(x.get("views", 0)) for x in items)
                note += f", {len(items)} monthly samples"
            except Exception:
                note += ", pageview response unreadable"
        new_rows.append(f"{lid}\t{title}\tsearch\t{views}\t{note}")
    path = ROOT / "salience" / "medicine.tsv"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    ids = {r["id"] for r in spec}
    keep = [ln for ln in lines if ln.split("\t")[0] not in ids]
    path.write_text("\n".join(keep + new_rows) + "\n", encoding="utf-8")
    print(f"salience/medicine.tsv: {len(spec)} new rows")


if __name__ == "__main__":
    main()
