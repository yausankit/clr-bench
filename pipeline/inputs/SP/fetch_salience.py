#!/usr/bin/env python3
"""Fetch 12-month English Wikipedia pageviews for each candidate list."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

from build_salience import all_items, item_page_title

ROOT = Path(__file__).resolve().parent
START = "2025100100"
END = "2026093000"


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "CLRSynth-SP/2.0 (dataset snapshot)"})
    wait = 60
    while True:
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return json.loads(resp.read().decode("utf-8")), None
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                return {}, f"HTTP 404: {exc.read().decode(errors='replace')[:200]}"
            print(f"retry pageviews {url}: HTTP {exc.code}", flush=True)
        except Exception as exc:
            print(f"retry pageviews {url}: {type(exc).__name__}: {exc}", flush=True)
        time.sleep(wait)
        wait = min(wait * 2, 600)


def main():
    for universe, item in all_items():
        out = ROOT / "salience" / "raw" / universe / f"{item['id']}.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.exists() and out.stat().st_size > 20:
            print(f"exists {item['id']}", flush=True)
            continue
        title = item_page_title(item).replace(" ", "_")
        path = urllib.parse.quote(title, safe="")
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/"
               f"en.wikipedia/all-access/user/{path}/monthly/{START}/{END}")
        obj, error = fetch(url)
        if error:
            obj = {"items": [], "error": error, "wiki_title": item_page_title(item)}
        out.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"saved {item['id']}: {len(obj.get('items', []))} months", flush=True)
        time.sleep(0.6)


if __name__ == "__main__":
    main()
