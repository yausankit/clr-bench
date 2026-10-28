#!/usr/bin/env python3
"""Build SPOTCHECK.tsv with five members and five non-members per list, citing raw rows."""
from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

import yaml
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
sys.path.insert(0, str(ROOT))
import build_lists as bl  # noqa: E402

SOURCE_FALLBACK = {
    "commonwealth": ["commonwealth_member_countries.html", "wikidata_country_group_members.json"],
    "asean": ["wikidata_country_group_members.json"],
    "arab_league": ["wikidata_country_group_members.json"],
    "nsg": ["wikidata_country_group_members.json"],
    "australia_group": ["wikidata_country_group_members.json"],
    "opec": ["wikidata_opec_members.json"],
    "g7": ["wikipedia_g7.txt", "wikidata_g7_entity.json"],
    "gcc": ["wikipedia_gcc.txt", "wikidata_gcc_entity.json"],
}


def norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", text.lower())


def source_files(item: dict) -> list[str]:
    files = re.findall(r"[A-Za-z0-9_.-]+\.(?:html|pdf|js|json)", str(item.get("source", "")))
    files.extend(SOURCE_FALLBACK.get(item["id"], []))
    out = []
    for name in files:
        if (RAW / name).exists() and name not in out:
            out.append(name)
    return out


def entity_name(universe: str, value: str) -> str:
    rows = {"chemical": bl.CHEM_ROWS, "country": bl.COUNTRY_ROWS, "carrier": bl.CARRIER_ROWS}[universe]
    return next((r["entity"] for r in rows if r["value"] == value), value)


def needles_for(item: dict, value: str) -> list[str]:
    universe = item["universe"]
    resolver = bl.resolve_chem if universe == "chemical" else bl.resolve_country if universe == "country" else bl.resolve_carrier
    out = []
    for label, hint in bl.OFFICIAL_BY_LIST.get(item["id"], []):
        mapped = resolver(label, hint) if universe == "chemical" else resolver(label)
        if mapped == value:
            if universe == "country":
                out.append(entity_name(universe, value))
            else:
                out.extend([label, hint])
            break
    if universe == "country":
        out.append(entity_name(universe, value))
        for filename in ("wikidata_country_group_members.json", "wikidata_opec_members.json"):
            path = RAW / filename
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                for row in data["results"]["bindings"]:
                    if row.get("iso", {}).get("value") == value:
                        out.append(row.get("itemLabel", {}).get("value", ""))
    for needle in list(out):
        if "(" in needle:
            out.append(needle.split("(", 1)[0].strip())
    out.extend(re.findall(r"\b\d{2,7}-\d{2}-\d\b", str(hint if 'hint' in locals() else "")))
    return [x for x in out if x and len(x) > 2]


def text_evidence(filename: str, needles: list[str]) -> tuple[str, bool]:
    path = RAW / filename
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    for i, line in enumerate(lines, 1):
        folded = norm(line)
        if any(norm(x) in folded or (re.fullmatch(r"[\d-]+", x) and x in line) for x in needles):
            return f"{filename}:L{i} contains {needles[0]!r}", True
    return f"{filename}:lines 1-{len(lines)} scanned", False


def pdf_evidence(filename: str, needles: list[str], cache: dict) -> tuple[str, bool]:
    if filename not in cache:
        cache[filename] = [(i + 1, page.extract_text() or "")
                           for i, page in enumerate(PdfReader(RAW / filename).pages)]
    pages = cache[filename]
    for page_no, text in pages:
        folded = norm(text)
        if any(norm(x) in folded or (re.fullmatch(r"[\d-]+", x) and x in text) for x in needles):
            return f"{filename}:p{page_no} contains {needles[0]!r}", True
    return f"{filename}:pages 1-{len(pages)} scanned", False


def find_member(item: dict, value: str, pdf_cache: dict) -> str:
    needles = needles_for(item, value)
    files = source_files(item)
    for filename in files:
        if filename.endswith(".pdf"):
            evidence, found = pdf_evidence(filename, needles, pdf_cache)
        else:
            evidence, found = text_evidence(filename, needles)
        if found:
            return evidence
    return "UNVERIFIED: " + ", ".join(files)


def absence_evidence(item: dict, value: str) -> str:
    files = source_files(item)
    filename = files[0] if files else "raw"
    path = RAW / filename
    rows = len(bl.OFFICIAL_BY_LIST.get(item["id"], []))
    if path.suffix == ".pdf":
        pages = len(PdfReader(path).pages)
        return f"{filename}:pages 1-{pages}, member table records={rows}; {entity_name(item['universe'], value)} absent"
    lines = len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    return f"{filename}:lines 1-{lines}, member table records={rows}; {entity_name(item['universe'], value)} absent"


def main() -> None:
    bl.main()
    lists = []
    for path in sorted((ROOT / "lists").glob("*.yaml")):
        universe = path.stem
        for item in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            item["universe"] = universe
            lists.append(item)
    pdf_cache = {}
    rows = []
    for item in lists:
        members = sorted(item["members"])[:5]
        if len(members) < 5:
            raise ValueError(f"{item['id']}: fewer than five members")
        excluded = set(item["members"]) | set(item["disputed"])
        universe_values = {"chemical": bl.CHEM_ROWS, "country": bl.COUNTRY_ROWS,
                           "carrier": bl.CARRIER_ROWS}[item["universe"]]
        nonmembers = [r["value"] for r in universe_values if r["value"] not in excluded][:5]
        for value in members:
            rows.append([item["id"], item["universe"], value, "member", find_member(item, value, pdf_cache)])
        for value in nonmembers:
            rows.append([item["id"], item["universe"], value, "nonmember", absence_evidence(item, value)])
    out = ROOT / "SPOTCHECK.tsv"
    with out.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.writer(fh, delimiter="\t", lineterminator="\n")
        writer.writerow(["list_id", "universe", "value", "role", "evidence"])
        writer.writerows(rows)
    unverified = [row for row in rows if row[3] == "member" and row[4].startswith("UNVERIFIED")]
    print(f"wrote {out}: {len(lists)} lists, {len(rows)} rows, unverified={len(unverified)}")
    for row in unverified:
        print("UNVERIFIED", row, file=sys.stderr)
    if unverified:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
