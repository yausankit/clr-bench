"""Append and verify ADD_SY_a1 SPOTCHECK rows (5 members + 5 non-members per new list).

Every row is checked against the raw SNOMED expansion and raw/snomed/names.json that produced the
list; the evidence column cites the expansion entry number or the names.json line.
Idempotent: rows for a list that already has entries are not appended again.
"""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
UNIVERSE = "procedure"
CHECKS = 5


def load_universe():
    with (ROOT / "universes" / "procedure.tsv").open(encoding="utf-8") as fh:
        return [r["value"] for r in csv.DictReader(fh, delimiter="\t")]


def names_lines():
    text = (ROOT / "raw" / "snomed" / "names.json").read_text(encoding="utf-8")
    lines = text.splitlines()
    return json.loads(text), {ln.split('"')[1]: i + 1 for i, ln in enumerate(lines) if ln.startswith('"')}


def main():
    vals = load_universe()
    names, line_no = names_lines()
    spec = list(csv.DictReader((ROOT / "add_lists_spec.tsv").open(encoding="utf-8"), delimiter="\t"))
    path = ROOT / "SPOTCHECK.tsv"
    lines = [ln for ln in path.read_text(encoding="utf-8").splitlines() if ln.strip()]
    have = {ln.split("\t")[1] for ln in lines if ln.startswith(UNIVERSE + "\t")}
    new = []
    for row in spec:
        lid, code = row["id"], row["code"]
        if lid in have:
            continue
        exp = json.loads((ROOT / "raw" / "snomed" / f"expand_{code}.json").read_text())["expansion"]
        contains = exp["contains"]
        codes = {x["code"] for x in contains}
        members = sorted(codes & set(vals))
        nonmembers = [v for v in sorted(set(vals) - codes) if v in names]
        if len(members) < CHECKS or len(nonmembers) < CHECKS:
            raise SystemExit(f"{lid}: not enough members/non-members for SPOTCHECK")
        picks = [members[i] for i in range(CHECKS)]
        nonpicks = [nonmembers[i * len(nonmembers) // CHECKS] for i in range(CHECKS)]
        for v in picks:
            i = next(i for i, x in enumerate(contains) if x["code"] == v)
            display = contains[i]["display"]
            if v in names and names[v] != display:
                raise SystemExit(f"{lid}: display mismatch for {v}: {display!r} vs {names[v]!r}")
            ev = f"raw/snomed/expand_{code}.json expansion entry #{i + 1}: code {v} \"{display}\""
            new.append([UNIVERSE, lid, "member", v, ev])
        for v in nonpicks:
            ev = (f"raw/snomed/names.json:{line_no[v]} \"{v}\": \"{names[v]}\"; "
                  f"absent from raw/snomed/expand_{code}.json ({len(contains)} entries scanned)")
            new.append([UNIVERSE, lid, "nonmember", v, ev])
    if new:
        lines.extend("\t".join(r) for r in new)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    # verification pass: every row of the new lists is rechecked against raw/
    exp_cache, checked = {}, 0
    for ln in lines:
        parts = ln.split("\t")
        if len(parts) != 5 or parts[0] != UNIVERSE:
            continue
        lid, kind, value = parts[1], parts[2], parts[3]
        spec_row = next((r for r in spec if r["id"] == lid), None)
        if spec_row is None:
            continue
        code = spec_row["code"]
        if code not in exp_cache:
            exp_cache[code] = {x["code"] for x in
                               json.loads((ROOT / "raw" / "snomed" / f"expand_{code}.json").read_text())["expansion"]["contains"]}
        inside = value in exp_cache[code]
        if kind == "member" and not inside:
            raise SystemExit(f"SPOTCHECK verification failed: {lid} member {value} not in expansion")
        if kind == "nonmember" and inside:
            raise SystemExit(f"SPOTCHECK verification failed: {lid} nonmember {value} is in expansion")
        checked += 1
    print(f"SPOTCHECK.tsv: {len(new)} rows appended, {checked} rows verified")


if __name__ == "__main__":
    main()
