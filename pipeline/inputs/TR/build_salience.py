"""Build salience/<U>.tsv from raw/pageviews/<title>.json (Wikimedia REST pageviews API).

The value is the sum of monthly pageviews of the English Wikipedia article of the list's concept
over the twelve months that end before the snapshot date (2025-10-01 .. 2026-09-30).
"""
import json
import os
import re
import shutil

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "pageviews")
OUT = os.path.join(HERE, "salience")


def slug(title):
    return re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")


def main():
    os.makedirs(OUT, exist_ok=True)
    raw_out = os.path.join(OUT, "raw")
    os.makedirs(raw_out, exist_ok=True)
    for path in sorted(os.listdir(os.path.join(HERE, "lists"))):
        if not path.endswith(".yaml"):
            continue
        name = path[:-5]
        items = yaml.safe_load(open(os.path.join(HERE, "lists", path), encoding="utf-8")) or []
        lines = ["concept_id\twiki_title\tmatch\tpageviews_12m\tnote"]
        for it in items:
            title = it.get("wiki") or ""
            if not title:
                lines.append(f"{it['id']}\t\tno_title\t0\tno Wikipedia concept for this list")
                continue
            p = os.path.join(RAW, slug(title) + ".json")
            if not os.path.exists(p):
                lines.append(f"{it['id']}\t{title}\tmissing\t0\tpageviews fetch missing")
                continue
            d = json.load(open(p, encoding="utf-8"))
            total = sum(int(x["views"]) for x in d.get("items", []))
            lines.append(f"{it['id']}\t{title}\tarticle\t{total}\t{len(d.get('items', []))} months")
            shutil.copyfile(p, os.path.join(raw_out, slug(title) + ".json"))
        with open(os.path.join(OUT, name + ".tsv"), "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
        print(name, len(items), "rows")


if __name__ == "__main__":
    main()
