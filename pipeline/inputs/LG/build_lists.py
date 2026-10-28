#!/usr/bin/env python3
"""Build lists/<universe>.yaml from the curated list definitions in raw/curated/ and the
universes. Every member is a universe value; members outside the universe are recorded in
out_of_universe so that members + disputed + out_of_universe == official_count."""
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "curated"
UNI = ROOT / "universes"

CHANGES = {
    "schengen_cctlds": [{"value": "bg", "date": "2025-01-01", "event": "joined"},
                        {"value": "ro", "date": "2025-01-01", "event": "joined"}],
    "asean_cctlds": [{"value": "tl", "date": "2025-10-26", "event": "joined"}],
    "brics_cctlds": [{"value": "id", "date": "2025-01-06", "event": "joined"}],
}


def universe(name):
    lines = (UNI / f"{name}.tsv").read_text(encoding="utf-8").splitlines()
    return [l.split("\t")[0] for l in lines[1:] if l.strip()]


def attr_classes(name, attr):
    lines = (UNI / f"{name}.tsv").read_text(encoding="utf-8").splitlines()
    head = lines[0].split("\t")
    col = head.index("attr:" + attr)
    out = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        parts = line.split("\t")
        out.setdefault(parts[col], []).append(parts[0])
    return out


def emit(universe_name, items, values, recount=False):
    out = []
    for it in items:
        seen = set()
        members = [str(m) for m in it["members"] if not (str(m) in seen or seen.add(str(m)))]
        inside = [m for m in members if m in values]
        outside = [m for m in members if m not in values]
        outside += [str(m) for m in it.get("out_of_universe") or []]
        official = (len(members) + len(outside)) if recount else it.get("official_count", len(members))
        assert len(inside) + len(it.get("disputed") or []) + len(outside) == official, \
            f"{it['id']}: {len(inside)}+{len(outside)} != {official}"
        out.append({"id": it["id"], "name": it["name"], "synonyms": it.get("synonyms") or [],
                    "members": inside, "disputed": it.get("disputed") or [],
                    "changes": CHANGES.get(it["id"], []), "out_of_universe": outside,
                    "official_count": official, "source": it["source"], "salience": 0})
    (ROOT / "lists" / f"{universe_name}.yaml").write_text(
        yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(f"lists/{universe_name}.yaml: {len(out)} lists, {sum(len(x['members']) for x in out)} members")


def main():
    tld_vals = universe("tld")
    tld = json.loads((RAW / "lists_tld.json").read_text())["org_lists"]
    for it in tld:
        codes = it.get("iso") or []
        it["members"] = [c.lower() for c in codes if c.lower() in set(tld_vals)]
        it["out_of_universe"] = [c for c in codes if c.lower() not in set(tld_vals)]
        it["out_of_universe"] += it.get("extra_out") or []
        it["official_count"] = len(codes) + len(it.get("extra_out") or [])
    extra = json.loads((RAW / "lists_tld_extra.json").read_text())["lists"]
    emit("tld", tld + extra, set(tld_vals))
    port_items = json.loads((RAW / "lists_port.json").read_text())["lists"]
    classes = attr_classes("port", "range")
    for cid, label in (("system", "IANA system ports"), ("user", "IANA user ports")):
        port_items.append({"id": f"iana_{cid}_ports", "name": label,
                           "synonyms": ["well-known ports" if cid == "system" else "registered ports"],
                           "members": classes[cid], "disputed": [], "changes": [],
                           "out_of_universe": [], "official_count": len(classes[cid]),
                           "source": "https://www.rfc-editor.org/rfc/rfc6335", "salience": 0})
    emit("port", port_items, set(universe("port")))
    for name, src in (("client_app", "lists_client_app.json"), ("user", "lists_user.json")):
        items = json.loads((RAW / src).read_text())["lists"]
        emit(name, items, set(universe(name)), recount=True)


if __name__ == "__main__":
    main()
