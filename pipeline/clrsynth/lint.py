"""clrsynth lint <dataset>: check a dataset's inputs against the guide (CLRSYNTH_ADD_DATASET)."""
import json
import re
ROMAN = re.compile(r"[IVXLC]+")   # Roman numerals in list names are not acronyms
from pathlib import Path

import yaml

from .inputs import Dataset, InputError, load_chain
from .candidates import attribute_class_lists, allocate_slots

FORMATS = ("json", "text", "files")
MIN_ENTITIES = 30
MIN_POSITIONS = 3
MAX_EXAMPLE_CHARS = 50000


def lint_dataset(ds):
    errors = []
    notes = []
    e = errors.append
    # universes
    for name, u in ds.universes.items():
        if not u.attr_names:
            e(f"universes/{name}.tsv: no attr:<name> column (at least one natural attribute is required)")
        for v in u.values:
            if not u.entity[v].strip():
                e(f"universes/{name}.tsv: value {v!r} has an empty entity")
                break
    # scenario fields
    if not ds.fields:
        e("scenario.yaml: no fields")
    for f, spec in ds.fields.items():
        uname = spec.get("universe")
        if uname not in ds.universes:
            e(f"scenario.yaml: field {f}: universe {uname!r} has no universes/{uname}.tsv")
    # lists
    for uname, lists in ds.lists.items():
        if uname not in ds.universes:
            e(f"lists/{uname}.yaml: no universes/{uname}.tsv")
            continue
        u = ds.universes[uname]
        values = set(u.values)
        raw = yaml.safe_load((ds.root / "lists" / f"{uname}.yaml").read_text()) or []
        ids = [str(r.get("id")) for r in raw]
        for dup in sorted({i for i in ids if ids.count(i) > 1}):
            e(f"lists/{uname}.yaml: duplicate id {dup}")
        for r, lst in zip(raw, lists):
            where = f"lists/{uname}.yaml: {lst.id}"
            missing = sorted(set(lst.members) - values)
            if missing:
                e(f"{where}: members not in universe (move them to out_of_universe): {missing[:5]}")
            if len(lst.members & values) < 5:
                e(f"{where}: fewer than 5 members in the universe")
            if "salience" not in r:
                e(f"{where}: no salience (run clrsynth salience)")
            if isinstance(lst.official_count, int):
                got = len(lst.members) + len(lst.disputed) + len(lst.out_of_universe)
                if got != lst.official_count:
                    e(f"{where}: members+disputed+out_of_universe = {got} != official_count {lst.official_count}")
            else:
                e(f"{where}: official_count must be an integer")
        attr_lists = attribute_class_lists(u, lists)
        for lid, why in sorted(attr_lists.items()):
            notes.append(f"lists/{uname}.yaml: {lid} equals {why} (kept only as a competing list)")
        usable = [l for l in lists if l.id not in attr_lists]
        for f, spec in ds.fields.items():
            if spec.get("universe") == uname and len(usable) < 2:
                e(f"field {f}: fewer than 2 lists that differ from every single-valued attribute class")
    # value descriptions (universes/<U>.desc.tsv): every value, one line, and no word that names a list
    for uname, u in ds.universes.items():
        if not u.desc:
            continue
        missing = [v for v in u.values if not u.desc.get(v)]
        if missing:
            e(f"universes/{uname}.desc.tsv: {len(missing)} values without a description, e.g. {missing[:3]}")
        foreign = [v for v, d in u.desc.items() if d and sum(ch.isascii() for ch in d) < 0.9 * len(d)]
        if foreign:
            e(f"universes/{uname}.desc.tsv: descriptions must be in English like the prompts: {foreign[:3]}")
        long_ = [v for v, d in u.desc.items() if len(d) > 200 or "\n" in d]
        if long_:
            e(f"universes/{uname}.desc.tsv: descriptions longer than 200 characters: {long_[:3]}")
        # a description must not name a list: its full name, a synonym, its id read as words, or an acronym from
        # its name (GCC, EU, OPEC); ordinary descriptive words (database, monitoring) are fine, P0 judges guessing
        names = {}
        for l in ds.lists.get(uname, []):
            phrases = {l.name, l.id.replace("_", " "), *l.synonyms}
            acr = set(re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", " ".join([l.name, *l.synonyms])))
            acr = {a for a in acr if not ROMAN.fullmatch(a)}   # "Schedule II" vs "angiotensin II"
            names[l.id] = ({ph.lower() for ph in phrases if len(ph) >= 4}, acr)
        for v, d in sorted(u.desc.items()):
            low = " " + re.sub(r"[^a-z0-9]+", " ", d.lower()) + " "
            toks = set(re.findall(r"\b[A-Z][A-Z0-9]{1,}\b", d))
            hit = next(((lid, ph) for lid, (phs, acr) in names.items()
                        for ph in sorted(phs) if " " + re.sub(r"[^a-z0-9]+", " ", ph) + " " in low), None) or \
                next(((lid, a) for lid, (phs, acr) in names.items() for a in sorted(acr & toks)), None)
            if hit:
                e(f"universes/{uname}.desc.tsv: {v!r} names list {hit[0]} ({hit[1]!r}); a description must not "
                  f"name a list")
    for f, spec in ds.fields.items():
        if spec.get("universe") in ds.universes and spec.get("universe") not in ds.lists:
            e(f"field {f}: no lists/{spec.get('universe')}.yaml")
    # templates
    by_field = {}
    for t in ds.templates:
        by_field.setdefault(t.field, []).append(t)
        if t.field not in ds.fields:
            e(f"scenario.yaml: template {t.id}: field {t.field} is not a scenario field")
            continue
        uname = ds.fields[t.field].get("universe")
        ids = {l.id for l in ds.lists.get(uname, [])}
        if len(set(t.plausible)) < 2:
            e(f"scenario.yaml: template {t.id}: plausible needs at least 2 distinct lists")
        for lid in t.plausible:
            if lid not in ids:
                e(f"scenario.yaml: template {t.id}: plausible list {lid!r} not in lists/{uname}.yaml")
        if t.effect != "exclude_record":
            e(f"scenario.yaml: template {t.id}: effect must be exclude_record")
    banned = {"tier", "rank", "premium", "top", "core", "legacy", "family", "group", "elite", "priority",
              "vip", "gold", "major", "minor", "high", "low"}
    import re as _re
    data_words = set()
    for f in ds.fields:
        for w in _re.findall(r"[A-Za-z]+", f.replace("_", " ")):
            data_words |= {w.lower(), w.lower().rstrip("s")}
    for noun in ds.scenario.get("label_nouns") or []:
        clash = {w.lower() for w in str(noun).split()} & data_words
        if clash:  # the pipeline skips such nouns itself, so this is a note, not an error
            notes.append(f"scenario.yaml: label noun {noun!r} uses a word from the data's own tables or fields "
                         f"{sorted(clash)}; it will not be used (a reader takes 'in {noun} 39' for a record id)")
        hit = banned & {w.lower() for w in str(noun).split()}
        if hit:
            e(f"scenario.yaml: label noun {noun!r} contains a word that hints at a class or rank: {sorted(hit)}")
    for f in ds.fields:
        if len(by_field.get(f, [])) < 3:
            e(f"scenario.yaml: field {f}: fewer than 3 rule templates")
    # chains
    paths = ds.chain_paths()
    if not paths:
        e("chains/: no chain config")
    seeds = []
    for p in paths:
        try:
            seeds.append(yaml.safe_load(p.read_text()).get("seed"))
        except yaml.YAMLError:
            pass
    if len(set(seeds)) != len(seeds):
        e("chains/: every chain config needs its own seed")
    for p in paths:
        try:
            cfg = load_chain(p)
        except (InputError, yaml.YAMLError) as x:
            e(f"chains/{p.name}: {x}")
            continue
        for spec in cfg["fields"]:
            f = spec.get("field")
            if f not in ds.fields:
                e(f"chains/{p.name}: field {f} not in scenario.yaml")
                continue
            for tid in spec.get("templates") or []:
                t = next((t for t in ds.templates if t.id == tid), None)
                if t is None or t.field != f:
                    e(f"chains/{p.name}: template {tid} is not a template of field {f}")
        if not errors and p != paths[0]:
            try:
                allocate_slots(ds, cfg)
            except ValueError as x:
                e(f"chains/{p.name}: {x}")
            continue
        if not errors:
            try:
                slots = allocate_slots(ds, cfg)
            except ValueError as x:
                e(f"chains/{p.name}: {x}")
                continue
            from .candidates import FieldContext, candidates_for_slot
            n_chains = len(paths)
            for spec in cfg["fields"]:
                f = spec["field"]
                need = sum(1 for s in slots if s["field"] == f)
                # chains of a dataset never share a C, and about half of the candidates fail P1H
                want = 2 * need * n_chains + 1
                cands, reasons = candidates_for_slot(FieldContext(ds, cfg, f), set(), 1, limit=want)
                if len(cands) < want:
                    e(f"chains/{p.name}: field {f} yields {len(cands)} candidate list(s), needs at least {want} "
                      f"(a list is usable as C only if one of its members also belongs to two other lists of the "
                      f"field with different members); rejected: {'; '.join(reasons[:4])}")
    if not errors:
        errors.extend(_lint_module(ds, paths))
    ds.lint_notes = notes
    return errors


def _lint_module(ds, chain_paths):
    errors = []
    e = errors.append
    try:
        mod = ds.module
    except Exception as x:
        return [f"dataset.py: import failed: {type(x).__name__}: {x}"]
    for name in ("ANSWER_FORMAT", "TRAP_FIELDS", "TASK", "base_world", "entities", "slots", "set_value",
                 "total", "render", "reference"):
        if not hasattr(mod, name):
            e(f"dataset.py: missing {name}")
    if errors:
        return errors
    if mod.ANSWER_FORMAT not in FORMATS:
        return [f"dataset.py: ANSWER_FORMAT must be one of {FORMATS}"]
    cfg = load_chain(chain_paths[0])
    fields = [s["field"] for s in cfg["fields"]]
    for f in fields:
        if f not in mod.TRAP_FIELDS:
            e(f"dataset.py: chain field {f} not in TRAP_FIELDS")
    if errors:
        return errors
    seed = cfg["seed"]
    try:
        w1 = mod.base_world(seed, "lint")
        w2 = mod.base_world(seed, "lint")
        if json.dumps(w1, sort_keys=True, default=str) != json.dumps(w2, sort_keys=True, default=str):
            e("dataset.py: base_world is not deterministic for the same (seed, step)")
        ents = list(mod.entities(w1))
        if len(ents) < MIN_ENTITIES:
            e(f"dataset.py: base_world has {len(ents)} entities (at least {MIN_ENTITIES} required)")
        for f in fields:
            pos = list(mod.slots(w1, f))
            per = {}
            for ent, p in pos:
                per.setdefault(ent, []).append(p)
            thin = [x for x in ents if len(per.get(x, [])) < MIN_POSITIONS]
            if thin:
                e(f"dataset.py: field {f}: {len(thin)} entities have fewer than {MIN_POSITIONS} positions")
            u = ds.universes[ds.universe_of(f)]
            marker = u.values[len(u.values) // 2]
            decreased = False
            for ent, p in pos:
                base = mod.total(w1, ent, set())
                less = mod.total(w1, ent, {(f, p)})
                if not isinstance(base, int) or not isinstance(less, int):
                    e(f"dataset.py: total must return int (field {f})")
                    break
                if less < base:
                    decreased = True
                    w3 = mod.base_world(seed, "lint")
                    for ff in fields:
                        for ent2, p2 in mod.slots(w3, ff):
                            other = ds.universes[ds.universe_of(ff)].values[0]
                            mod.set_value(w3, ff, p2, other if other != marker else ds.universes[ds.universe_of(ff)].values[1])
                    mod.set_value(w3, f, p, marker)
                    data = mod.render(w3, sorted(ents))
                    text = data if isinstance(data, str) else json.dumps(data, ensure_ascii=False)
                    if marker not in text:
                        e(f"dataset.py: field {f}: value set with set_value does not appear in render()")
                    if hasattr(mod, "values") and mod.values(data, f).count(marker) != 1:
                        e(f"dataset.py: values(render(...), {f!r}) should contain the value set at one position "
                          f"exactly once; got {mod.values(data, f).count(marker)}")
                    ref_all = mod.reference(data, {})
                    ref_ex = mod.reference(data, {f: {marker}})
                    tot_all = {x: mod.total(w3, x, set()) for x in ents}
                    excl = {(ff, pp) for ff in [f] for _, pp in mod.slots(w3, ff) if pp == p}
                    if {str(k): v for k, v in ref_all.items()} != {str(k): v for k, v in tot_all.items()}:
                        e(f"dataset.py: reference(render(...), {{}}) disagrees with total() (field {f})")
                    elif sum(ref_ex.values()) != sum(mod.total(w3, x, excl) for x in ents):
                        e(f"dataset.py: reference with {f} excluded disagrees with total() (field {f})")
                    break
            if not decreased:
                e(f"dataset.py: field {f}: excluding a position never lowers total()")
        sample = mod.render(w1, sorted(ents)[:7])  # about the size of an L5 example input
        size = len(sample if isinstance(sample, str) else json.dumps(sample, ensure_ascii=False, indent=1))
        if size > MAX_EXAMPLE_CHARS:
            e(f"dataset.py: render() of 7 entities is {size} characters (at most {MAX_EXAMPLE_CHARS}); prompts embed "
              f"an example and practice views carry several instances, so learning methods overflow the model "
              f"context. Give each entity fewer records")
        iso = _isolated_reference(ds, mod, w1, ents)
        if iso:
            e(iso)
    except Exception as x:
        e(f"dataset.py: interface check raised {type(x).__name__}: {x}")
    return errors


def _isolated_reference(ds, mod, world, ents):
    """dataset.py is embedded into the delivered control programs, which run in an empty directory:
    importing it and calling reference() must not need any file next to it."""
    import subprocess, sys, tempfile
    data = mod.render(world, sorted(ents))
    expect = sum(mod.total(world, x, set()) for x in ents)
    src = (ds.root / "dataset.py").read_text() + (
        "\n\nif __name__ == '__main__':\n    import json as _j, sys as _s\n"
        "    _t = open(_s.argv[1], encoding='utf-8').read()\n"
        f"    _d = {'_t' if mod.ANSWER_FORMAT == 'text' else '_j.loads(_t)'}\n"
        "    print(sum(reference(_d, {}).values()))\n")
    with tempfile.TemporaryDirectory(prefix="clrsynth-lint-") as tmp:
        (Path(tmp) / "prog.py").write_text(src)
        (Path(tmp) / "input").write_text(data if isinstance(data, str) else json.dumps(data, ensure_ascii=False))
        r = subprocess.run([sys.executable, "prog.py", "input"], cwd=tmp, capture_output=True, text=True, timeout=120)
    if r.returncode or r.stdout.strip() != str(expect):
        return ("dataset.py: importing it and calling reference() must work in an empty directory (no file reads at "
                f"import time or inside reference); got: {(r.stderr.strip().splitlines() or [r.stdout.strip()])[-1][:200]}")
    return None


def lint_main(name, inputs_root):
    try:
        ds = Dataset(inputs_root, name)
        errors = lint_dataset(ds)
    except InputError as x:
        print(f"error: {x}\nlint FAILED: {name}: 1 error(s)")
        return 1
    for n in getattr(ds, "lint_notes", []):
        print(f"note: {n}")
    for x in errors:
        print(f"error: {x}")
    if errors:
        print(f"lint FAILED: {name}: {len(errors)} error(s)")
        return 1
    print(f"lint OK: {name}")
    return 0
