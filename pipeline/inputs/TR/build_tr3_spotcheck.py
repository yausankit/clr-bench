"""Append deterministic 5-member / 5-non-member rows for TR round-3 airline lists."""
import json, os, re, sys
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_tr3_lists as b3  # noqa: E402

RAW = os.path.join(HERE, "raw")
SPOT = os.path.join(HERE, "SPOTCHECK.tsv")
NAME_ALIAS = {b3.ALIAS.get(k, k): v for k, v in {
    "China": ["China", "People's Republic of China"],
    "Gambia": ["Gambia", "The Gambia"],
    "The Gambia": ["Gambia", "The Gambia"],
    "Ivory Coast": ["Ivory Coast", "Côte d'Ivoire", "Cote d'Ivoire"],
    "Democratic Republic of the Congo": ["Democratic Republic of the Congo", "DR Congo"],
    "Czech Republic": ["Czech Republic", "Czechia"],
    "Turkey": ["Turkey", "Türkiye"],
    "Cape Verde": ["Cape Verde", "Cabo Verde"],
}.items()}

def spread(items, k=5):
    items = sorted(set(items))
    if len(items) <= k: return items
    idx = [round(j * (len(items) - 1) / (k - 1)) for j in range(k)]
    return [items[i] for i in idx]

def source_lines(title):
    return open(os.path.join(RAW, "wiki", b3.wiki_slug(title) + ".wiki"), encoding="utf-8").read().splitlines()

def scan_names(country, aliases):
    if country in b3.SCAN_ALIAS: return b3.SCAN_ALIAS[country]
    if country in aliases: return aliases[country]
    return NAME_ALIAS.get(country, [country])

def hit(line, names):
    return any(re.search(r"(?<![A-Za-z])" + re.escape(x) + r"(?![A-Za-z])", line) for x in names)

def country_line(lines, lo, hi, country, aliases):
    names = scan_names(country, aliases)
    for n in range(lo, hi + 1):
        if hit(lines[n - 1], names): return n
    raise AssertionError((country, names, lo, hi))

def airline_bindings():
    bindings = json.load(open(os.path.join(RAW, "airlines.json"), encoding="utf-8"))["results"]["bindings"]
    out = {}
    for n, b in enumerate(bindings, 1):
        out.setdefault(b.get("itemLabel", {}).get("value", ""),
                       (b.get("countryLabel", {}).get("value", ""), n))
    return out

def main():
    rows = [line.rstrip("\n").split("\t") for line in open(SPOT, encoding="utf-8")]
    header, old = rows[0], rows[1:]
    lists = {x["id"]: x for x in yaml.safe_load(open(os.path.join(HERE, "lists", "airline.yaml")))}
    uni = b3.rows()
    country_of = {r["value"]: r["attr:country"] for r in uni}
    bindings = airline_bindings()
    new_ids = [s[0] for s in b3.SPECS]
    out = []
    for lid, name, org, title, country_text, (lo, hi), official, aliases in b3.SPECS:
        countries = [b3.ALIAS.get(c, c) for c in country_text.split("|")]
        cset = set(countries)
        lines = source_lines(title)
        lst = lists[lid]
        for v in spread(lst["members"]):
            c = country_of[v]
            ln = country_line(lines, lo, hi, c, aliases)
            cn, binding_line = bindings[v]
            assert cn == c, (lid, v, c, cn)
            out.append([lid, "airline", v, "member",
                        f"raw/wiki/{b3.wiki_slug(title)}.wiki:{ln} lists {c}; "
                        f"raw/airlines.json:{binding_line} binds {v} to {c}",
                        lines[ln - 1].strip()[:220]])
        pool = [v for v in sorted(country_of) if country_of[v] not in cset]
        for v in spread(pool):
            c = country_of[v]
            cn, binding_line = bindings[v]
            assert cn == c, (lid, v, c, cn)
            # A narrow member-table range is used above; none of these countries may occur there.
            names = NAME_ALIAS.get(c, [c])
            assert not any(hit(lines[n - 1], names) for n in range(lo, hi + 1)), (lid, v, c)
            out.append([lid, "airline", v, "nonmember",
                        f"raw/wiki/{b3.wiki_slug(title)}.wiki:{lo}-{hi} {official}-country member table "
                        f"does not list {c}; raw/airlines.json:{binding_line} binds {v} to {c}",
                        f"{v} / {c}"])
    drop = set(new_ids)
    kept = [r for r in old if r[0] not in drop]
    with open(SPOT, "w", encoding="utf-8") as fh:
        fh.write("\t".join(header) + "\n")
        for r in kept: fh.write("\t".join(r) + "\n")
        for r in out: fh.write("\t".join(r) + "\n")
    print("appended", len(out), "rows for", len(new_ids), "lists")

if __name__ == "__main__": main()
