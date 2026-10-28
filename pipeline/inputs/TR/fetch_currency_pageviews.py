"""Fetch 12-month English Wikipedia pageviews for the new currency-list concepts.

Wikimedia REST API, one request at a time, 0.5 s apart (guide section 3).
Window: 2025-10-01 .. 2026-09-30 (the twelve months before the dataset snapshot).
"""
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw", "pageviews")
PROXY = os.environ.get("HTTPS_PROXY", "")  # optional HTTP proxy; empty means direct

TITLES = [
    "Group of Seven", "OECD", "NATO", "Shanghai Cooperation Organisation",
    "Eurasian Economic Union", "Organization of Turkic States",
    "Community of Portuguese Language Countries", "ECOWAS", "East African Community",
    "Southern African Development Community", "Southern African Customs Union",
    "Caribbean Community", "Mercosur", "Arab Maghreb Union", "OPEC", "Nordic Council",
    "Pacific Islands Forum", "ISO 4217", "Rial",
]


def slug(title):
    return re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")


def main():
    os.makedirs(RAW, exist_ok=True)
    for title in TITLES:
        path = os.path.join(RAW, slug(title) + ".json")
        if os.path.exists(path):
            print("have", title)
            continue
        url = ("https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/"
               "all-access/user/" + title.replace(" ", "_") + "/monthly/2025100100/2026093000")
        out = subprocess.run(["curl", "-sS", "-x", PROXY, "-w", "\n%{http_code}", url],
                             capture_output=True, text=True)
        body, _, code = out.stdout.rpartition("\n")
        if code != "200":
            print("FAILED", title, code, body[:200])
            sys.exit(1)
        d = json.loads(body)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(d, fh, ensure_ascii=False)
        print("saved", title, sum(int(x["views"]) for x in d["items"]))
        time.sleep(0.5)


if __name__ == "__main__":
    main()
