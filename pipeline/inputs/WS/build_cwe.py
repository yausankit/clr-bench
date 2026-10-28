#!/usr/bin/env python3
"""Build universes/cwe.tsv and lists/cwe.yaml from raw/cwec_latest.xml.zip (MITRE CWE 4.20)."""
import csv, io, json, sys, zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "raw" / "cwec_latest.xml.zip"
NS = "{http://cwe.mitre.org/cwe-7}"

TREES = [  # CWE-1000 Research Concepts top-level entries (view members), with the CWE name
    ("cwe1000_284", "284", "Improper Access Control"),
    ("cwe1000_435", "435", "Improper Interaction Between Multiple Correctly-Behaving Entities"),
    ("cwe1000_664", "664", "Improper Control of a Resource Through its Lifetime"),
    ("cwe1000_682", "682", "Incorrect Calculation"),
    ("cwe1000_691", "691", "Insufficient Control Flow Management"),
    ("cwe1000_693", "693", "Protection Mechanism Failure"),
    ("cwe1000_697", "697", "Insufficient Comparison"),
    ("cwe1000_703", "703", "Improper Check or Handling of Exceptional Conditions"),
    ("cwe1000_707", "707", "Improper Neutralization"),
    ("cwe1000_710", "710", "Improper Adherence to Coding Standards"),
]

CATEGORIES = [  # id, list id, name, source family
    ("1027", "owasp2017_a01", "OWASP Top Ten 2017 Category A1 - Injection", "owasp2017"),
    ("1028", "owasp2017_a02", "OWASP Top Ten 2017 Category A2 - Broken Authentication", "owasp2017"),
    ("1029", "owasp2017_a03", "OWASP Top Ten 2017 Category A3 - Sensitive Data Exposure", "owasp2017"),
    ("1031", "owasp2017_a05", "OWASP Top Ten 2017 Category A5 - Broken Access Control", "owasp2017"),
    ("1345", "owasp2021_a01", "OWASP Top Ten 2021 Category A01:2021 - Broken Access Control", "owasp2021"),
    ("1346", "owasp2021_a02", "OWASP Top Ten 2021 Category A02:2021 - Cryptographic Failures", "owasp2021"),
    ("1347", "owasp2021_a03", "OWASP Top Ten 2021 Category A03:2021 - Injection", "owasp2021"),
    ("1348", "owasp2021_a04", "OWASP Top Ten 2021 Category A04:2021 - Insecure Design", "owasp2021"),
    ("1349", "owasp2021_a05", "OWASP Top Ten 2021 Category A05:2021 - Security Misconfiguration", "owasp2021"),
    ("1353", "owasp2021_a07", "OWASP Top Ten 2021 Category A07:2021 - Identification and Authentication Failures", "owasp2021"),
    ("1354", "owasp2021_a08", "OWASP Top Ten 2021 Category A08:2021 - Software and Data Integrity Failures", "owasp2021"),
    ("1436", "owasp2025_a01", "OWASP Top Ten 2025 Category A01:2025 - Broken Access Control", "owasp2025"),
    ("1437", "owasp2025_a02", "OWASP Top Ten 2025 Category A02:2025 - Security Misconfiguration", "owasp2025"),
    ("1438", "owasp2025_a03", "OWASP Top Ten 2025 Category A03:2025 - Software Supply Chain Failures", "owasp2025"),
    ("1439", "owasp2025_a04", "OWASP Top Ten 2025 Category A04:2025 - Cryptographic Failures", "owasp2025"),
    ("1440", "owasp2025_a05", "OWASP Top Ten 2025 Category A05:2025 - Injection", "owasp2025"),
    ("1441", "owasp2025_a06", "OWASP Top Ten 2025 Category A06:2025 - Insecure Design", "owasp2025"),
    ("1442", "owasp2025_a07", "OWASP Top Ten 2025 Category A07:2025 - Authentication Failures", "owasp2025"),
    ("1443", "owasp2025_a08", "OWASP Top Ten 2025 Category A08:2025 - Software or Data Integrity Failures", "owasp2025"),
    ("1444", "owasp2025_a09", "OWASP Top Ten 2025 Category A09:2025 - Logging & Alerting Failures", "owasp2025"),
    ("1445", "owasp2025_a10", "OWASP Top Ten 2025 Category A10:2025 - Mishandling of Exceptional Conditions", "owasp2025"),
    ("1006", "bad_coding_practices", "Bad Coding Practices", "cwe699"),
    ("1009", "audit", "Audit", "cwe699"),
    ("1010", "authenticate_actors", "Authenticate Actors", "cwe699"),
    ("1011", "authorize_actors", "Authorize Actors", "cwe699"),
    ("1012", "cross_cutting", "Cross Cutting", "cwe699"),
    ("1013", "encrypt_data", "Encrypt Data", "cwe699"),
    ("1014", "identify_actors", "Identify Actors", "cwe699"),
    ("1015", "limit_access", "Limit Access", "cwe699"),
    ("1016", "limit_exposure", "Limit Exposure", "cwe699"),
    ("1018", "manage_user_sessions", "Manage User Sessions", "cwe699"),
    ("1019", "validate_inputs", "Validate Inputs", "cwe699"),
    ("1020", "verify_message_integrity", "Verify Message Integrity", "cwe699"),
    ("1306", "cisq_reliability", "CISQ Quality Measures - Reliability", "cisq"),
    ("1307", "cisq_maintainability", "CISQ Quality Measures - Maintainability", "cisq"),
    ("1308", "cisq_security", "CISQ Quality Measures - Security", "cisq"),
    ("1309", "cisq_efficiency", "CISQ Quality Measures - Efficiency", "cisq"),
    ("890", "sfp_memory_access", "SFP Primary Cluster: Memory Access", "sfp"),
    ("895", "sfp_information_leak", "SFP Primary Cluster: Information Leak", "sfp"),
    ("896", "sfp_tainted_input", "SFP Primary Cluster: Tainted Input", "sfp"),
    ("898", "sfp_authentication", "SFP Primary Cluster: Authentication", "sfp"),
    ("901", "sfp_privilege", "SFP Primary Cluster: Privilege", "sfp"),
    ("904", "sfp_malware", "SFP Primary Cluster: Malware", "sfp"),
    ("905", "sfp_predictability", "SFP Primary Cluster: Predictability", "sfp"),
    ("963", "sfp_exposed_data", "SFP Secondary Cluster: Exposed Data", "sfp"),
    ("981", "sfp_path_traversal", "SFP Secondary Cluster: Path Traversal", "sfp"),
    ("990", "sfp_tainted_input_command", "SFP Secondary Cluster: Tainted Input to Command", "sfp"),
]

FAMILY_NAMES = {
    "owasp2017": "OWASP Top 10 2017",
    "owasp2021": "OWASP Top 10 2021",
    "owasp2025": "OWASP Top 10 2025",
    "cwe699": "CWE-699 Software Development view category",
    "cisq": "CISQ automated quality measure",
    "sfp": "Seven Pernicious Kingdoms cluster",
}


def load():
    z = zipfile.ZipFile(RAW)
    name = [n for n in z.namelist() if n.endswith(".xml") and "cwec" in n][0]
    return ET.parse(io.BytesIO(z.read(name))).getroot()



def _salience():
    import csv as _csv
    path = ROOT / "salience" / "cwe.tsv"
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as fh:
        return {r["concept_id"]: int(float(r["pageviews_12m"] or 0))
                for r in _csv.DictReader(fh, delimiter="\t")}

def main():
    r = load()
    W = r.find(NS + "Weaknesses")
    C = r.find(NS + "Categories")
    views = {v.get("ID"): v for v in r.find(NS + "Views").findall(NS + "View")}
    weak = {w.get("ID"): w for w in W.findall(NS + "Weakness")}
    cats = {c.get("ID"): c for c in C.findall(NS + "Category")}

    universe = {}
    for wid, w in weak.items():
        if w.get("Status") == "Deprecated" or w.get("Abstraction") == "Pillar":
            continue
        universe[wid] = w

    # ChildOf(1000) edges
    child = {}
    for wid, w in weak.items():
        rel = w.find(NS + "Related_Weaknesses")
        if rel is None:
            continue
        for rw in rel.findall(NS + "Related_Weakness"):
            if rw.get("Nature") == "ChildOf":
                child.setdefault(rw.get("View_ID"), {}).setdefault(rw.get("CWE_ID"), []).append(wid)

    def descendants(view, root):
        seen, stack = set(), [root]
        while stack:
            x = stack.pop()
            for y in child.get(view, {}).get(x, []):
                if y not in seen:
                    seen.add(y)
                    stack.append(y)
        return seen

    def category_members(cid, seen=None):
        seen = set() if seen is None else seen
        c = cats.get(cid)
        if c is None:
            return seen
        rel = c.find(NS + "Relationships")
        if rel is None:
            return seen
        for m in rel.findall(NS + "Has_Member"):
            mid = m.get("CWE_ID")
            if mid in cats:
                if mid not in seen:
                    seen.add(mid)
                    category_members(mid, seen)
            else:
                seen.add(mid)
        return seen

    def cwe_name(cid):
        if cid in weak:
            return weak[cid].get("Name")
        if cid in cats:
            return cats[cid].get("Name")
        return "CWE-%s" % cid

    lists = []
    for lid, root, name in TREES:
        members = {root} | descendants("1000", root)
        members = {m for m in members if m in weak}
        lists.append(dict(id=lid, name="CWE-1000 Research Concepts subtree: %s (CWE-%s)" % (name, root),
                          synonyms=[name, "CWE-%s subtree" % root],
                          source="https://cwe.mitre.org/data/definitions/%s.html" % root,
                          members=members, disputed=set()))
    for cid, lid, name, fam in CATEGORIES:
        members = {m for m in category_members(cid) if m in weak}
        lists.append(dict(id=lid, name=name, synonyms=[], fam=fam,
                          source="https://cwe.mitre.org/data/definitions/%s.html" % cid,
                          members=members, disputed=set()))

    out = []
    for lst in lists:
        all_members = sorted(lst["members"], key=int)
        in_u = [m for m in all_members if m in universe]
        out_u = ["CWE-%s" % m for m in all_members if m not in universe]
        if len(in_u) < 5:
            continue
        item = {
            "id": lst["id"],
            "name": lst["name"],
            "synonyms": lst.get("synonyms") or [],
            "members": ["CWE-%s" % m for m in in_u],
            "disputed": sorted("CWE-%s" % m for m in lst["disputed"]),
            "changes": [],
            "out_of_universe": out_u,
            "official_count": len(all_members),
            "source": lst["source"],
        }
        if lst.get("fam"):
            item["synonyms"] = [FAMILY_NAMES[lst["fam"]]]
        out.append(item)

    # universe tsv
    (ROOT / "universes").mkdir(exist_ok=True)
    rows = ["value\tentity\tattr:abstraction"]
    for wid in sorted(universe, key=int):
        w = universe[wid]
        nm = w.get("Name", "").replace("\t", " ").replace("\n", " ")
        rows.append("CWE-%s\t%s\t%s" % (wid, nm, w.get("Abstraction")))
    (ROOT / "universes" / "cwe.tsv").write_text("\n".join(rows) + "\n", encoding="utf-8")

    (ROOT / "lists").mkdir(exist_ok=True)
    sal = _salience()
    for x in out:
        x["salience"] = sal.get(x["id"], 0)
    (ROOT / "lists" / "cwe.yaml").write_text(
        yaml.safe_dump(out, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print("universe", len(universe), "lists", len(out), [x["id"] for x in out])


if __name__ == "__main__":
    main()
