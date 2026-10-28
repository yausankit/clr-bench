"""Re-check every spot-check row of the new currency lists against raw/.

For organisation lists the role is recomputed from the Wikipedia member block stored in
raw/wiki/<article>.json (member country -> ISO 4217 currency via the raw ISO table); for the ISO
classes and the name family it is recomputed from the raw ISO table cells.
"""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_currency_extra as bce  # noqa: E402
import build_spotcheck as bsc  # noqa: E402


def main():
    values = bce.universe_codes()
    c2c = bce.country_currency()
    table = bce.iso_table()
    dcol, names = {}, {}
    for _, row in table.iterrows():
        code = str(row["Code"]).strip()
        dcol[code] = re.sub(r"\[[^\]]*\]", "", str(row["D[a]"])).strip()
        names[code] = str(row["Currency"]).strip()
    lists = {it["id"]: it for it in yaml.safe_load(open(os.path.join(HERE, "lists", "currency.yaml")))}
    orgs = {s[0]: s for s in bce.ORGS}
    new_ids = list(orgs) + ["zero_minor_unit_currencies", "three_minor_unit_currencies",
                            "rial_named_currencies"]
    rows = [line.rstrip("\n").split("\t") for line in open(os.path.join(HERE, "SPOTCHECK.tsv"),
                                                           encoding="utf-8")][1:]
    ok = True
    for lid in new_ids:
        lst = lists[lid]
        mine = [r for r in rows if r[0] == lid]
        mem = [r for r in mine if r[3] == "member"]
        non = [r for r in mine if r[3] == "nonmember"]
        problems = []
        if len(mem) != 5 or len(non) != 5:
            problems.append(f"{len(mem)} members / {len(non)} non-members")
        if lid in orgs:
            _, _, article, _, countries, _ = orgs[lid]
            text = open(os.path.join(HERE, "raw", "wiki", bsc.slug(article) + ".wiki"), encoding="utf-8").read()
            lines, hits = bsc.member_lines(text, countries)
            by_code = {}
            for c in countries:
                by_code.setdefault(c2c.get(c), c)
            for r in mine:
                code, role, ev = r[2], r[3], r[4]
                country = by_code.get(code)
                if role == "member":
                    if country is None:
                        problems.append(f"{code}: no member country maps to it")
                        continue
                    ln = int(re.search(r"\.wiki:(\d+)", ev).group(1))
                    if ln != hits.get(country):
                        problems.append(f"{code}: cited line {ln} != member line {hits.get(country)}")
                    if not any(re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", lines[ln - 1])
                               for a in bsc.ALIAS.get(country, [country])):
                        problems.append(f"{code}: member line {ln} does not name {country}")
                else:
                    if code in lst["members"]:
                        problems.append(f"{code}: listed as non-member but is a member")
                    ln = int(re.search(r"\.wiki:(\d+)", ev).group(1))
                    nhit = sum(1 for c in countries
                               if any(re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", lines[ln - 1])
                                      for a in bsc.ALIAS.get(c, [c])))
                    if nhit < 3:
                        problems.append(f"{code}: cited line {ln} is not a member block")
        else:
            for r in mine:
                code, role = r[2], r[3]
                if role == "member" and code not in lst["members"]:
                    problems.append(f"{code}: not in list but marked member")
                if role == "nonmember" and code in lst["members"]:
                    problems.append(f"{code}: in list but marked non-member")
                if lid == "zero_minor_unit_currencies" and (dcol.get(code) == "0") != (role == "member"):
                    problems.append(f"{code}: D[a]={dcol.get(code)} role {role}")
                if lid == "three_minor_unit_currencies" and (dcol.get(code) == "3") != (role == "member"):
                    problems.append(f"{code}: D[a]={dcol.get(code)} role {role}")
                if lid == "rial_named_currencies":
                    hit = bool(re.search(r"\b(rial|riyal)$", names.get(code, ""), re.I))
                    if hit != (role == "member"):
                        problems.append(f"{code}: name {names.get(code)!r} role {role}")
        status = "PASS" if not problems else "FAIL"
        ok = ok and not problems
        print(status, lid, "; ".join(problems[:4]))
    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
