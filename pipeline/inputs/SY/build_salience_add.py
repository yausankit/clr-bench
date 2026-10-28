"""Recompute salience/procedure.tsv from salience/raw/ for the ADD_SY_a1 lists.

Uses the same rule as build_salience.py: the first English-Wikipedia search hit counts only when
its title is lexically related to the list name; pageviews_12m is the sum of the monthly
all-access user pageviews for 2025-10 .. 2026-09.  Unmatched lists keep salience 0.
Rows of the pre-existing lists are preserved byte for byte.
"""
import csv
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
STOP = {"the", "and", "for", "with", "from", "use", "code", "atc",
        "finding", "findings", "sign", "signs", "symptom", "symptoms", "disease", "diseases",
        "disorder", "disorders", "procedure", "procedures", "condition", "conditions", "system",
        "site", "mass", "structure", "structures", "therapy", "therapies", "agents", "agent",
        "group", "groups", "abnormal", "normal", "entire", "part"}


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
    spec = list(csv.DictReader((ROOT / "add_lists_spec.tsv").open(encoding="utf-8"), delimiter="\t"))
    new_rows = []
    for row in spec:
        lid = row["id"]
        sp = RAW / f"search_procedure_{lid}.json"
        hits = []
        if sp.exists():
            hits = (json.loads(sp.read_text()).get("query") or {}).get("search") or []
        if not hits:
            new_rows.append(f"{lid}\t\t\tnone\t0\tno English Wikipedia article found")
            continue
        title = hits[0]["title"]
        why = related(row["name"], title)
        if why is None:
            new_rows.append(f"{lid}\t{title}\tnone\t0\tfirst hit not related to the list name")
            continue
        pp = RAW / f"pageviews_procedure_{lid}.json"
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
    path = ROOT / "salience" / "procedure.tsv"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    ids = {r["id"] for r in spec}
    keep = [ln for ln in lines if ln.split("\t")[0] not in ids]
    path.write_text("\n".join(keep + new_rows) + "\n", encoding="utf-8")
    print(f"salience/procedure.tsv: {len(spec)} new rows")


if __name__ == "__main__":
    main()
