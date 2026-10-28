"""Re-check every SPOTCHECK row of the lists added in TR round 2 against raw/."""
import json
import os
import re
import sys

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_currency_extra as bce  # noqa: E402
import build_tr2_lists as btl  # noqa: E402
import build_tr2_spotcheck as bsc  # noqa: E402


def main():
    values = bce.universe_codes()
    iso = bsc.iso_rows()
    airlines = bsc.airline_index()
    airline_lists = {x["id"]: x for x in yaml.safe_load(open(os.path.join(HERE, "lists", "airline.yaml")))}
    currency_lists = {x["id"]: x for x in yaml.safe_load(open(os.path.join(HERE, "lists", "currency.yaml")))}
    rows = [line.rstrip("\n").split("\t") for line in open(os.path.join(HERE, "SPOTCHECK.tsv"),
                                                           encoding="utf-8")][1:]
    new_air = [b[0] for b in btl.AIRLINE_BLOCS]
    new_cur = ["usd_pegged_currencies", "eur_linked_currencies", "fixed_exchange_rate_currencies",
               "currency_union_currencies", "eccas_currencies", "sica_currencies"]
    uni_rows = btl.universe_rows("airline")
    country_of = {r["value"]: r["attr:country"] for r in uni_rows}
    fixed = {c: (d, a, ln) for d, a, c, ln in bsc.fixed_rows_with_lines() if c}
    euro = dict((c, ln) for c, ln in bsc.euro_rows_with_lines())
    union = {}
    for c, ln in bsc.union_rows_with_lines():
        union.setdefault(c, ln)
    ok = True
    for lid in new_air + new_cur:
        mine = [r for r in rows if r[0] == lid]
        mem = [r for r in mine if r[3] == "member"]
        non = [r for r in mine if r[3] == "nonmember"]
        problems = []
        if len(mem) != 5 or len(non) != 5:
            problems.append(f"{len(mem)} members / {len(non)} non-members")
        if lid in new_air:
            spec = next(b for b in btl.AIRLINE_BLOCS if b[0] == lid)
            article, countries = spec[2], set(spec[4])
            lines = bsc.wiki_lines(article)
            for r in mine:
                v, role, ev = r[2], r[3], r[4]
                want = v in set(airline_lists[lid]["members"])
                if want != (role == "member"):
                    problems.append(f"{v}: role {role} wrong")
                if v not in country_of:
                    problems.append(f"{v}: not in airline universe")
                    continue
                c = country_of[v]
                if (c in countries) != (role == "member"):
                    problems.append(f"{v}: country {c} role mismatch")
                cn = int(re.search(r"binding (\d+)", ev).group(1))
                ctry, cn0 = airlines[v]
                if cn != cn0 or ctry != c:
                    problems.append(f"{v}: binding {cn} != {cn0} ({ctry})")
                if role == "member":
                    ln = int(re.search(r"\.wiki:(\d+)", ev).group(1))
                    al = bsc.ALIAS.get(c, [c])
                    if not any(re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", lines[ln - 1])
                               for a in al):
                        problems.append(f"{v}: line {ln} does not name {c}")
        elif lid in ("usd_pegged_currencies", "fixed_exchange_rate_currencies"):
            members = set(currency_lists[lid]["members"])
            for r in mine:
                code, role = r[2], r[3]
                if (code in members) != (role == "member"):
                    problems.append(f"{code}: role {role} wrong")
                if role == "member":
                    d, a, ln = fixed[code]
                    if "usd" in lid and a != "USD":
                        problems.append(f"{code}: anchor {a}")
                    ln2 = int(re.search(r"\.wiki:(\d+)", r[4]).group(1))
                    if ln2 != ln or d not in r[4]:
                        problems.append(f"{code}: cited line {ln2} != {ln} ({d})")
                elif code in fixed and lid == "usd_pegged_currencies" and fixed[code][1] == "USD":
                    problems.append(f"{code}: listed as non-member but USD-anchored")
        elif lid == "eur_linked_currencies":
            members = set(currency_lists[lid]["members"])
            for r in mine:
                code, role = r[2], r[3]
                if (code in members) != (role == "member"):
                    problems.append(f"{code}: role {role} wrong")
                if role == "member":
                    ln = int(re.search(r"\.wiki:(\d+)", r[4]).group(1))
                    if euro.get(code) != ln:
                        problems.append(f"{code}: cited line {ln} != {euro.get(code)}")
                    if not bsc.wiki_lines("International_status_and_usage_of_the_euro")[ln - 1].startswith("| " + code):
                        problems.append(f"{code}: line {ln} does not carry the code")
                elif code in euro:
                    problems.append(f"{code}: in euro table but marked non-member")
        elif lid == "currency_union_currencies":
            members = set(currency_lists[lid]["members"])
            ulines = bsc.wiki_lines("Currency_union")
            for r in mine:
                code, role = r[2], r[3]
                if (code in members) != (role == "member"):
                    problems.append(f"{code}: role {role} wrong")
                if role == "member":
                    ln = int(re.search(r"\.wiki:(\d+)", r[4]).group(1))
                    if union.get(code) != ln:
                        problems.append(f"{code}: cited line {ln} != {union.get(code)}")
                    names = btl.iso_name_map()
                    hit = False
                    for l in re.findall(r"\[\[([^\]\|#]+)", ulines[ln - 1]):
                        l = btl.norm_name(l)
                        codes = btl.UNION_NAMES.get(l)
                        if codes is None:
                            one = names.get(l)
                            codes = [one] if one else []
                        hit = hit or code in codes
                    if not hit:
                        problems.append(f"{code}: line {ln} does not map to the code")
                elif code in union:
                    problems.append(f"{code}: in union table but marked non-member")
        else:  # eccas_currencies / sica_currencies
            lst = currency_lists[lid]
            countries = (["Angola", "Burundi", "Cameroon", "Central African Republic", "Chad",
                          "Republic of the Congo", "Democratic Republic of the Congo", "Equatorial Guinea",
                          "Gabon", "Rwanda", "São Tomé and Príncipe"] if lid == "eccas_currencies" else
                         ["Belize", "Costa Rica", "Dominican Republic", "El Salvador", "Guatemala",
                          "Honduras", "Nicaragua", "Panama"])
            c2c = bce.country_currency()
            by_code = {}
            for c in countries:
                by_code.setdefault({"El Salvador": "USD"}.get(c, c2c.get(c)), c)
            article = ("Economic Community of Central African States" if lid == "eccas_currencies"
                       else "Central American Integration System")
            lines = bsc.wiki_lines(article)
            members = set(lst["members"])
            for r in mine:
                code, role = r[2], r[3]
                if (code in members) != (role == "member"):
                    problems.append(f"{code}: role {role} wrong")
                if role == "member":
                    c = by_code.get(code)
                    if c is None:
                        problems.append(f"{code}: no member country maps to it")
                        continue
                    ln = int(re.search(r"\.wiki:(\d+)", r[4]).group(1))
                    al = bsc.ALIAS.get(c, [c])
                    if not any(re.search(r"(?<![A-Za-z])" + re.escape(a) + r"(?![A-Za-z])", lines[ln - 1])
                               for a in al):
                        problems.append(f"{code}: line {ln} does not name {c}")
                elif code in by_code:
                    problems.append(f"{code}: member country {by_code[code]} but marked non-member")
        status = "PASS" if not problems else "FAIL"
        ok = ok and not problems
        print(status, lid, "; ".join(problems[:4]))
    print("ALL PASS" if ok else "FAILURES")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
