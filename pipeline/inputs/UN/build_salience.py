#!/usr/bin/env python3
"""Recompute list pageview totals and the required per-universe tables from raw JSON."""
import csv,json
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parent
for lp in sorted((ROOT/"lists").glob("*.yaml")):
    rows=[]
    for item in yaml.safe_load(lp.read_text(encoding="utf-8")) or []:
        p=ROOT/"salience"/"raw"/f"{lp.stem}__{item['id']}.json"
        data=json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
        views=sum(int(x.get("views",0)) for x in data.get("items",[]))
        title=data.get("_requested_title") or item.get("name",item["id"])
        if data.get("status")==404: match="no_page";note="pageviews REST returned 404"
        elif data.get("items"): match="exact_title";note="monthly English Wikipedia pageviews, 2025-10-01 through 2026-09-30"
        else: match="no_data";note="no monthly observations returned"
        rows.append([item["id"],title,match,views,note])
    with (ROOT/"salience"/f"{lp.stem}.tsv").open("w",encoding="utf-8",newline="") as f:
        w=csv.writer(f,delimiter="\t",lineterminator="\n");w.writerow(["concept_id","wiki_title","match","pageviews_12m","note"]);w.writerows(rows)
