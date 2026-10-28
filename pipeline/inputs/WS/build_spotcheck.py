#!/usr/bin/env python3
"""Regenerate SPOTCHECK.tsv: 5 members and 5 non-members per list, each verified against raw/ lines.

Evidence format: raw file : line (quoted table cell or JSON binding).  Non-members carry a
negative check over the same source (no member row / no ancestor binding / no Has_Member path).
"""
import io
import json
import re
import zipfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
WIKI = RAW / "wiki"


def spread(seq, k=5):
    seq = list(seq)
    if len(seq) <= k:
        return seq
    return [seq[i * len(seq) // k] for i in range(k)]


def read_tsv(name):
    rows = {}
    with (ROOT / "universes" / f"{name}.tsv").open(encoding="utf-8") as fh:
        head = fh.readline().rstrip("\n").split("\t")
        for line in fh:
            row = line.rstrip("\n").split("\t")
            rows[row[0]] = dict(zip(head, row))
    return rows


# ---------------------------------------------------------------- TLD rosters
def _clean(name):
    name = re.sub(r"<!--.*?-->", "", name, flags=re.S)
    m = re.search(r"\{\{sort\|[^|]*\|([^}]*)\}\}", name)
    if m:
        name = m.group(1)
    m = re.search(r"\{\{sic\|([^|}]*)[^}]*\}\}", name)
    if m:
        name = m.group(1)
    name = re.sub(r"\[\[([^\]|]+)\|?([^\]]*)\]\]", lambda x: x.group(2) or x.group(1), name)
    return re.sub(r"<[^>]+>", "", name).strip()


TLD_ALIAS = {
    "nl": ["Netherlands"], "cz": ["Czechia", "Czech Republic"], "tr": ["Turkey", "Türkiye"],
    "us": ["United States"], "kr": ["South Korea", "Korea"], "ru": ["Russia"], "ir": ["Iran"],
    "bo": ["Bolivia"], "md": ["Moldova"], "tz": ["Tanzania"], "vn": ["Vietnam", "Viet Nam"],
    "la": ["Laos"], "fm": ["Micronesia"], "ps": ["Palestine"], "sy": ["Syria"],
    "ci": ["Côte d'Ivoire", "Cote d'Ivoire", "Ivory Coast"],
    "st": ["Sao Tome and Principe", "São Tomé and Príncipe"],
    "tl": ["Timor-Leste", "East Timor"], "nr": ["Nauru"], "gy": ["Guyana"], "tw": ["Taiwan"],
    "gq": ["Equatorial Guinea"], "uk": ["United Kingdom"], "gb": ["United Kingdom"],
}


def iso_table():
    lines = (WIKI / "ISO_3166-1_alpha-2.wikitext").read_text(encoding="utf-8").splitlines()
    out = {}
    for i, line in enumerate(lines, 1):
        m = re.match(r'\|\s*id="([A-Z]{2})"\s*\|', line)
        if not m:
            continue
        cells = line.split("||")
        if len(cells) < 5:
            continue
        name = _clean(cells[1])
        tld = re.search(r"\[\[\.([a-z0-9-]+)\]\]", cells[3])
        if tld:
            out[tld.group(1)] = {"code": m.group(1), "name": name, "line": i, "text": line.strip()}
    return out


def _names_for(value, iso):
    out = set(TLD_ALIAS.get(value, []))
    if value in iso:
        name = iso[value]["name"]
        out.add(name)
        for sep in (", Kingdom of the", ", Republic of", ", United Republic of", ", Islamic Republic of",
                    ", Plurinational State of", ", Federated States of", ", Province of China", ", State of"):
            if name.endswith(sep):
                out.add(name[: -len(sep)])
    return sorted(out, key=len, reverse=True)


def tld_rows(rows):
    iso = iso_table()
    lists = {l["id"]: l for l in yaml.safe_load((ROOT / "lists" / "tld.yaml").read_text())}
    for lid, lst in lists.items():
        page = WIKI / (lst["source"].rsplit("/", 1)[-1] + ".wikitext")
        plines = page.read_text(encoding="utf-8").splitlines()
        members = list(lst["members"])
        for v in spread(members):
            pats = _names_for(v, iso)
            hits = [(i, l) for i, l in enumerate(plines, 1)
                    if any(re.search(r"\b" + re.escape(n) + r"\b", l) for n in pats)]
            best = (next((x for x in hits if "{{flag|" in x[1]), None)
                    or next((x for x in hits if x[1].lstrip().startswith(("|", "*", "#"))), None)
                    or (hits[0] if hits else None))
            assert best, (lid, v)
            ev = (f"raw/wiki/ISO_3166-1_alpha-2.wikitext:{iso[v]['line']} "
                  f"({iso[v]['code']} .{v} {iso[v]['name']}); "
                  f"raw/wiki/{page.name}:{best[0]} ({best[1].strip()[:110]})")
            rows.append((lid, "tld", "member", v, ev))
        pool = sorted(v for v in iso if v not in set(members))
        negatives = []
        for v in pool:
            pats = _names_for(v, iso)
            if any(re.search(r"\b" + re.escape(n) + r"\b", l) for l in plines for n in pats):
                continue
            negatives.append(v)
        for v in spread(negatives):
            ev = (f"raw/wiki/ISO_3166-1_alpha-2.wikitext:{iso[v]['line']} "
                  f"({iso[v]['code']} .{v} {iso[v]['name']}); "
                  f"raw/wiki/{page.name}: 0 lines mention {iso[v]['name']} (negative check, {len(plines)} lines)")
            rows.append((lid, "tld", "nonmember", v, ev))


# ---------------------------------------------------------------- languages
LANG_ALIAS = {
    "el": ["Greek"], "es": ["Spanish"], "nb": ["Norwegian"], "no": ["Norwegian"],
    "ny": ["Chewa"], "ss": ["Swazi"], "st": ["Sotho", "Southern Sotho"],
    "nr": ["Southern Ndebele", "South Ndebele"], "nd": ["Ndebele", "North Ndebele"],
    "zh": ["Chinese"], "ga": ["Irish"], "mt": ["Maltese"], "ks": ["Kashmiri"],
    "or": ["Odia", "Oriya"], "pa": ["Punjabi"], "sd": ["Sindhi"], "as": ["Assamese"],
    "bn": ["Bengali"], "gu": ["Gujarati"], "hi": ["Hindi"], "kn": ["Kannada"],
    "ml": ["Malayalam"], "mr": ["Marathi"], "ne": ["Nepali"], "ta": ["Tamil"],
    "te": ["Telugu"], "ur": ["Urdu"], "af": ["Afrikaans"], "en": ["English"],
    "ts": ["Tsonga"], "tn": ["Tswana"], "ve": ["Venda"], "xh": ["Xhosa"], "zu": ["Zulu"],
    "sn": ["Shona"], "sl": ["Slovenian", "Slovene"], "cs": ["Czech"], "bg": ["Bulgarian"],
    "hr": ["Croatian"], "da": ["Danish"], "nl": ["Dutch"], "et": ["Estonian"],
    "fi": ["Finnish"], "fr": ["French"], "de": ["German"], "hu": ["Hungarian"],
    "it": ["Italian"], "lv": ["Latvian"], "lt": ["Lithuanian"], "pl": ["Polish"],
    "pt": ["Portuguese"], "ro": ["Romanian"], "sk": ["Slovak"], "sv": ["Swedish"],
    "is": ["Icelandic"], "ar": ["Arabic"], "ru": ["Russian"], "sw": ["Swahili"],
}

STATE_COUNTRY = {"india_eighth_schedule": "India", "south_africa_official": "South Africa",
                 "zimbabwe_official": "Zimbabwe"}


def iso639_lines():
    lines = (WIKI / "List_of_ISO_639-1_codes.wikitext").read_text(encoding="utf-8").splitlines()
    out = {}
    for i, line in enumerate(lines, 1):
        m = re.search(r'\|\s*id="([a-z]{2})"', line)
        if m and m.group(1) not in out:
            out[m.group(1)] = i
    return out


def lang_names(code, uni):
    out = set(LANG_ALIAS.get(code, []))
    entity = uni[code]["entity"]
    out.add(entity.split(",")[0].strip())
    out.add(entity)
    return sorted((x for x in out if x), key=len, reverse=True)


def _first_hit(plines, names, lo=1, hi=None):
    hi = hi or len(plines)
    for i in range(lo, hi + 1):
        line = plines[i - 1]
        if any(re.search(r"\b" + re.escape(n) + r"\b", line) for n in names):
            if line.lstrip().startswith(("|", "*", "#", "!")):
                return i, line
    for i in range(lo, hi + 1):
        line = plines[i - 1]
        if any(re.search(r"\b" + re.escape(n) + r"\b", line) for n in names):
            return i, line
    return None


def language_rows(rows):
    uni = read_tsv("language")
    iso = iso639_lines()
    lists = {l["id"]: l for l in yaml.safe_load((ROOT / "lists" / "language.yaml").read_text())}
    text = (RAW / "wikidata" / "language_ancestors_all.json").read_text(encoding="utf-8")
    binding = {}
    off = 0
    for part in text.split("}, {"):
        start = text.count("\n", 0, off) + 1
        anc = re.search(r"entity/(Q\d+)\"", part)
        code = re.search(r'"code"\s*:\s*\{[^}]*?"value"\s*:\s*"([a-z]{2,3})"', part, re.S)
        if anc and code:
            code_line = start + part[:code.start()].count("\n")
            binding.setdefault((code.group(1), anc.group(1)), (start, code_line))
        off += len(part) + 3
    for lid, lst in lists.items():
        members = list(lst["members"])
        page_name = lst["source"].rsplit("/", 1)[-1]
        if page_name.startswith("Q"):
            qid = page_name
            for v in spread(members):
                ln = binding.get((v, qid))
                assert ln, (lid, v)
                ev = (f"raw/wiki/List_of_ISO_639-1_codes.wikitext:{iso[v]} (id={v}); "
                      f"raw/wikidata/language_ancestors_all.json:{ln[0]} (binding start); "
                      f"raw/wikidata/language_ancestors_all.json:{ln[1]} (code {v}, ancestor {qid})")
                rows.append((lid, "language", "member", v, ev))
            negatives = [v for v in sorted(uni) if v not in set(members) and (v, qid) not in binding]
            for v in spread(negatives):
                ev = (f"raw/wiki/List_of_ISO_639-1_codes.wikitext:{iso[v]} (id={v}); "
                      f"raw/wikidata/language_ancestors_all.json: 0 bindings with code {v} and ancestor {qid}")
                rows.append((lid, "language", "nonmember", v, ev))
            continue
        page = WIKI / (page_name + ".wikitext")
        plines = page.read_text(encoding="utf-8").splitlines()
        lo, hi = 1, len(plines)
        if lid in STATE_COUNTRY:
            flag = "{{FlagLangs|" + STATE_COUNTRY[lid] + "}}"
            start = next((i for i, l in enumerate(plines, 1) if flag in l), None)
            assert start, (lid, flag)
            end = next((i for i in range(start + 1, len(plines)) if "{{FlagLangs|" in plines[i - 1]),
                       len(plines) + 1)
            lo, hi = start, end - 1
        for v in spread(members):
            hit = _first_hit(plines, lang_names(v, uni), lo, hi)
            assert hit, (lid, v, page_name)
            ev = (f"raw/wiki/List_of_ISO_639-1_codes.wikitext:{iso[v]} (id={v}); "
                  f"raw/wiki/{page.name}:{hit[0]} ({hit[1].strip()[:110]})")
            rows.append((lid, "language", "member", v, ev))
        negatives = []
        for v in sorted(uni):
            if v in set(members):
                continue
            if not any(re.search(r"\b" + re.escape(n) + r"\b", plines[i - 1])
                       for i in range(lo, hi + 1) for n in lang_names(v, uni)):
                negatives.append(v)
        for v in spread(negatives):
            ev = (f"raw/wiki/List_of_ISO_639-1_codes.wikitext:{iso[v]} (id={v}); "
                  f"raw/wiki/{page.name}: 0 lines in rows {lo}-{hi} mention "
                  f"{lang_names(v, uni)[0]} (negative check)")
            rows.append((lid, "language", "nonmember", v, ev))


# ---------------------------------------------------------------- CWE catalogue
def cwe_catalogue():
    z = zipfile.ZipFile(RAW / "cwec_latest.xml.zip")
    name = [n for n in z.namelist() if n.endswith(".xml") and "cwec" in n][0]
    lines = io.TextIOWrapper(z.open(name), encoding="utf-8").read().splitlines()
    weak_start, cat_start, cat_end = {}, {}, {}
    child = {}          # child id -> (parent id, line) in View 1000
    cat_members = {}    # category id -> [(member id, line)]
    cur, kind = None, None
    for i, line in enumerate(lines, 1):
        m = re.search(r'<(Weakness|Category) ID="(\d+)"', line)
        if m:
            cur, kind = m.group(2), m.group(1)
            (weak_start if kind == "Weakness" else cat_start)[cur] = i
            continue
        if re.search(r"</Weakness>", line):
            cur, kind = None, None
        elif re.search(r"</Category>", line):
            if cur:
                cat_end[cur] = i
            cur, kind = None, None
        elif kind == "Weakness":
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', line))
            if line.strip().startswith("<Related_Weakness") and attrs.get("Nature") == "ChildOf" \
                    and attrs.get("View_ID") == "1000" and cur:
                child.setdefault(cur, []).append((attrs.get("CWE_ID"), i))
        elif kind == "Category":
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', line))
            if line.strip().startswith("<Has_Member") and cur:
                cat_members.setdefault(cur, []).append((attrs.get("CWE_ID"), i))
    return lines, weak_start, cat_start, cat_end, child, cat_members


def _path_to(cid, root, child):
    """A ChildOf(1000) path from cid up to root, over all parents (the graph is a DAG)."""
    stack = [(cid, [])]
    seen = {cid}
    while stack:
        cur, path = stack.pop()
        if cur == root:
            return path
        for parent, line in child.get(cur, []):
            if parent not in seen:
                seen.add(parent)
                stack.append((parent, path + [(cur, parent, line)]))
    return None


def _cat_path(root, target, cat_members):
    queue = [(root, [])]
    seen = set()
    while queue:
        cur, path = queue.pop(0)
        if cur in seen:
            continue
        seen.add(cur)
        for member, line in cat_members.get(cur, []):
            step = path + [(cur, member, line)]
            if member == target:
                return step
            if member in cat_members:
                queue.append((member, step))
    return None


def cwe_rows(rows):
    lines, weak_start, cat_start, cat_end, child, cat_members = cwe_catalogue()
    uni = read_tsv("cwe")
    lists = {l["id"]: l for l in yaml.safe_load((ROOT / "lists" / "cwe.yaml").read_text())}
    for lid, lst in lists.items():
        root = re.search(r"definitions/(\d+)\.html", lst["source"]).group(1)
        members = list(lst["members"])
        if root in weak_start and any(lid.startswith("cwe1000_") for _ in [0]):
            for v in spread(members):
                cid = v.split("-")[1]
                ch = _path_to(cid, root, child)
                assert ch is not None, (lid, v)
                if cid == root:
                    ev = f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[cid]} (Weakness {cid}, tree root of View 1000 member {root})"
                else:
                    path = " -> ".join([cid] + [p for _, p, _ in ch])
                    ev = (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[cid]} (Weakness {cid}); "
                          f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{ch[0][2]} (ChildOf {ch[0][1]}); chain {path}; root {root}")
                rows.append((lid, "cwe", "member", v, ev))
            negatives = []
            for v in sorted(uni):
                if v in set(members):
                    continue
                cid = v.split("-")[1]
                if _path_to(cid, root, child) is None:
                    negatives.append(v)
            for v in spread(negatives):
                cid = v.split("-")[1]
                ch = child.get(cid, [])
                path = ", ".join(f"{cid}->{p} (line {ln})" for p, ln in ch) or cid + " (no ChildOf edge in View 1000)"
                ev = (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[cid]} (Weakness {cid}); "
                      f"first ChildOf edges {path}; no path to root {root}")
                rows.append((lid, "cwe", "nonmember", v, ev))
            continue
        cid = root
        assert cid in cat_start, (lid, cid)
        block = f"{cat_start[cid]}-{cat_end.get(cid, cat_start[cid])}"
        for v in spread(members):
            mid = v.split("-")[1]
            path = _cat_path(cid, mid, cat_members)
            assert path, (lid, v)
            ev = "; ".join(f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{ln} (Category {c} Has_Member {m})"
                           for c, m, ln in path)
            if len(path) > 1:
                ev += f"; nested through {len(path) - 1} subcategor{'y' if len(path) == 2 else 'ies'}"
            rows.append((lid, "cwe", "member", v, ev))
        negatives = []
        for v in sorted(uni):
            if v in set(members):
                continue
            mid = v.split("-")[1]
            if _cat_path(cid, mid, cat_members) is None:
                negatives.append(v)
        for v in spread(negatives):
            mid = v.split("-")[1]
            ev = (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[mid]} (Weakness {mid}); "
                  f"Category {cid} block lines {block}: no Has_Member path to CWE-{mid}")
            rows.append((lid, "cwe", "nonmember", v, ev))


def main():
    rows = []
    tld_rows(rows)
    language_rows(rows)
    cwe_rows(rows)
    rows.sort(key=lambda r: (r[1], r[0], r[2], r[3]))
    from collections import Counter
    counts = Counter((r[0], r[2]) for r in rows)
    bad = [k for k, v in counts.items() if v != 5]
    if bad:
        raise SystemExit(f"lists without exactly 5 members and 5 non-members: {bad[:20]}")
    out = ROOT / "SPOTCHECK.tsv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        fh.write("list_id\tuniverse\trole\tvalue\tevidence\n")
        for r in rows:
            fh.write("\t".join(r) + "\n")
    print(f"SPOTCHECK.tsv: {len(rows)} rows, {len(counts) // 2} lists, every list 5 members + 5 non-members")


if __name__ == "__main__":
    main()
