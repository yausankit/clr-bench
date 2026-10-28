#!/usr/bin/env python3
"""Build universes/client_app.tsv and universes/user.tsv from the curated catalogs in
raw/curated/ (which record the process names / login names and their public sources)."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "curated"


def write(name, src, header):
    rows = [l.rstrip("\n") for l in (RAW / src).read_text(encoding="utf-8").splitlines()
            if l.strip() and not l.startswith("#")]
    out = [header]
    seen = set()
    for r in rows:
        parts = r.split("\t")
        if len(parts) != 3:
            raise SystemExit(f"{src}: bad row {r!r}")
        if parts[0] in seen:
            raise SystemExit(f"{src}: duplicate {parts[0]}")
        seen.add(parts[0])
        out.append("\t".join(parts))
    (ROOT / "universes" / name).write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{name}: {len(seen)} values")


if __name__ == "__main__":
    write("client_app.tsv", "client_apps.tsv", "value\tentity\tattr:vendor")
    write("user.tsv", "usernames.tsv", "value\tentity\tattr:role")
