#!/usr/bin/env python3
"""Unpack the large per-chain files (payload.tar.gz) next to the small ones and check them against MANIFEST.sha256.

usage: python data/unpack_chains.py [CHAIN ...]      (default: all chains in data/CHAINS.tsv)

Each payload holds bundle_k1_v0/ (practice and test task files with public views, hidden inputs and expected
answers), test_k1_v0.json (scored test instances), practice_views_v0.json, diagnostics.json (value-level diagnostic
instances) and bundle_k1_v0_rg/private/ (practice files of the rewarded-practice condition). Files listed in the
manifest but not shipped (versions 1 and 2 of each chain, L5 artifacts of other builds) are skipped by the check.
"""
import hashlib
import sys
import tarfile
from pathlib import Path

DATA = Path(__file__).resolve().parent


def chains():
    rows = [l.split("\t") for l in (DATA / "CHAINS.tsv").read_text().splitlines()[1:] if l.strip()]
    return [r[0] for r in rows]


def unpack(chain):
    d = DATA / "chains" / chain
    with tarfile.open(d / "payload.tar.gz") as tf:
        for m in tf.getmembers():
            if m.name.startswith("/") or ".." in Path(m.name).parts:
                raise SystemExit(f"{chain}: unsafe path in payload: {m.name}")
        if hasattr(tarfile, "data_filter"):
            tf.extractall(d, filter="data")
        else:
            tf.extractall(d)
    checked = bad = 0
    for line in (d / "MANIFEST.sha256").read_text().splitlines():
        digest, name = line.split(None, 1)
        p = d / name.strip()
        if not p.exists():
            continue
        checked += 1
        if hashlib.sha256(p.read_bytes()).hexdigest() != digest:
            bad += 1
            print(f"{chain}: checksum mismatch {name}")
    print(f"{chain}: unpacked, {checked} manifest files checked, {bad} mismatches")
    return bad == 0


if __name__ == "__main__":
    ok = all([unpack(c) for c in (sys.argv[1:] or chains())])
    sys.exit(0 if ok else 1)
