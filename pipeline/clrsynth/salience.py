"""clrsynth salience <dataset>: merge salience/<U>.tsv (concept id, pageviews over 12 months) into the lists, so that
better-known groupings are tried first."""
import csv
from pathlib import Path

import yaml


def merge_salience(root):
    root = Path(root)
    report = {}
    for lpath in sorted((root / "lists").glob("*.yaml")):
        spath = root / "salience" / f"{lpath.stem}.tsv"
        if not spath.exists():
            report[lpath.stem] = "no salience table"
            continue
        with spath.open(encoding="utf-8") as fh:
            table = {r["concept_id"]: int(float(r.get("pageviews_12m") or 0))
                     for r in csv.DictReader(fh, delimiter="\t")}
        items = yaml.safe_load(lpath.read_text(encoding="utf-8")) or []
        hit = 0
        for it in items:
            it["salience"] = table.get(str(it["id"]), 0)
            hit += str(it["id"]) in table
        lpath.write_text(yaml.safe_dump(items, allow_unicode=True, sort_keys=False), encoding="utf-8")
        report[lpath.stem] = f"{hit}/{len(items)} lists matched"
    return report
