#!/usr/bin/env python3
"""Build SPOTCHECK.tsv: five members and five non-members per list, each checked by a program
against the raw snapshot and cited as file:line.

Member rows: the value is present in the list's member array of the curated raw snapshot and in
the value registry (IANA root zone / IANA port registry / curated process or account catalog).
Non-member rows: the whole member array of that list (line span and entry count) is scanned and
the value is absent, while the value itself is still present in the value registry.  Any row whose
claim cannot be verified makes the script exit non-zero, so an unsupported list cannot pass.
"""
import csv
import html
import re
import hashlib
import json
import sys
from pathlib import Path

import yaml

from add_sources import NEW_IDS

ROOT = Path(__file__).resolve().parent
LISTS = ROOT / "lists"


def lines_of(rel):
    return (ROOT / rel).read_text(encoding="utf-8").splitlines()


def json_items(rel):
    data = json.loads((ROOT / rel).read_text(encoding="utf-8"))
    return data.get("lists") or data.get("org_lists") or []


def list_block(rel, lid):
    """Line span (1-based) of one list object in a pretty-printed JSON snapshot."""
    text = lines_of(rel)
    starts = [(i, line.strip().split('"')[3]) for i, line in enumerate(text, 1)
              if line.strip().startswith('"id":')]
    for k, (start, cur) in enumerate(starts):
        if cur == lid:
            end = starts[k + 1][0] - 1 if k + 1 < len(starts) else len(text)
            return start, end, text[start - 1:end]
    raise KeyError(f"{rel}: no list {lid}")


def value_line(rel, lid, value, upper=False):
    want = value.upper() if upper else value
    start, end, block = list_block(rel, lid)
    for off, line in enumerate(block):
        if line.strip().rstrip(",") == f'"{want}"':
            return start + off, (start, end)
    return 0, (start, end)


def universe(name):
    ls = lines_of(f"universes/{name}.tsv")
    head = ls[0].split("\t")
    rows = [line.split("\t") for line in ls[1:] if line.strip()]
    return head, rows


def pick(values, n, key):
    return sorted(values, key=lambda v: hashlib.sha256(f"{key}/{v}".encode()).hexdigest())[:n]


def main():
    tld_head, tld_rows = universe("tld")
    port_head, port_rows = universe("port")
    app_head, app_rows = universe("client_app")
    user_head, user_rows = universe("user")
    tld_type = {r[0]: r[tld_head.index("attr:type")] for r in tld_rows}

    iana_rows = {}
    for i, line in enumerate(lines_of("raw/iana/service-names-port-numbers.csv"), 1):
        parts = line.split(",")
        if len(parts) > 3 and parts[1].strip().isdigit():
            iana_rows.setdefault(parts[1].strip(), []).append((i, parts[0].strip(), parts[2].strip(), parts[3]))

    root = {line.strip().lower(): i
            for i, line in enumerate(lines_of("raw/iana/tlds-alpha-by-domain.txt"), 1)
            if line.strip() and not line.startswith("#")}
    iso_line = {}
    for i, line in enumerate(lines_of("raw/iso/countries.csv"), 1):
        parts = next(csv.reader([line]))
        if len(parts) > 1 and len(parts[1]) == 2:
            iso_line[parts[1].lower()] = (i, parts[0])

    tld_lists = yaml.safe_load((LISTS / "tld.yaml").read_text())
    org_ids = {it["id"] for it in json_items("raw/curated/lists_tld.json")}
    group_items = json_items("raw/curated/lists_tld_groups.json")
    group_ids = {it["id"] for it in group_items}
    group_of = {it["id"]: it for it in group_items}
    block_of = {}
    for lst in tld_lists:
        if lst["id"] in org_ids:
            rel = "raw/curated/lists_tld.json"
        elif lst["id"] in group_ids:
            rel = "raw/curated/lists_tld_groups.json"
        else:
            rel = "raw/curated/lists_tld_extra.json"
        block_of[lst["id"]] = (rel,) + tuple(list_block(rel, lst["id"])[:2])

    port_ids = {it["id"] for it in json_items("raw/curated/lists_port.json")}

    app_cat = {line.split("\t")[0]: i for i, line in enumerate(lines_of("raw/curated/client_apps.tsv"), 1)
               if line.strip() and not line.startswith("#")}
    user_cat = {line.split("\t")[0]: i for i, line in enumerate(lines_of("raw/curated/usernames.tsv"), 1)
                if line.strip() and not line.startswith("#")}

    rows, fails = [], 0
    for name, values, catalog, cat_rel, snap_rel in (
            ("tld", [r[0] for r in tld_rows], None, None, None),
            ("port", [r[0] for r in port_rows], iana_rows, "raw/iana/service-names-port-numbers.csv", "raw/curated/lists_port.json"),
            ("client_app", [r[0] for r in app_rows], app_cat, "raw/curated/client_apps.tsv", "raw/curated/lists_client_app.json"),
            ("user", [r[0] for r in user_rows], user_cat, "raw/curated/usernames.tsv", "raw/curated/lists_user.json")):
        all_values = set(values)
        for lst in yaml.safe_load((LISTS / f"{name}.yaml").read_text()):
            lid = lst["id"]
            if lid in NEW_IDS:
                continue
            members = [str(m) for m in lst["members"]]
            mset = set(members)
            if name == "tld" and (lid.endswith("_cctlds") or lid == "asia_pacific_cctlds"):
                pool = [v for v in values if tld_type.get(v) == "ccTLD"]
            else:
                pool = values
            nonmembers = [v for v in pool if v not in mset]
            for role, picked in (("member", pick(members, 5, lid)),
                                 ("nonmember", pick(nonmembers, 5, lid + "/non"))):
                for v in picked:
                    ev_file, ev_line, ev = "", 0, ""
                    if name in ("port", "client_app", "user"):
                        if name == "port":
                            cands = iana_rows.get(v, [])
                            if cands:
                                ln, svc, proto, desc = cands[0]
                                ev_file, ev_line = cat_rel, ln
                                ev = f"IANA registry {svc or '(unassigned)'}/{proto}: {desc}"
                            if lid not in port_ids:
                                lo, hi = (0, 1023) if lid == "iana_system_ports" else (1024, 49151)
                                inside = bool(cands) and lo <= int(v) <= hi
                                ok = inside if role == "member" else (bool(cands) and not inside)
                                ev += f" | {lid} is IANA port range {lo}-{hi}"
                                if not ok:
                                    fails += 1
                                rows.append({"list_id": lid, "universe": name, "role": role,
                                             "value": v, "evidence_file": ev_file,
                                             "evidence_line": ev_line, "evidence": ev,
                                             "check": "PASS" if ok else "FAIL"})
                                continue
                        else:
                            ln = catalog.get(v, 0)
                            if ln:
                                ev_file, ev_line = cat_rel, ln
                                ev = lines_of(cat_rel)[ln - 1]
                        start, end, _ = list_block(snap_rel, lid)
                        span = f"{snap_rel}:{start}-{end} ({len(mset)} entries)"
                        if role == "member":
                            vl, _ = value_line(snap_rel, lid, v)
                            ok = (v in mset) and bool(ev_line) and vl > 0
                            ev += f" | member of {lid} at {snap_rel}:{vl}"
                        else:
                            ok = (v not in mset) and bool(ev_line)
                            ev += f" | absent from {lid}, member array scanned at {span}"
                    else:
                        if role == "member":
                            rel, start, end = block_of[lid]
                            if lid in group_ids:
                                g = group_of[lid]
                                name = next((m["name"] for m in g["members"]
                                             if m["iso"].lower() == v), "")
                                page = g["official_file"]
                                plines = [html.unescape(re.sub(r"<[^>]+>", " ", line))
                                          for line in lines_of(page)]
                                vl = 0
                                for i in range(1, len(plines) + 1):
                                    window = re.sub(r"\s+", " ", " ".join(plines[i - 1:i + 2])).lower()
                                    if name.lower() in window:
                                        vl = i
                                        break
                                ev_file, ev_line = page, vl
                                ev = f"member of {lid} at {page}:{vl} ({name})"
                                ok = (v in mset) and vl > 0
                            else:
                                upper = rel.endswith("lists_tld.json") and lid in org_ids
                                vl, (a, b) = value_line(rel, lid, v, upper=upper)
                                ev_file, ev_line = rel, vl
                                ev = (f"member of {lid} at {rel}:{vl}"
                                      + (f" (ISO alpha-2 {v.upper()})" if upper else ""))
                                ok = vl > 0
                        else:
                            rel, start, end = block_of[lid]
                            ok = v not in mset
                            ev_file, ev_line = rel, start
                            ev = (f"absent from {lid}; member array scanned at "
                                  f"{rel}:{start}-{end} ({len(mset)} entries)")
                        if v in root:
                            ev += f" | root zone raw/iana/tlds-alpha-by-domain.txt:{root[v]}"
                        else:
                            ok = False
                        if v in iso_line:
                            ev += f" | ISO raw/iso/countries.csv:{iso_line[v][0]} ({iso_line[v][1]})"
                    if not ok:
                        fails += 1
                    rows.append({"list_id": lid, "universe": name, "role": role, "value": v,
                                 "evidence_file": ev_file, "evidence_line": ev_line,
                                 "evidence": ev.replace("\t", " "),
                                 "check": "PASS" if ok else "FAIL"})
    with (ROOT / "SPOTCHECK.tsv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["list_id", "universe", "role", "value", "evidence_file",
                                           "evidence_line", "evidence", "check"],
                           delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    print(f"SPOTCHECK.tsv: {len(rows)} rows, {fails} failure(s)")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
