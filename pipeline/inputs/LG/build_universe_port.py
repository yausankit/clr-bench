#!/usr/bin/env python3
"""Build universes/port.tsv from the IANA Service Name and Transport Protocol Port
Number Registry (raw/iana/service-names-port-numbers.csv).
Attribute: RFC 6335 range (system 0-1023, user 1024-49151) and transport protocol."""
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
MAX_PORT = 49151


def main():
    rows = list(csv.DictReader((RAW / "iana" / "service-names-port-numbers.csv").open(encoding="utf-8")))
    by_port = {}
    for r in rows:
        name = (r["Service Name"] or "").strip()
        num = (r["Port Number"] or "").strip()
        proto = (r["Transport Protocol"] or "").strip()
        if not name or not num.isdigit() or proto not in ("tcp", "udp"):
            continue
        port = int(num)
        if port > MAX_PORT:
            continue
        rec = by_port.setdefault(port, {"names": [], "proto": set()})
        rec["names"].append(name)
        rec["proto"].add(proto)
    out = ["value\tentity\tattr:range\tattr:transport"]
    for port in sorted(by_port):
        rec = by_port[port]
        proto = rec["proto"]
        transport = "tcp" if proto == {"tcp"} else "udp" if proto == {"udp"} else "both"
        rng = "system" if port <= 1023 else "user"
        out.append(f"{port}\t{rec['names'][0]}\t{rng}\t{transport}")
    (ROOT / "universes" / "port.tsv").write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"port: {len(by_port)} values")


if __name__ == "__main__":
    main()
