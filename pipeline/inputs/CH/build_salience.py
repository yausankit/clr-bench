#!/usr/bin/env python3
"""Fetch and aggregate 12-month English Wikipedia pageviews for CH list concepts."""
from __future__ import annotations

import csv
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "salience" / "raw"
OUT = ROOT / "salience"
START = "2025101600"
END = "2026101500"

TITLES = {
    "stockholm_annex_a": "Stockholm Convention",
    "stockholm_annex_c": "Persistent organic pollutant",
    "rotterdam_pesticides": "Rotterdam Convention",
    "rotterdam_industrial": "Rotterdam Convention",
    "rotterdam_annex_iii": "Rotterdam Convention",
    "opcw_schedule_1": "Chemical Weapons Convention",
    "opcw_schedule_2": "Chemical Weapons Convention",
    "opcw_schedule_3": "Chemical Weapons Convention",
    "opcw_all_schedules": "Chemical Weapons Convention",
    "montreal_all_controlled_substances": "Montreal Protocol",
    "iarc_group_1": "List of IARC Group 1 carcinogens",
    "iarc_group_2a": "List of IARC Group 2A carcinogens",
    "iarc_group_2b": "List of IARC Group 2B carcinogens",
    "iarc_group_3": "List of IARC Group 3 carcinogens",
    "wfd_priority": "Water Framework Directive",
    "wfd_hazardous": "Water Framework Directive",
    "montreal_annex_a_group_i": "Montreal Protocol",
    "stockholm_all_pops": "Persistent organic pollutant",
    "eu": "European Union",
    "eu_1958": "Inner Six",
    "nato": "NATO",
    "commonwealth": "Commonwealth of Nations",
    "asean": "ASEAN",
    "arab_league": "Arab League",
    "mtcr": "Missile Technology Control Regime",
    "nsg": "Nuclear Suppliers Group",
    "australia_group": "Australia Group",
    "wassenaar": "Wassenaar Arrangement",
    "schengen": "Schengen Area",
    "opec": "OPEC",
    "g7": "G7",
    "gcc": "Gulf Cooperation Council",
    "star_alliance": "Star Alliance",
    "oneworld": "Oneworld",
    "skyteam": "SkyTeam",
    "alta_full": "Latin American and Caribbean Air Transport Association",
    "alta_associate": "Latin American and Caribbean Air Transport Association",
    "a4a": "Airlines for America",
    "a4e": "Airlines for Europe",
}


def opener() -> urllib.request.OpenerDirector:
    handler = urllib.request.ProxyHandler()  # HTTP_PROXY / HTTPS_PROXY from the environment, if set
    op = urllib.request.build_opener(handler)
    op.addheaders = [("User-Agent", "CLRSynth-dataset/1.0 (research)")]
    return op


def fetch_one(op: urllib.request.OpenerDirector, concept: str, title: str) -> dict:
    quoted = urllib.parse.quote(title.replace(" ", "_"), safe="")
    url = (f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
           f"all-access/user/{quoted}/monthly/{START}/{END}")
    wait = 60
    while True:
        try:
            with op.open(url, timeout=300) as response:
                payload = json.load(response)
            return {"concept_id": concept, "wiki_title": title, "url": url, "response": payload}
        except urllib.error.HTTPError as exc:
            if exc.code == 429:
                print(f"{concept}: 429; waiting {wait}s", flush=True)
                time.sleep(wait)
                wait = min(600, wait * 2)
                continue
            if 500 <= exc.code < 600:
                print(f"{concept}: HTTP {exc.code}; waiting 30s", flush=True)
                time.sleep(30)
                continue
            if exc.code == 404:
                print(f"{concept}: HTTP 404 for {title!r}; leaving raw response missing", flush=True)
                return None
            raise
        except Exception as exc:
            print(f"{concept}: {type(exc).__name__}: {exc}; waiting 30s", flush=True)
            time.sleep(30)


def fetch_all() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    op = opener()
    for concept, title in TITLES.items():
        path = RAW / f"{concept}.json"
        if path.exists() and path.stat().st_size > 20:
            print(f"{concept}: cached", flush=True)
            continue
        data = fetch_one(op, concept, title)
        if data is None:
            continue
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"{concept}: {sum(x['views'] for x in data['response']['items'])}", flush=True)
        time.sleep(0.5)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = []
    for concept, title in TITLES.items():
        path = RAW / f"{concept}.json"
        views = 0
        if path.exists():
            data = json.loads(path.read_text(encoding="utf-8"))
            title = data.get("wiki_title", title)
            views = sum(int(x["views"]) for x in data["response"]["items"])
            note = "monthly total"
        else:
            note = "raw response missing"
        rows.append({"concept_id": concept, "wiki_title": title, "match": "exact",
                     "pageviews_12m": views, "note": note})
    owners = {}
    for path in sorted((ROOT / "lists").glob("*.yaml")):
        for item in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            owners[str(item["id"])] = path.stem
    for uname in ("chemical", "country", "carrier"):
        selected = [row for row in rows if owners.get(row["concept_id"]) == uname]
        with (OUT / f"{uname}.tsv").open("w", encoding="utf-8", newline="") as fh:
            writer = csv.DictWriter(fh, delimiter="\t", fieldnames=[
                "concept_id", "wiki_title", "match", "pageviews_12m", "note"], lineterminator="\n")
            writer.writeheader()
            writer.writerows(selected)
        print(f"wrote {OUT / (uname + '.tsv')} ({len(selected)} rows)")


if __name__ == "__main__":
    if "--fetch" in sys.argv:
        fetch_all()
    build()
