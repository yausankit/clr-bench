#!/usr/bin/env python3
"""Fetch the 2026-10-16 MediaWiki revisions for the SP public sources, one request every 2.1 seconds."""
import json
import os
import time
import urllib.parse
import urllib.request
from pathlib import Path

PAGES = {
    "ucl_finals": "List of European Cup and UEFA Champions League finals",
    "uel_finals": "List of UEFA Cup and Europa League finals",
    "cup_winners_cup_finals": "List of UEFA Cup Winners' Cup finals",
    "club_world_cup_finals": "List of FIFA Club World Cup finals",
    "intercontinental_cup": "Intercontinental Cup (football)",
    "european_super_league": "European Super League",
    "g14": "G-14",
    "cwc_2025": "2025 FIFA Club World Cup",
    "ucl_2024_25": "2024–25 UEFA Champions League",
    "premier_league_1992_93": "1992–93 FA Premier League",
    "laliga_1929": "1929 La Liga",
    "bundesliga_1963_64": "1963–64 Bundesliga",
    "seriea_1929_30": "1929–30 Serie A",
    "dow_jones": "Dow Jones Industrial Average",
    "nasdaq_100": "Nasdaq-100",
    "sp_100": "S&P 100",
    "sp_500": "List of S&P 500 companies",
    "stoxx_europe_50": "STOXX Europe 50",
    "stoxx_europe_600": "STOXX Europe 600",
    "sp_europe_350": "S&P Europe 350",
    "sp_global_100": "S&P Global 100",
    "ftse_all_share": "FTSE All-Share Index",
    "ftse_100": "FTSE 100 Index",
    "dax": "DAX",
    "cac_40": "CAC 40",
    "ibex_35": "IBEX 35",
    "ftse_mib": "FTSE MIB",
    "euro_stoxx_50": "EURO STOXX 50",
    "smi": "Swiss Market Index",
    "aex": "AEX index",
    "bel_20": "BEL 20",
    "omx_stockholm_30": "OMX Stockholm 30",
    "hang_seng": "Hang Seng Index",
    "kospi_200": "KOSPI 200",
    "asx_50": "S&P/ASX 50",
    "eu_members": "Member state of the European Union",
    "nato": "NATO",
    "g7": "Group of Seven",
    "g20": "G20",
    "oecd": "OECD",
    "opec": "OPEC",
    "asean": "ASEAN",
    "african_union": "African Union",
    "commonwealth": "Commonwealth of Nations",
    "schengen": "Schengen Area",
    "council_of_europe": "Council of Europe",
    "apec": "Asia-Pacific Economic Cooperation",
    "oas": "Organization of American States",
    "gcc": "Gulf Cooperation Council",
    "nordic_council": "Nordic Council",
    "mercosur": "Mercosur",
}


API = "https://en.wikipedia.org/w/api.php"
CUTOFF = "2026-10-16T23:59:59Z"
UA = {"User-Agent": "CLRSynth-SP/2.0 (dataset snapshot)"}


def request(params):
    req = urllib.request.Request(API + "?" + urllib.parse.urlencode(params), headers=UA)
    wait = 60
    while True:
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:
            print(f"retry {params}: {type(exc).__name__}: {exc}", flush=True)
            time.sleep(wait)
            wait = min(wait * 2, 600)


def revision_ids(titles):
    found = {}
    for title in titles:
        obj = request({"action": "query", "prop": "revisions", "titles": title,
                       "rvlimit": "1", "rvstart": CUTOFF, "rvdir": "older",
                       "rvprop": "ids|timestamp", "format": "json", "formatversion": "2",
                       "redirects": "1"})
        if "error" in obj:
            raise RuntimeError(obj["error"])
        for page in obj["query"]["pages"]:
            revisions = page.get("revisions") or []
            if revisions:
                found[page["title"]] = revisions[0]["revid"]
        for link in obj["query"].get("normalized", []) + obj["query"].get("redirects", []):
            if link["to"] in found:
                found[link["from"]] = found[link["to"]]
        if title not in found:
            pages = obj["query"]["pages"]
            if len(pages) == 1 and pages[0].get("revisions"):
                found[title] = pages[0]["revisions"][0]["revid"]
        time.sleep(2.1)
    return found


def main():
    root = Path(__file__).resolve().parent / "raw" / "pages"
    stage = root.parent / "pages_20261016"
    stage.mkdir(parents=True, exist_ok=True)
    revs = revision_ids(list(PAGES.values()))
    print(f"resolved {len(revs)} revision ids at {CUTOFF}", flush=True)
    time.sleep(2.1)
    for key, title in PAGES.items():
        out = stage / f"{key}.json"
        oldid = revs.get(title)
        if not oldid:
            raise RuntimeError(f"no revision at cutoff for {title}")
        if out.exists() and out.stat().st_size > 1000:
            print(f"exists staged {key}", flush=True)
            continue
        obj = request({"action": "parse", "oldid": str(oldid), "prop": "text|revid",
                       "format": "json", "formatversion": "2"})
        if "error" in obj:
            raise RuntimeError(f"{key}: {obj['error']}")
        out.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        parsed = obj["parse"]
        print(f"saved {key}: {parsed['title']} revid={parsed.get('revid')} ({out.stat().st_size} bytes)",
              flush=True)
        time.sleep(2.1)
    if len(list(stage.glob("*.json"))) != len(PAGES):
        raise RuntimeError("staged snapshot is incomplete")
    root.mkdir(parents=True, exist_ok=True)
    for key in PAGES:
        os.replace(stage / f"{key}.json", root / f"{key}.json")
    stage.rmdir()
    print(f"installed {len(PAGES)} pages under {root}", flush=True)


if __name__ == "__main__":
    main()
