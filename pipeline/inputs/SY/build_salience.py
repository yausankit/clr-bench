"""Recompute salience/<universe>.tsv from the raw Wikimedia API responses in salience/raw/.

For every list the first English Wikipedia search hit is used when its title is lexically related to
the list name (a shared word, a shared prefix of >= 5 letters, or one word inside the other); otherwise
the list gets 0 and stays in the input.  pageviews_12m is the sum of the monthly all-access user
pageviews for 2025-10 .. 2026-09.
"""
import json
import re
from pathlib import Path

import yaml

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
    for path in sorted((ROOT / "lists").glob("*.yaml")):
        u = path.stem
        rows = ["concept_id\twiki_title\tmatch\tpageviews_12m\tnote"]
        for lst in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            lid = lst["id"]
            sp = RAW / f"search_{u}_{lid}.json"
            hits = []
            if sp.exists():
                hits = (json.loads(sp.read_text()).get("query") or {}).get("search") or []
            if not hits:
                rows.append(f"{lid}\t\t\tnone\t0\tno English Wikipedia article found")
                continue
            title = hits[0]["title"]
            why = related(lst["name"], title)
            if why is None:
                rows.append(f"{lid}\t{title}\tnone\t0\tfirst hit not related to the list name")
                continue
            pp = RAW / f"pageviews_{u}_{lid}.json"
            views = 0
            note = f"search hit, shared '{why}'"
            if pp.exists():
                try:
                    items = json.loads(pp.read_text()).get("items") or []
                    views = sum(int(x.get("views", 0)) for x in items)
                    note += f", {len(items)} monthly samples"
                except Exception:
                    note += ", pageview response unreadable"
            rows.append(f"{lid}\t{title}\tsearch\t{views}\t{note}")
        (ROOT / "salience" / f"{u}.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")
        print(u, len(rows) - 1)


if __name__ == "__main__":
    main()
