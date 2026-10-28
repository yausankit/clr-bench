"""Append 5 member / 5 non-member spot-check rows for every new currency list.

Evidence is a line of the raw Wikipedia wikitext (raw/wiki/<article>.wiki, exported verbatim from
raw/wiki/<article>.json) plus the ISO 4217 table cell (raw/iso4217_page.json).  Deterministic.
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_currency_extra as bce  # noqa: E402

RAW = os.path.join(HERE, "raw")
ALIAS = {
    "Côte d'Ivoire": ["Ivory Coast", "Côte d'Ivoire", "Cabo Verde"],
    "East Timor": ["Timor-Leste", "East Timor"],
    "Bahamas": ["Bahamas"],
    "Gambia": ["Gambia"],
    "DR Congo": ["DR Congo", "Democratic Republic of the Congo"],
    "São Tomé and Príncipe": ["São Tomé and Príncipe"],
    "Saint Kitts and Nevis": ["Saint Kitts and Nevis", "St. Kitts and Nevis", "St Kitts and Nevis"],
    "Saint Vincent and the Grenadines": ["Saint Vincent and the Grenadines", "St Vincent and the Grenadines",
                                         "St. Vincent and the Grenadines"],
    "Micronesia": ["Micronesia"],
}
COUNTRY_OF_CODE = {}


def slug(title):
    return re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")


def ensure_wikitext(article):
    """Export raw/wiki/<slug>.wiki from the raw JSON response once (byte-stable)."""
    base = os.path.join(RAW, "wiki", slug(article))
    jp, wp = base + ".json", base + ".wiki"
    text = json.load(open(jp, encoding="utf-8"))["parse"]["wikitext"]
    if not os.path.exists(wp):
        with open(wp, "w", encoding="utf-8") as fh:
            fh.write(text if text.endswith("\n") else text + "\n")
    return wp


def member_lines(text, countries):
    lines = text.splitlines()
    names = {c: ALIAS.get(c, [c]) for c in countries}
    scored = []
    for i, line in enumerate(lines, 1):
        hits = [c for c, al in names.items()
                if any(re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", line) for a in al)]
        if len(hits) >= 3:
            scored.append((len(hits), i, hits))
    scored.sort(key=lambda x: (-x[0], x[1]))
    block = scored[:12]
    out = {}
    for c, al in names.items():
        for _, i, hits in block:
            if c in hits:
                out[c] = i
                break
        if c not in out:  # any line inside the block's span that names the country
            lo = min(i for _, i, _ in block) - 5
            hi = max(i for _, i, _ in block) + 5
            for i, line in enumerate(lines, 1):
                if lo <= i <= hi and any(re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", line)
                                         for a in al):
                    out[c] = i
                    break
    return lines, out


def spread(items, k=5):
    items = sorted(items)
    if len(items) <= k:
        return items
    idx = [round(j * (len(items) - 1) / (k - 1)) for j in range(k)]
    return [items[i] for i in idx]


def main():
    values = bce.universe_codes()
    c2c = bce.country_currency()
    for name, code in c2c.items():
        COUNTRY_OF_CODE.setdefault(code, name)
    table = bce.iso_table()
    rows = {}
    for _, row in table.iterrows():
        rows[str(row["Code"]).strip()] = (re.sub(r"\[[^\]]*\]", "", str(row["D[a]"])).strip(),
                                          str(row["Currency"]).strip())
    lists = {it["id"]: it for it in yaml.safe_load(open(os.path.join(HERE, "lists", "currency.yaml")))}
    new_ids = [spec[0] for spec in bce.ORGS] + ["zero_minor_unit_currencies",
                                                "three_minor_unit_currencies", "rial_named_currencies"]
    out = []
    for lid in new_ids:
        lst = lists[lid]
        members = list(lst["members"])
        nonmembers = sorted(values - set(members) - set(lst.get("disputed") or []))
        if lid in [spec[0] for spec in bce.ORGS]:
            article = next(s for s in bce.ORGS if s[0] == lid)[2]
            wp = ensure_wikitext(article)
            text = open(wp, encoding="utf-8").read()
            countries = next(s for s in bce.ORGS if s[0] == lid)[4]
            lines, hits = member_lines(text, countries)
            by_code = {}
            for c in countries:
                code = c2c.get(c)
                by_code.setdefault(code, c)
            for code in spread(members):
                country = by_code.get(code, COUNTRY_OF_CODE.get(code, code))
                ln = hits.get(country)
                if ln is None:
                    raise SystemExit(f"no member line for {lid} {code} {country}")
                out.append([lid, "currency", code, "member",
                            f"raw/wiki/{slug(article)}.wiki:{ln} + raw/iso4217_page.json row {code}",
                            lines[ln - 1].strip()[:200]])
            for code in spread(nonmembers):
                home = COUNTRY_OF_CODE.get(code, "?")
                ln = min(i for _, i, _ in sorted([(0, hits[c], c) for c in hits], key=lambda x: x[1]))
                out.append([lid, "currency", code, "nonmember",
                            f"raw/wiki/{slug(article)}.wiki:{ln} (member block; {home} absent) + "
                            f"raw/iso4217_page.json row {code}",
                            lines[ln - 1].strip()[:200]])
        elif lid == "rial_named_currencies":
            for code in spread(members):
                out.append([lid, "currency", code, "member",
                            f"raw/iso4217_page.json row {code}, Currency = {rows[code][1]}", ""])
            for code in spread(nonmembers):
                out.append([lid, "currency", code, "nonmember",
                            f"raw/iso4217_page.json row {code}, Currency = {rows[code][1]}", ""])
        else:
            want = "0" if lid == "zero_minor_unit_currencies" else "3"
            for code in spread(members):
                out.append([lid, "currency", code, "member",
                            f"raw/iso4217_page.json row {code}, column D[a] = {rows[code][0]}", rows[code][1]])
            for code in spread(nonmembers):
                out.append([lid, "currency", code, "nonmember",
                            f"raw/iso4217_page.json row {code}, column D[a] = {rows[code][0]}", rows[code][1]])
    path = os.path.join(HERE, "SPOTCHECK.tsv")
    old = [line.rstrip("\n").split("\t") for line in open(path, encoding="utf-8")]
    header, body = old[0], [r for r in old[1:] if r[0] not in set(new_ids)]
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for r in body:
            fh.write("\t".join(r) + "\n")
        for r in out:
            fh.write("\t".join(r) + "\n")
    print("appended", len(out), "rows for", len(new_ids), "lists")


if __name__ == "__main__":
    main()
