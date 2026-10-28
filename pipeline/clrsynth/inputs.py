"""Load a dataset's frozen inputs: universes, lists, scenario, chain configs, dataset.py."""
import csv
import hashlib
import importlib.util
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

import yaml


class InputError(Exception):
    pass


def rng_for(seed, *names):
    digest = hashlib.sha256("/".join([str(seed), *map(str, names)]).encode()).hexdigest()
    return random.Random(int(digest, 16))


def seeded_order(items, seed, *names):
    """Deterministic pseudo-random order that does not depend on input order."""
    def key(item):
        return hashlib.sha256("/".join([str(seed), *map(str, names), str(item)]).encode()).hexdigest()
    return sorted(items, key=key)


@dataclass
class Universe:
    name: str
    values: list
    entity: dict
    attrs: dict            # value -> {attr: frozenset(values)}
    attr_names: list
    multi: set             # values whose entity names several entities
    desc: dict = field(default_factory=dict)   # value -> one-sentence description (universes/<U>.desc.tsv)

    def single_valued_attrs(self):
        return [a for a in self.attr_names
                if all(len(self.attrs[v].get(a, ())) <= 1 for v in self.values)]


def load_universe(path):
    path = Path(path)
    lines = [line for line in path.read_text(encoding="utf-8").splitlines()
             if line.strip() and not line.startswith("#")]
    reader = csv.DictReader(lines, delimiter="\t")
    if not reader.fieldnames or "value" not in reader.fieldnames or "entity" not in reader.fieldnames:
        raise InputError(f"{path}: needs columns value and entity")
    attr_names = [c[5:] for c in reader.fieldnames if c.startswith("attr:")]
    values, entity, attrs, multi = [], {}, {}, set()
    for row in reader:
        value = row["value"]
        if value in entity:
            raise InputError(f"{path}: duplicate value {value!r}")
        values.append(value)
        entity[value] = row["entity"] or ""
        attrs[value] = {}
        for a in attr_names:
            raw = (row.get("attr:" + a) or "").strip()
            if raw:
                attrs[value][a] = frozenset(p.strip() for p in raw.split("|") if p.strip())
        if " / " in entity[value]:
            multi.add(value)
    desc = {}
    dpath = path.with_name(path.stem + ".desc.tsv")
    if dpath.exists():
        dlines = [line for line in dpath.read_text(encoding="utf-8").splitlines()
                  if line.strip() and not line.startswith("#")]
        for row in csv.DictReader(dlines, delimiter="\t"):
            desc[str(row["value"])] = (row.get("description") or "").strip()
    return Universe(path.stem, values, entity, attrs, attr_names, multi, desc)


@dataclass
class NamedList:
    id: str
    name: str
    members: frozenset
    disputed: frozenset
    changes: list
    official_count: object
    out_of_universe: list
    salience: float
    source: str
    synonyms: list = field(default_factory=list)


def load_lists(path):
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or []
    out = []
    for item in raw:
        out.append(NamedList(
            id=str(item["id"]), name=str(item.get("name", item["id"])),
            members=frozenset(str(m) for m in item.get("members") or []),
            disputed=frozenset(str(m) for m in item.get("disputed") or []),
            changes=list(item.get("changes") or []),
            official_count=item.get("official_count"),
            out_of_universe=list(item.get("out_of_universe") or []),
            salience=float(item.get("salience") or 0),
            source=str(item.get("source", "")),
            synonyms=[str(s) for s in item.get("synonyms") or []]))
    return out


@dataclass
class Template:
    id: str
    field: str
    effect: str
    plausible: list
    rule: str
    source: str


class Dataset:
    def __init__(self, inputs_root, name):
        self.name = name
        self.root = Path(inputs_root).resolve() / name
        if not self.root.is_dir():
            raise InputError(f"{self.root}: dataset directory not found")
        scen_path = self.root / "scenario.yaml"
        if not scen_path.exists():
            raise InputError(f"{scen_path}: missing")
        self.scenario = yaml.safe_load(scen_path.read_text(encoding="utf-8")) or {}
        self.universes = {}
        for p in sorted((self.root / "universes").glob("*.tsv")):
            if p.name.endswith(".desc.tsv"):
                continue
            self.universes[p.stem] = load_universe(p)
        self.lists = {}
        for p in sorted((self.root / "lists").glob("*.yaml")):
            self.lists[p.stem] = load_lists(p)
        self.fields = self._fields()
        self.templates = self._templates()
        self._module = None

    def _fields(self):
        raw = self.scenario.get("fields") or {}
        out = {}
        if isinstance(raw, dict):
            for name, spec in raw.items():
                out[str(name)] = dict(spec or {})
        else:
            for spec in raw:
                out[str(spec["field"])] = dict(spec)
        return out

    def _templates(self):
        out = []
        for t in self.scenario.get("rule_templates") or []:
            out.append(Template(id=str(t["id"]), field=str(t.get("field", "")),
                                effect=str(t.get("effect", "exclude_record")),
                                plausible=[str(x) for x in t.get("plausible") or []],
                                rule=str(t.get("rule", "")), source=str(t.get("source", ""))))
        return out

    def universe_of(self, field_name):
        spec = self.fields.get(field_name)
        if not spec or "universe" not in spec:
            raise InputError(f"scenario.yaml: field {field_name} has no universe")
        return str(spec["universe"])

    def value_form(self, field_name):
        form = str(self.fields.get(field_name, {}).get("value_form", "self_describing"))
        return "code" if form == "code" else "self_describing"

    def business(self):
        for key in ("business_process", "business", "title"):
            if self.scenario.get(key):
                return str(self.scenario[key]).strip()
        return ""

    def label_nouns(self):
        nouns = self.scenario.get("label_nouns")
        if nouns:
            return [str(n) for n in nouns]
        return ["tenant class", "review tag", "routing bucket", "ledger code", "audit lane",
                "handling class", "queue tag"]

    def chain_paths(self):
        return sorted((self.root / "chains").glob("*.yaml"))

    @property
    def module(self):
        if self._module is None:
            path = self.root / "dataset.py"
            if not path.exists():
                raise InputError(f"{path}: missing")
            name = f"clrsynth_dataset_{self.name}_{hashlib.sha1(str(path).encode()).hexdigest()[:8]}"
            spec = importlib.util.spec_from_file_location(name, path)
            mod = importlib.util.module_from_spec(spec)
            sys.modules[name] = mod
            spec.loader.exec_module(mod)
            self._module = mod
        return self._module


def load_chain(path):
    path = Path(path).resolve()
    cfg = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    for key in ("id", "dataset", "seed", "fields"):
        if key not in cfg:
            raise InputError(f"{path}: missing key {key}")
    cfg.setdefault("slots", 5)
    cfg.setdefault("probe", {})
    cfg["probe"].setdefault("criterion", "soft")
    cfg["_path"] = str(path)
    # inputs/<D>/chains/<chain>.yaml -> inputs root is three levels up
    cfg["_inputs_root"] = str(path.parent.parent.parent)
    return cfg


def period_bounds(cfg):
    period = cfg.get("period") or {}
    start = str(period.get("start", "0000"))
    snapshot = str(cfg.get("snapshot", "9999-12-31"))
    return start, snapshot
