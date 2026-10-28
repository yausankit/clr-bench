"""Independently verify every TR round-3 SPOTCHECK row against raw snapshots."""
import json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_tr3_lists as b3  # noqa: E402
import build_tr3_spotcheck as bs  # noqa: E402

RAW = os.path.join(HERE, "raw")

def bindings():
    rows = json.load(open(os.path.join(RAW, "airlines.json"), encoding="utf-8"))["results"]["bindings"]
    out = {}
    for n, b in enumerate(rows, 1):
        out.setdefault(b.get("itemLabel", {}).get("value", ""),
                       (b.get("countryLabel", {}).get("value", ""), n))
    return out

def main():
    lists = {x["id"]: x for x in yaml.safe_load(open(os.path.join(HERE, "lists", "airline.yaml")))}
    country_of = {r["value"]: r["attr:country"] for r in b3.rows()}
    bind = bindings()
    rows = [line.rstrip("\n").split("\t") for line in open(os.path.join(HERE, "SPOTCHECK.tsv"), encoding="utf-8")][1:]
    ok = True
    for lid, name, org, title, country_text, (lo, hi), official, aliases in b3.SPECS:
        countries = [b3.ALIAS.get(c, c) for c in country_text.split("|")]
        cset = set(countries)
        lines = bs.source_lines(title)
        slug = b3.wiki_slug(title)
        mine = [r for r in rows if r[0] == lid]
        mem = [r for r in mine if r[3] == "member"]
        non = [r for r in mine if r[3] == "nonmember"]
        problems = []
        if len(mem) != 5: problems.append(f"{len(mem)} members")
        if len(non) != 5: problems.append(f"{len(non)} non-members")
        if len({r[2] for r in mine}) != 10: problems.append("duplicate airline values")
        if len(lists[lid]["members"]) < 10 or len(set(countries) & set(country_of.values())) < 4:
            problems.append("list threshold")
        for c in countries:
            try: bs.country_line(lines, lo, hi, c, aliases)
            except AssertionError: problems.append(f"source table lacks {c}")
        for r in mine:
            v, role, ev = r[2], r[3], r[4]
            if v not in country_of: problems.append(f"{v}: not in airline universe"); continue
            c = country_of[v]
            if (v in set(lists[lid]["members"])) != (role == "member"):
                problems.append(f"{v}: wrong role")
            if role == "member":
                m = re.search(r"raw/wiki/([^:]+\.wiki):(\d+) lists (.+?); raw/airlines\.json:(\d+) binds (.+?) to (.+)$", ev)
                if not m: problems.append(f"{v}: bad member evidence"); continue
                wslug, ln, ec, bln, evv, ecc = m.groups()
                ln, bln = int(ln), int(bln)
                if wslug[:-5] != slug or not (lo <= ln <= hi): problems.append(f"{v}: source line out of table")
                if ec != c or ecc != c or evv != v: problems.append(f"{v}: evidence country/value mismatch")
                names = bs.scan_names(c, aliases)
                if not bs.hit(lines[ln - 1], names): problems.append(f"{v}: cited line does not name {c}")
                if c not in cset: problems.append(f"{v}: member country {c} outside source set")
                if bind.get(v) != (c, bln): problems.append(f"{v}: airline binding mismatch")
            else:
                m = re.search(r"raw/wiki/([^:]+\.wiki):(\d+)-(\d+) (\d+)-country member table does not list (.+?); raw/airlines\.json:(\d+) binds (.+?) to (.+)$", ev)
                if not m: problems.append(f"{v}: bad nonmember evidence"); continue
                wslug, a, b, oc, ec, bln, evv, ecc = m.groups()
                a, b, oc, bln = int(a), int(b), int(oc), int(bln)
                if (wslug[:-5], a, b, oc) != (slug, lo, hi, official): problems.append(f"{v}: cited table mismatch")
                if ec != c or ecc != c or evv != v: problems.append(f"{v}: evidence country/value mismatch")
                if c in cset: problems.append(f"{v}: non-member country {c} is in source set")
                names = bs.NAME_ALIAS.get(c, [c])
                if any(bs.hit(lines[n - 1], names) for n in range(lo, hi + 1)):
                    problems.append(f"{v}: country {c} appears in member table")
                if bind.get(v) != (c, bln): problems.append(f"{v}: airline binding mismatch")
        status = "PASS" if not problems else "FAIL"
        ok = ok and not problems
        print(status, lid, "; ".join(problems[:5]))
    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1

if __name__ == "__main__": sys.exit(main())
