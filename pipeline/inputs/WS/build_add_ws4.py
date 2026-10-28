#!/usr/bin/env python3
"""Append 18 MITRE-official CWE groupings to lists/cwe.yaml and SPOTCHECK.tsv.

Only source data is read from raw/: the MITRE CWE 4.20 XML package, pageview JSON
under raw/ws4_pageviews/, and byte-preserving baseline files under raw/base_add_ws4_*.
"""
import io
import json
import re
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw"
NS = "{http://cwe.mitre.org/cwe-7}"


NEW_LISTS = [
    # id, view, catalogue id, exact official category/tree name, Wikipedia title
    ("cwe1400_access_control", "1400", "1396", "Access Control", "Access_control"),
    ("cwe1400_concurrency", "1400", "1401", "Concurrency", "Concurrency_(computer_science)"),
    ("cwe1400_encryption", "1400", "1402", "Encryption", "Encryption"),
    ("cwe1400_file_handling", "1400", "1404", "File Handling", "Computer_file"),
    ("cwe1400_improper_neutralization", "1400", "1407", "Improper Neutralization", "Taint_checking"),
    ("cwe1400_injection", "1400", "1409", "Injection", "Code_injection"),
    ("cwe1400_memory_safety", "1400", "1399", "Memory Safety", "Memory_safety"),
    ("cwe1400_poor_coding_practices", "1400", "1412", "Poor Coding Practices", "Coding_conventions"),
    ("cwe1400_resource_lifecycle_management", "1400", "1416", "Resource Lifecycle Management", "Resource_management"),
    ("cwe1400_sensitive_information_exposure", "1400", "1417", "Sensitive Information Exposure", "Information_leakage"),
    ("cwe700_security_features", "700", "254", "7PK - Security Features", "Computer_security"),
    ("cwe700_encapsulation", "700", "485", "7PK - Encapsulation", "Encapsulation_(computer_programming)"),
    ("cwe1194_privilege_separation", "1194", "1198", "Privilege Separation and Access Control Issues", "Access_control"),
    ("cwe1194_circuit_logic", "1194", "1199", "General Circuit and Logic Design Concerns", "Integrated_circuit_design"),
    ("cwe699_authentication_errors", "699", "1211", "Authentication Errors", "Authentication"),
    ("cwe699_authorization_errors", "699", "1212", "Authorization Errors", "Authorization"),
    ("cwe1000_285", "1000", "285", "Improper Authorization", "Authorization"),
    ("cwe1000_1390", "1000", "1390", "Weak Authentication", "Authentication"),
]

VIEW_NAMES = {
    "1400": "CWE-1400 Comprehensive Categorization for Software Assurance Trends",
    "700": "CWE-700 Seven Pernicious Kingdoms",
    "1194": "CWE-1194 Hardware Design",
    "699": "CWE-699 Software Development",
    "1000": "CWE-1000 Research Concepts",
}


def spread(seq, k=5):
    seq = list(seq)
    if len(seq) <= k:
        return seq
    return [seq[i * len(seq) // k] for i in range(k)]


def xml_source():
    z = zipfile.ZipFile(RAW / "cwec_latest.xml.zip")
    name = [n for n in z.namelist() if n.endswith(".xml") and "cwec" in n][0]
    return ET.fromstring(z.read(name)), name


def category_members(root, cid, seen=None):
    cats = {c.get("ID"): c for c in root.find(NS + "Categories").findall(NS + "Category")}
    seen = set() if seen is None else seen
    for member in cats[cid].findall(f"{NS}Relationships/{NS}Has_Member"):
        mid = member.get("CWE_ID")
        if mid in cats:
            if mid not in seen:
                seen.add(mid)
                category_members(root, mid, seen)
        else:
            seen.add(mid)
    return seen


def class_tree(root, cid):
    weak = {w.get("ID"): w for w in root.find(NS + "Weaknesses").findall(NS + "Weakness")}
    children = {}
    for wid, weakness in weak.items():
        for rel in weakness.findall(f"{NS}Related_Weaknesses/{NS}Related_Weakness"):
            if rel.get("Nature") == "ChildOf" and rel.get("View_ID") == "1000":
                children.setdefault(rel.get("CWE_ID"), []).append(wid)
    seen, stack = {cid}, [cid]
    while stack:
        node = stack.pop()
        for child in children.get(node, []):
            if child not in seen:
                seen.add(child)
                stack.append(child)
    return seen


def _cat_path(root, start, target):
    cats = {c.get("ID"): c for c in root.find(NS + "Categories").findall(NS + "Category")}
    queue, seen = [(start, [])], set()
    while queue:
        cur, path = queue.pop(0)
        if cur in seen:
            continue
        seen.add(cur)
        for member in cats[cur].findall(f"{NS}Relationships/{NS}Has_Member"):
            mid = member.get("CWE_ID")
            step = path + [(cur, mid)]
            if mid == target:
                return step
            if mid in cats:
                queue.append((mid, step))
    return None


def _tree_path(weak, start, target):
    stack, seen = [(start, [])], {start}
    while stack:
        cur, path = stack.pop()
        if cur == target:
            return path
        for rel in weak[cur].findall(f"{NS}Related_Weaknesses/{NS}Related_Weakness"):
            if rel.get("Nature") != "ChildOf" or rel.get("View_ID") != "1000":
                continue
            parent = rel.get("CWE_ID")
            if parent not in seen:
                seen.add(parent)
                stack.append((parent, path + [(cur, parent)]))
    return None


def _line_index():
    z = zipfile.ZipFile(RAW / "cwec_latest.xml.zip")
    name = [n for n in z.namelist() if n.endswith(".xml") and "cwec" in n][0]
    lines = io.TextIOWrapper(z.open(name), encoding="utf-8").read().splitlines()
    weak_start, weak_end, cat_start, cat_end = {}, {}, {}, {}
    cat_member_line = {}
    cur, kind = None, None
    for number, line in enumerate(lines, 1):
        match = re.search(r'<(Weakness|Category) ID="(\d+)"', line)
        if match:
            cur, kind = match.group(2), match.group(1)
            (weak_start if kind == "Weakness" else cat_start)[cur] = number
            continue
        if re.search(r"</Weakness>", line):
            if cur:
                weak_end[cur] = number
            cur, kind = None, None
        elif re.search(r"</Category>", line):
            if cur:
                cat_end[cur] = number
            cur, kind = None, None
        elif kind == "Category":
            attrs = dict(re.findall(r'(\w+)="([^"]*)"', line))
            if line.strip().startswith("<Has_Member") and cur:
                cat_member_line[(cur, attrs.get("CWE_ID"))] = number
    return lines, weak_start, weak_end, cat_start, cat_end, cat_member_line


def pageviews(title):
    path = RAW / "ws4_pageviews" / f"pv_{title}.json"
    items = json.loads(path.read_text(encoding="utf-8"))["items"]
    months = [item["timestamp"] for item in items]
    expected = [f"{year}{month:02d}0100" for year, month in
                [(2025, m) for m in range(10, 13)] + [(2026, m) for m in range(1, 10)]]
    assert months == expected, (path, months)
    return sum(int(item["views"]) for item in items)


def make_entry(view, cid, official_name, members, universe, title, species):
    all_members = sorted(members, key=int)
    in_universe = ["CWE-" + cid for cid in all_members if "CWE-" + cid in universe]
    out = ["CWE-" + cid for cid in all_members if "CWE-" + cid not in universe]
    if species == "category":
        list_id = [x[0] for x in NEW_LISTS if x[1] == view and x[2] == cid][0]
        name = f"{VIEW_NAMES[view]} category: {official_name} (CWE-{cid})"
        synonyms = [official_name, f"CWE-{cid} category"]
    else:
        list_id = f"cwe1000_{cid}"
        name = f"CWE-1000 Research Concepts subtree: {official_name} (CWE-{cid})"
        synonyms = [official_name, f"CWE-{cid} subtree"]
    return {
        "id": list_id,
        "name": name,
        "synonyms": synonyms,
        "members": in_universe,
        "disputed": [],
        "changes": [],
        "out_of_universe": out,
        "official_count": len(all_members),
        "source": f"https://cwe.mitre.org/data/definitions/{cid}.html",
        "salience": pageviews(title),
    }


def generate_lists(root, universe):
    cats = {c.get("ID"): c for c in root.find(NS + "Categories").findall(NS + "Category")}
    weak = {w.get("ID"): w for w in root.find(NS + "Weaknesses").findall(NS + "Weakness")}
    entries = []
    for list_id, view, cid, official_name, title in NEW_LISTS:
        if view == "1000":
            ids = class_tree(root, cid)
            species = "tree"
            official_name = weak[cid].get("Name")
        else:
            ids = category_members(root, cid)
            species = "category"
            official_name = cats[cid].get("Name")
        all_weak = {mid for mid in ids if mid in weak}
        entry = make_entry(view, cid, official_name, all_weak, universe, title, species)
        assert entry["id"] == list_id, (entry["id"], list_id)
        assert entry["official_count"] == len(entry["members"]) + len(entry["out_of_universe"])
        entries.append(entry)
    return entries


def overlap_report(existing, entries):
    all_lists = existing + entries
    failures = []
    for entry in entries:
        members = set(entry["members"])
        best = max((sum(1 for other in all_lists if other["id"] != entry["id"] and value in other["members"])
                    for value in members), default=0)
        if best < 2:
            failures.append((entry["id"], best))
    assert not failures, failures


def spotcheck_rows(root, entries):
    lines, weak_start, weak_end, cat_start, cat_end, cat_member_line = _line_index()
    weak = {w.get("ID"): w for w in root.find(NS + "Weaknesses").findall(NS + "Weakness")}
    universe = {"CWE-" + wid for wid, weakness in weak.items()
                if weakness.get("Status") != "Deprecated" and weakness.get("Abstraction") != "Pillar"}
    by_id = {entry["id"]: entry for entry in entries}
    cfg = {list_id: (view, cid) for list_id, view, cid, _, _ in NEW_LISTS}
    rows = []
    for list_id, _, _, _, _ in NEW_LISTS:
        view, cid = cfg[list_id]
        members = set(by_id[list_id]["members"])
        if view == "1000":
            for value in spread(sorted(members, key=lambda x: int(x.split("-")[1]))):
                mid = value.split("-")[1]
                path = _tree_path(weak, mid, cid)
                assert path is not None, (list_id, value)
                if not path:
                    evidence = (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[mid]} "
                                f"(Weakness {mid}, tree root of View 1000 member {cid})")
                else:
                    edge = path[0]
                    evidence = (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[mid]} (Weakness {mid}); "
                                f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[edge[0]]} "
                                f"(ChildOf {edge[1]}); chain {' -> '.join([mid] + [p for _, p in path])}; root {cid}")
                rows.append((list_id, "cwe", "member", value, evidence))
            nonmembers = sorted(universe - members, key=lambda x: int(x.split("-")[1]))
            for value in spread(nonmembers):
                mid = value.split("-")[1]
                assert _tree_path(weak, mid, cid) is None, (list_id, value)
                rels = [rel.get("CWE_ID") for rel in weak[mid].findall(f"{NS}Related_Weaknesses/{NS}Related_Weakness")
                        if rel.get("Nature") == "ChildOf" and rel.get("View_ID") == "1000"]
                edges = ", ".join(rels) or "none"
                evidence = (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[mid]} (Weakness {mid}); "
                            f"View 1000 ChildOf parent(s) {edges}; no path to root {cid}")
                rows.append((list_id, "cwe", "nonmember", value, evidence))
            continue

        block = f"{cat_start[cid]}-{cat_end[cid]}"
        for value in spread(sorted(members, key=lambda x: int(x.split("-")[1]))):
            mid = value.split("-")[1]
            path = _cat_path(root, cid, mid)
            assert path is not None, (list_id, value)
            evidence = "; ".join(
                f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{cat_member_line[(parent, child)]} "
                f"(Category {parent} Has_Member {child})"
                for parent, child in path)
            rows.append((list_id, "cwe", "member", value, evidence))
        nonmembers = sorted(universe - members, key=lambda x: int(x.split("-")[1]))
        for value in spread(nonmembers):
            mid = value.split("-")[1]
            assert _cat_path(root, cid, mid) is None, (list_id, value)
            evidence = (f"raw/cwec_latest.xml.zip!cwec_v4.20.xml:{weak_start[mid]} (Weakness {mid}); "
                        f"Category {cid} block lines {block}: no Has_Member path to CWE-{mid}")
            rows.append((list_id, "cwe", "nonmember", value, evidence))
    counts = Counter((row[0], row[2]) for row in rows)
    assert len(counts) == 2 * len(entries) and all(value == 5 for value in counts.values())
    return rows


def main():
    root, _ = xml_source()
    weak = {w.get("ID"): w for w in root.find(NS + "Weaknesses").findall(NS + "Weakness")}
    universe = {"CWE-" + wid for wid, weakness in weak.items()
                if weakness.get("Status") != "Deprecated" and weakness.get("Abstraction") != "Pillar"}
    assert len(universe) == 934

    base_yaml = (RAW / "base_add_ws4_cwe.yaml").read_text(encoding="utf-8")
    existing = yaml.safe_load(base_yaml)
    entries = generate_lists(root, universe)
    assert len(entries) >= 12 and sum(len(entry["members"]) >= 8 for entry in entries) >= 8
    assert not ({entry["id"] for entry in entries} & {entry["id"] for entry in existing})
    overlap_report(existing, entries)

    new_yaml = yaml.safe_dump(entries, allow_unicode=True, sort_keys=False)
    (ROOT / "lists" / "cwe.yaml").write_text(base_yaml.rstrip("\n") + "\n" + new_yaml, encoding="utf-8")

    base_spot = (RAW / "base_add_ws4_SPOTCHECK.tsv").read_text(encoding="utf-8")
    rows = spotcheck_rows(root, entries)
    with (ROOT / "SPOTCHECK.tsv").open("w", encoding="utf-8", newline="") as handle:
        handle.write(base_spot)
        for row in rows:
            handle.write("\t".join(row) + "\n")

    base_sal = (RAW / "base_add_ws4_salience.tsv").read_text(encoding="utf-8")
    with (ROOT / "salience" / "cwe.tsv").open("w", encoding="utf-8", newline="") as handle:
        handle.write(base_sal)
        for entry, config in zip(entries, NEW_LISTS):
            title = config[4]
            note = "wikipedia article"
            handle.write(f"{entry['id']}\t{title}\texact\t{entry['salience']}\t{note}\n")

    base_titles = (RAW / "base_add_ws4_titles.tsv").read_text(encoding="utf-8")
    with (ROOT / "salience" / "titles.tsv").open("w", encoding="utf-8", newline="") as handle:
        handle.write(base_titles)
        for entry, config in zip(entries, NEW_LISTS):
            handle.write(f"{entry['id']}\t{config[4]}\twikipedia article\n")

    per_view = Counter(config[1] for config in NEW_LISTS)
    print("appended", len(entries), "lists", dict(sorted(per_view.items())), "spotcheck", len(rows))


if __name__ == "__main__":
    main()
