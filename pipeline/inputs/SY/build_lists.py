"""Build lists/<universe>.yaml from public classification sources kept in raw/.

  raw/mesh/desc2025.xml, raw/mesh/mtrees2025.bin   NLM MeSH 2025
  raw/atc/                                        WHOCC ATC/DDD index pages
  raw/snomed/expand_<concept>.json                SNOMED CT is-a expansions (tx.fhir.org)

A list is a closed set of the source's members.  Its member values are the universe values whose
name is identical to the source member's name (MeSH, ATC) or whose code is a descendant (SNOMED);
the remaining source members go to out_of_universe, so that
official_count == len(members) + len(disputed) + len(out_of_universe).
"""
import csv
import html as H
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
TREE_NAMES = {}


def norm(s):
    s = H.unescape(str(s)).lower().replace("-", " ")
    s = re.sub(r"\([^)]*\)", "", s)
    s = re.sub(r"[^a-z0-9 /]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def slug(s):
    return re.sub(r"[^a-z0-9]+", "_", norm(s)).strip("_")


def universe(name):
    rows = list(csv.DictReader((ROOT / "universes" / f"{name}.tsv").open(), delimiter="\t"))
    return [r["value"] for r in rows], {r["value"]: r["entity"] for r in rows}


def prefixes(t):
    p = t.split(".")
    return [".".join(p[:i]) for i in range(1, len(p) + 1)]


def mesh_data():
    byterm, desc, node_count = {}, {}, {}
    for line in (ROOT / "raw" / "mesh" / "mtrees2025.bin").read_text(encoding="utf-8", errors="replace").splitlines():
        if ";" not in line:
            continue
        name, tree = line.rsplit(";", 1)
        TREE_NAMES[tree.strip()] = name.strip()
    for _, el in ET.iterparse(ROOT / "raw" / "mesh" / "desc2025.xml", events=("end",)):
        if el.tag != "DescriptorRecord":
            continue
        ui = el.findtext("DescriptorUI")
        name = (el.findtext("DescriptorName/String") or "").strip()
        trees = [t.text for t in el.findall("TreeNumberList/TreeNumber")]
        acts = [a.text for a in el.findall(
            "PharmacologicalActionList/PharmacologicalAction/DescriptorReferredTo/DescriptorName/String")]
        terms = [name] + [t.text for t in el.findall("ConceptList/Concept/TermList/Term/String")]
        desc[ui] = {"ui": ui, "name": name, "trees": trees, "acts": acts}
        for t in trees:
            for p in prefixes(t):
                node_count[p] = node_count.get(p, 0) + 1
        for t in terms:
            k = norm(t)
            if k and k not in byterm:
                byterm[k] = ui
        el.clear()
    return byterm, desc, node_count


def crosswalk(universe_name):
    """SNOMED code -> MeSH descriptor name, where MeSH has no entry under the data name."""
    path = ROOT / "raw" / "crosswalk" / f"{universe_name}.tsv"
    out = {}
    if path.exists():
        for row in csv.DictReader(path.open(), delimiter="\t"):
            out[row["code"]] = row["mesh_descriptor"]
    return out


def mesh_map(vals, entity, byterm, desc, root, universe_name=None):
    out, used = {}, set()
    cw = crosswalk(universe_name) if universe_name else {}
    missing = sorted({d for d in cw.values() if norm(d) not in byterm})
    if missing:
        raise SystemExit(f"crosswalk: unknown MeSH descriptor(s): {missing}")
    for v in sorted(vals):
        ui = byterm.get(norm(entity[v])) or byterm.get(norm(cw.get(v, "")))
        if ui is None or ui in used or not any(t.startswith(root) for t in desc[ui]["trees"]):
            continue
        out[v] = ui
        used.add(ui)
    return out


def mesh_tree_lists(vals, entity, byterm, desc, node_count, root, code_prefix, max_desc=4000, uname=None):
    mapping = mesh_map(vals, entity, byterm, desc, root, uname)
    byui = {ui: v for v, ui in mapping.items()}
    nodes = {}
    for v, ui in mapping.items():
        for t in desc[ui]["trees"]:
            if t.startswith(root):
                for p in prefixes(t):
                    nodes.setdefault(p, set()).add(ui)
    out = []
    for node in sorted(nodes):
        uis = nodes[node]
        members = sorted(byui[u] for u in uis if u in byui)
        if len(members) < 5 or node_count.get(node, 0) > max_desc:
            continue
        oou = sorted(desc[u]["name"] for u in desc if node in prefixes_of(desc[u]) and u not in byui)
        out.append({"id": f"mesh_{code_prefix}_{node.lower().replace('.', '_')}_{slug(TREE_NAMES.get(node, node))}"[:90],
                    "name": TREE_NAMES.get(node, node), "members": members, "official_count": len(members) + len(oou),
                    "out_of_universe": oou,
                    "source": f"https://meshb.nlm.nih.gov/treeNumber/{node}",
                    "synonyms": [], "node": node})
    return out


def prefixes_of(d):
    out = set()
    for t in d["trees"]:
        out.update(prefixes(t))
    return out


def mesh_action_lists(vals, entity, byterm, desc, root, uname=None):
    mapping = mesh_map(vals, entity, byterm, desc, root, uname)
    byui = {ui: v for v, ui in mapping.items()}
    groups = {}
    for ui, d in desc.items():
        for a in d["acts"]:
            groups.setdefault(a, set()).add(ui)
    out = []
    for action in sorted(groups):
        uis = groups[action]
        members = sorted(byui[u] for u in uis if u in byui)
        if len(members) < 5:
            continue
        oou = sorted(desc[u]["name"] for u in uis if u not in byui)
        out.append({"id": f"mesh_pa_{slug(action)}"[:90], "name": action, "members": members,
                    "official_count": len(members) + len(oou), "out_of_universe": oou,
                    "source": "MeSH 2025 PharmacologicalAction of descriptors (https://meshb.nlm.nih.gov/)",
                    "synonyms": []})
    return out


ATC_ROW = re.compile(r"<td>([A-Z]\d{2}[A-Z]{0,2}\d{0,2})(?:&nbsp;|\s)*</td><td><a [^>]*>([^<]+)</a>", re.I)


def atc_rows(path):
    return [(m.group(1), H.unescape(m.group(2)).strip())
            for m in ATC_ROW.finditer(path.read_text(encoding="utf-8", errors="replace"))]


def atc_class_name(code):
    pat = re.compile(r'href="\./\?code=' + code + r'&showdescription=no">([^<]+)</a>')
    path = ROOT / "raw" / "atc" / f"class_{code}.html"
    if path.exists():
        m = pat.search(path.read_text(encoding="utf-8", errors="replace"))
        if m:
            return H.unescape(m.group(1)).strip()
    for p in sorted((ROOT / "raw" / "atc").glob("class_*.html")):
        m = pat.search(p.read_text(encoding="utf-8", errors="replace"))
        if m:
            return H.unescape(m.group(1)).strip()
    return code


def atc_lists(vals, entity):
    byname = {norm(v): v for v in vals if " / " not in v}
    level4 = {}
    raw = ROOT / "raw" / "atc"
    for p in sorted(raw.glob("class_*.html")):
        code = p.stem.split("_")[1]
        if len(code) == 5:
            level4[code] = [(c, n) for c, n in atc_rows(p) if len(c) == 7]
    groups = dict(level4)
    for code, subs in level4.items():
        groups.setdefault(code[:4], []).extend(subs)
    for code, subs in level4.items():
        groups.setdefault(code[:3], []).extend(subs)
    out = []
    for code in sorted(groups):
        if len(code) > 5:
            continue
        subs = groups[code]
        names = [n for _, n in subs]
        members = sorted({byname[norm(n)] for n in names if norm(n) in byname})
        if len(members) < 5:
            continue
        oou = sorted({n for n in names if norm(n) not in byname})
        out.append({"id": f"atc_{code.lower()}", "name": atc_class_name(code), "members": members,
                    "official_count": len(members) + len(oou), "out_of_universe": oou,
                    "source": f"https://atcddd.fhi.no/atc_ddd_index/?code={code}&showdescription=no",
                    "synonyms": []})
    return out


def snomed_lists(universe_name, values):
    names = {}
    np = ROOT / "raw" / "snomed" / "names.json"
    if np.exists():
        names = json.loads(np.read_text())
    vals = set(values)
    out = []
    for p in sorted((ROOT / "raw" / "snomed").glob("expand_*.json")):
        code = p.stem.split("_", 1)[1]
        d = json.loads(p.read_text())
        exp = d.get("expansion", {})
        contains = [x["code"] for x in exp.get("contains", [])]
        total = exp.get("total")
        if total is None or total != len(contains):
            raise SystemExit(f"{p}: expansion is truncated ({total} vs {len(contains)})")
        members = sorted(set(contains) & vals)
        if len(members) < 5:
            continue
        oou = sorted(set(contains) - vals)
        disp = next((x.get("display") for x in exp.get("contains", []) if x["code"] == code), None)
        out.append({"id": f"snomed_{code}", "name": names.get(code, disp or code), "members": members,
                    "official_count": len(members) + len(oou), "out_of_universe": oou,
                    "source": f"SNOMED CT International Edition is-a descendants of {code} "
                              f"(tx.fhir.org/r4 ValueSet/$expand)", "synonyms": [],
                    "universe": universe_name})
    return out


def salience_values(universe_name):
    """concept_id -> pageviews_12m, when build_salience.py has already produced the table."""
    path = ROOT / "salience" / f"{universe_name}.tsv"
    out = {}
    if path.exists():
        for row in csv.DictReader(path.open(encoding="utf-8"), delimiter="\t"):
            try:
                out[row["concept_id"]] = int(float(row.get("pageviews_12m") or 0))
            except ValueError:
                out[row["concept_id"]] = 0
    return out


def write(universe_name, lists):
    seen, seen_sets, rows = set(), {}, []
    salience = salience_values(universe_name)
    for lst in sorted(lists, key=lambda x: x["id"]):
        key = frozenset(lst["members"])
        if lst["id"] in seen or key in seen_sets:
            continue
        seen.add(lst["id"])
        seen_sets[key] = lst["id"]
        lst.pop("universe", None)
        lst.pop("node", None)
        rows.append({"id": lst["id"], "name": lst["name"], "synonyms": lst["synonyms"],
                     "members": lst["members"], "disputed": [], "changes": [],
                     "official_count": lst["official_count"],
                     "out_of_universe": lst["out_of_universe"],
                     "source": lst["source"], "salience": salience.get(lst["id"], 0)})
    (ROOT / "lists" / f"{universe_name}.yaml").write_text(
        yaml.safe_dump(rows, allow_unicode=True, sort_keys=False), encoding="utf-8")
    print(universe_name, len(rows))


def main():
    byterm, desc, node_count = mesh_data()
    med_vals, med_ent = universe("medicine")
    con_vals, con_ent = universe("condition")
    pro_vals, pro_ent = universe("procedure")
    write("medicine", atc_lists(med_vals, med_ent)
          + mesh_action_lists(med_vals, med_ent, byterm, desc, "D", "medicine")
          + mesh_tree_lists(med_vals, med_ent, byterm, desc, node_count, "D", "d", max_desc=2000, uname="medicine"))
    write("condition", mesh_tree_lists(con_vals, con_ent, byterm, desc, node_count, "C", "c", uname="condition")
          + snomed_lists("condition", con_vals))
    write("procedure", mesh_tree_lists(pro_vals, pro_ent, byterm, desc, node_count, "E", "e", uname="procedure")
          + snomed_lists("procedure", pro_vals))


if __name__ == "__main__":
    main()
