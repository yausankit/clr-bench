#!/usr/bin/env python3
"""Re-check every SPOTCHECK.tsv row appended for the WS2 lists against raw/ (members: evidence line contains
the value; non-members: a fresh scan of the same source finds none)."""
import csv
import io
import json
import re
import zipfile
from collections import defaultdict

import yaml
import build_add_lists as B

ROOT = __import__("pathlib").Path(__file__).resolve().parent
RAW = ROOT / "raw"
WIKI2 = RAW / "wiki_ws2"
CHARTER_PAGE = "European_Charter_for_Regional_or_Minority_Languages"


def load_lists(path, base):
    items = yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))
    nb = len(yaml.safe_load((RAW / base).read_text(encoding="utf-8")))
    return {x["id"]: x for x in items[nb:]}


def main():
    lang = load_lists("lists/language.yaml", "base_language.yaml")
    cwe = load_lists("lists/cwe.yaml", "base_cwe.yaml")
    cwe_cat = {k: re.search(r"definitions/(\d+)", v["source"]).group(1) for k, v in cwe.items()}
    z = zipfile.ZipFile(RAW / "cwec_latest.xml.zip")
    name = [n for n in z.namelist() if n.endswith(".xml") and "cwec" in n][0]
    xml = z.read(name).decode("utf-8")
    xml_lines = xml.splitlines()
    cats = {}
    for m in re.finditer(r'<Category ID="(\d+)"[^>]*>.*?</Category>', xml, re.S):
        start = xml.count("\n", 0, m.start()) + 1
        cats[m.group(1)] = [h.group(1) for h in re.finditer(r'<Has_Member CWE_ID="(\d+)"', m.group(0))]
    def subtree(cid, seen=None):
        seen = set() if seen is None else seen
        out = set()
        for mid in cats.get(cid, []):
            if mid in cats:
                out |= subtree(mid, seen)
            else:
                out.add(mid)
        return out
    wd_lines = (RAW / "wikidata" / "language_ancestors_all.json").read_text(encoding="utf-8").splitlines()
    wd_pairs = set()
    qid = None
    for line in wd_lines:
        m = re.search(r'"value" : "http://www\.wikidata\.org/entity/(Q\d+)"', line)
        if m:
            qid = m.group(1)
            continue
        m = re.search(r'"value" : "([a-z]{2})"', line)
        if m and qid:
            wd_pairs.add((m.group(1), qid))
    wiki_cache = {}
    def wiki(page):
        if page not in wiki_cache:
            wiki_cache[page] = (WIKI2 / (page + ".wikitext")).read_text(encoding="utf-8").splitlines()
        return wiki_cache[page]

    CHARTERS = {x["id"]: c for x, c in zip([y for y in lang.values() if y["id"].endswith("_charter_languages")], [])} if False else None
    charter_ids = dict([("austria_charter_languages", "Austria"), ("bosnia_charter_languages", "Bosnia and Herzegovina"),
                        ("croatia_charter_languages", "Croatia"), ("finland_charter_languages", "Finland"),
                        ("hungary_charter_languages", "Hungary"), ("poland_charter_languages", "Poland"),
                        ("romania_charter_languages", "Romania"), ("serbia_charter_languages", "Serbia"),
                        ("slovakia_charter_languages", "Slovakia"), ("slovenia_charter_languages", "Slovenia"),
                        ("spain_charter_languages", "Spain"), ("ukraine_charter_languages", "Ukraine")])
    recomputed = {}
    for lid, country in charter_ids.items():
        codes = set()
        for display, target, _ in B.parse_charter_table(country):
            key = re.sub(r"\s+language$", "", target)
            code = B.NAME2CODE[key] if key in B.NAME2CODE else B.NAME2CODE[display]
            if code:
                codes.add(code)
        recomputed[lid] = codes
    for x in B.country_lists():
        recomputed[x["id"]] = set(x["members"])
    rows = list(csv.DictReader(open(ROOT / "SPOTCHECK.tsv", encoding="utf-8"), delimiter="\t"))
    seen = defaultdict(lambda: {"member": 0, "nonmember": 0})
    errors = []
    for r in rows:
        lid, uni, role, val, ev = r["list_id"], r["universe"], r["role"], r["value"], r["evidence"]
        if lid not in lang and lid not in cwe:
            continue
        seen[lid][role] += 1
        if uni == "cwe":
            cid = cwe_cat[lid]
            if role == "member":
                m = re.search(r"cwec_v4\.20\.xml:(\d+) \(Category (\d+) Has_Member (\d+)\)", ev)
                if not m:
                    errors.append((lid, val, "bad evidence format"))
                    continue
                line, cat, mid = int(m.group(1)), m.group(2), m.group(3)
                if val != "CWE-" + mid:
                    errors.append((lid, val, "evidence value mismatch"))
                elif not re.search(r'<Has_Member CWE_ID="%s"' % mid, xml_lines[line - 1]):
                    errors.append((lid, val, "evidence line has no Has_Member"))
                elif mid not in subtree(cid):
                    errors.append((lid, val, "member not in subtree"))
            else:
                if val.replace("CWE-", "") in subtree(cid):
                    errors.append((lid, val, "non-member is in subtree"))
        elif uni == "language":
            if lid in recomputed:
                if role == "member" and val not in recomputed[lid]:
                    errors.append((lid, val, "member missing from re-parsed source"))
                if role == "nonmember" and val in recomputed[lid]:
                    errors.append((lid, val, "non-member present in re-parsed source"))
            if role == "member":
                m = re.search(r"wikitext:(\d+) \(", ev)
                if lid.endswith("_charter_languages"):
                    if not m:
                        errors.append((lid, val, "no line"))
                        continue
                    line = int(m.group(1))
                    if not wiki(CHARTER_PAGE)[line - 1].strip().startswith("|"):
                        errors.append((lid, val, "charter evidence line is not a row"))
                elif lid == "spain_official_languages" or lid.startswith(("italy_law", "vojvodina", "ots_")):
                    page = re.search(r"raw/wiki_ws2/([A-Za-z_\-]+)\.wikitext:(\d+)", ev)
                    if not page:
                        errors.append((lid, val, "bad page evidence"))
                        continue
                    line = wiki(page.group(1))[int(page.group(2)) - 1]
                    nm = lang[lid]["name"]
                    if page.group(1) == "Languages_of_Spain" and "official" not in line:
                        errors.append((lid, val, "spain line"))
                else:
                    mq = re.search(r"ancestor (Q\d+)", ev)
                    if not mq or (val, mq.group(1)) not in wd_pairs:
                        errors.append((lid, val, "wikidata binding missing"))
            else:
                if lid.endswith("_charter_languages"):
                    if "absent" not in ev:
                        errors.append((lid, val, "no negative check"))
                elif lid.startswith(("italy_law", "vojvodina", "ots_", "spain_official")):
                    if "absent" not in ev:
                        errors.append((lid, val, "no negative check"))
                else:
                    mq = re.search(r"ancestor (Q\d+)", ev)
                    if (val, mq.group(1)) in wd_pairs if mq else False:
                        errors.append((lid, val, "non-member binding exists"))
    bad = {k: v for k, v in seen.items() if v["member"] != 5 or v["nonmember"] != 5}
    print("lists checked", len(seen), "rows", sum(v["member"] + v["nonmember"] for v in seen.values()))
    print("bad counts", bad)
    print("errors", errors[:1], "n", len(errors))
    assert not bad and not errors


if __name__ == "__main__":
    main()
