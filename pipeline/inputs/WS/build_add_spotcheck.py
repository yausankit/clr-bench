#!/usr/bin/env python3
"""Append 5 members and 5 non-members per new list to SPOTCHECK.tsv, each backed by a raw/ line or an
explicit negative check over the same raw source."""
import csv
import io
import json
import re
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
WIKI2 = RAW / "wiki_ws2"
CHARTER_PAGE = "European_Charter_for_Regional_or_Minority_Languages"
NS = "{http://cwe.mitre.org/cwe-7}"


def spread(seq, k=5):
    seq = list(seq)
    if len(seq) <= k:
        return seq
    return [seq[i * len(seq) // k] for i in range(k)]


def read_universe(u):
    with (ROOT / "universes" / f"{u}.tsv").open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh, delimiter="\t"))


def lang_names():
    names = {}
    for r in read_universe("language"):
        names.setdefault(r["value"], set()).add(r["entity"].split(",")[0].strip())
        for a in (r.get("aliases") or "").split("|"):
            if a.strip():
                names[r["value"]].add(a.strip())
    return names


def charter_rows(country):
    lines = (WIKI2 / (CHARTER_PAGE + ".wikitext")).read_text(encoding="utf-8").splitlines()
    starts = []
    for i, line in enumerate(lines):
        m = re.match(r'\|rowspan="(\d+)"\|\{\{flagcountry\|([^}]+)\}\}', line)
        if m:
            starts.append((i, int(m.group(1)), m.group(2)))
    for k, (i, n, name) in enumerate(starts):
        if name == country:
            end = starts[k + 1][0] if k + 1 < len(starts) else len(lines)
            rows = []
            for j in range(i + 1, end):
                m = re.match(r'\|\s*"?\[\[([^\]|]+)(?:\|([^\]]*))?\]\]', lines[j])
                if m:
                    rows.append(((m.group(2) or m.group(1)).strip(), m.group(1).strip(), j + 1))
            assert len(rows) == n, (country, len(rows), n)
            return i + 1, end, rows
    raise KeyError(country)


def build_cwe_index():
    z = zipfile.ZipFile(RAW / "cwec_latest.xml.zip")
    name = [n for n in z.namelist() if n.endswith(".xml") and "cwec" in n][0]
    text = z.read(name).decode("utf-8")
    idx = {}
    for m in re.finditer(r'<Category ID="(\d+)"[^>]*>.*?</Category>', text, re.S):
        cid = m.group(1)
        start = text.count("\n", 0, m.start()) + 1
        end = text.count("\n", 0, m.end()) + 1
        rows = []
        for h in re.finditer(r'<Has_Member CWE_ID="(\d+)"', m.group(0)):
            line = start + m.group(0).count("\n", 0, h.start())
            rows.append((h.group(1), line))
        idx[cid] = (start, end, rows)
    return idx


def cwe_members(idx, cid, seen=None, out=None):
    seen = set() if seen is None else seen
    out = {} if out is None else out
    if cid in seen or cid not in idx:
        return out
    seen.add(cid)
    for mid, line in idx[cid][2]:
        if mid in idx:
            cwe_members(idx, mid, seen, out)
        else:
            out.setdefault(mid, (cid, line))
    return out


def wt_lines(page):
    return (WIKI2 / (page + ".wikitext")).read_text(encoding="utf-8").splitlines()


import build_add_lists as B

CHARTER = [("austria_charter_languages", "Austria"), ("bosnia_charter_languages", "Bosnia and Herzegovina"),
           ("croatia_charter_languages", "Croatia"), ("finland_charter_languages", "Finland"),
           ("hungary_charter_languages", "Hungary"), ("poland_charter_languages", "Poland"),
           ("romania_charter_languages", "Romania"), ("serbia_charter_languages", "Serbia"),
           ("slovakia_charter_languages", "Slovakia"), ("slovenia_charter_languages", "Slovenia"),
           ("spain_charter_languages", "Spain"), ("ukraine_charter_languages", "Ukraine")]

BRANCH = [("north_germanic_languages", "Q106085"), ("west_scandinavian_languages", "Q1792570"),
          ("nguni_languages", "Q961559"), ("southern_bantu_languages", "Q980498"),
          ("gallo_romance_languages", "Q500394"), ("gallo_iberian_languages", "Q954321")]

PAGE_LINE = {  # list id -> (page, marker text that identifies the source line)
    "spain_official_languages": ("Languages_of_Spain", "| official"),
    "italy_law_482_languages": ("Languages_of_Italy", "Twelve languages are officially recognized"),
    "vojvodina_official_languages": ("Languages_of_Vojvodina", "five recognized minority languages"),
    "ots_official_languages": ("Organization_of_Turkic_States", "| official_languages"),
}


def wikidata_index():
    lines = (RAW / "wikidata" / "language_ancestors_all.json").read_text(encoding="utf-8").splitlines()
    pairs = {}
    qid = qline = None
    for i, line in enumerate(lines, 1):
        m = re.search(r'"value" : "http://www\.wikidata\.org/entity/(Q\d+)"', line)
        if m:
            qid, qline = m.group(1), i
            continue
        m = re.search(r'"value" : "([a-z]{2})"', line)
        if m and qid:
            pairs.setdefault((m.group(1), qid), (qline, i))
    return pairs, len(lines)


def names_of(code):
    return lang_names().get(code, {code})


def charter_rows_ev(country):
    start, end, rows = charter_rows(country)
    code_of = {}
    for display, target, line in rows:
        key = re.sub(r"\s+language$", "", target)
        code = B.NAME2CODE[key] if key in B.NAME2CODE else B.NAME2CODE[display]
        code_of.setdefault(code, []).append((display, line))
    return start, end, rows, code_of


def main():
    with (ROOT / "SPOTCHECK.tsv").open(encoding="utf-8") as fh:
        head = fh.readline()
    base = (RAW / "base_SPOTCHECK.tsv").read_text(encoding="utf-8")
    rows = []
    lang_uni = [r["value"] for r in read_universe("language")]
    cwe_uni = [r["value"] for r in read_universe("cwe")]
    lang_lists = yaml.safe_load((ROOT / "lists" / "language.yaml").read_text(encoding="utf-8"))
    cwe_lists = yaml.safe_load((ROOT / "lists" / "cwe.yaml").read_text(encoding="utf-8"))
    nbase_lang = len(yaml.safe_load((RAW / "base_language.yaml").read_text(encoding="utf-8")))
    nbase_cwe = len(yaml.safe_load((RAW / "base_cwe.yaml").read_text(encoding="utf-8")))

    cwe_idx = build_cwe_index()
    wd_pairs, wd_lines = wikidata_index()
    cwe_cat = {x["id"]: re.search(r"definitions/(\d+)", x["source"]).group(1) for x in cwe_lists[nbase_cwe:]}

    def add(lid, universe, members, nonmembers, ev_member, ev_non):
        for v in spread(members):
            rows.append((lid, universe, "member", v, ev_member(v)))
        for v in spread(nonmembers):
            rows.append((lid, universe, "nonmember", v, ev_non(v)))

    for x in lang_lists[nbase_lang:]:
        lid, members = x["id"], x["members"]
        non = [v for v in lang_uni if v not in set(members)]
        if lid in dict(CHARTER):
            country = dict(CHARTER)[lid]
            start, end, table, code_of = charter_rows_ev(country)
            def ev_m(v):
                display, line = code_of[v][0]
                txt = (WIKI2 / (CHARTER_PAGE + ".wikitext")).read_text(encoding="utf-8").splitlines()[line - 1].strip()
                return f"raw/wiki_ws2/{CHARTER_PAGE}.wikitext:{line} ({txt[:110]})"
            def ev_n(v):
                nm = sorted(names_of(v))
                return (f"raw/wiki_ws2/{CHARTER_PAGE}.wikitext:{start}-{end-1} (charter table rows for {country} "
                        f"scanned; {'/'.join(nm)} absent)")
            add(lid, "language", members, non, ev_m, ev_n)
        elif lid in PAGE_LINE:
            page, marker = PAGE_LINE[lid]
            lines = wt_lines(page)
            ln = next(i for i, l in enumerate(lines, 1) if marker in l)
            def ev_m(v, line=lines[ln - 1]):
                return f"raw/wiki_ws2/{page}.wikitext:{ln} ({line.strip()[:110]})"
            def ev_n(v):
                nm = sorted(names_of(v))
                return (f"raw/wiki_ws2/{page}.wikitext:{ln} (source line lists {len(members)} languages; "
                        f"{'/'.join(nm)} absent)")
            add(lid, "language", members, non, ev_m, ev_n)
        else:
            qid = dict(BRANCH)[lid]
            def ev_m(v, qid=qid):
                qline, cline = wd_pairs[(v, qid)]
                return (f"raw/wikidata/language_ancestors_all.json:{qline} (ancestor {qid}); "
                        f":{cline} (code {v}, ancestor {qid})")
            def ev_n(v, qid=qid):
                return (f"raw/wikidata/language_ancestors_all.json:1-{wd_lines} (0 bindings pair code {v} "
                        f"with ancestor {qid})")
            add(lid, "language", members, non, ev_m, ev_n)

    for x in cwe_lists[nbase_cwe:]:
        lid, members = x["id"], x["members"]
        cid = cwe_cat[lid]
        start, end, _ = cwe_idx[cid]
        allm = cwe_members(cwe_idx, cid)
        non = [v for v in cwe_uni if v not in set(members)]
        def ev_m(v, cid=cid):
            sub, line = allm[v.replace("CWE-", "")]
            return f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{line} (Category {sub} Has_Member {v.replace('CWE-', '')})"
        def ev_n(v, cid=cid):
            return (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{start}-{end-1} (Category {cid} subtree with "
                    f"{len(allm)} members scanned; {v} absent)")
        add(lid, "cwe", members, non, ev_m, ev_n)

    out = base
    for r in rows:
        out += "\t".join(r) + "\n"
    (ROOT / "SPOTCHECK.tsv").write_text(out, encoding="utf-8")
    print("appended", len(rows), "rows", len({r[0] for r in rows}), "lists")


if __name__ == "__main__":
    main()
