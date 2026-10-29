"""clrsynth screen <chain>: the Known probe, run on every candidate list before any chain is built.

The model sees the list's pool values with their descriptions, one round of feedback (the example A and a revealed
member are in the class, the practice non-member n_p is not), and the lesson, and is asked to name the grouping and
mark which values belong to it. A list passes when the soft score is at least 0.8 on average over the three rotations
of the revealed member and at least 0.6 in each, which requires both identifying the grouping and knowing its members.
Failing lists are written to out/<dataset>/SCREEN.json and skipped by make-chain in every chain of the domain."""
import json
from pathlib import Path

from .inputs import Dataset, load_chain, seeded_order
from .candidates import FieldContext, candidates_for_slot
from .chain import HINT, HINT_TITLE, split_field, singular
from .probe import Endpoint, parse_json_answer, soft_score


def screen_prompt(ds, cand, version):
    u = ds.universes[cand.universe]
    obj, fname = split_field(cand.field)
    one = singular(obj)
    code = ds.value_form(cand.field) == "code"
    vals = seeded_order(cand.pool(), 0, "screen", cand.C)
    lines = [f"- {v} — {u.entity[v]}" if code else f"- {v}" for v in vals]
    q = (lambda v: v if v.lstrip("-").isdigit() else f"'{v}'")
    return (f"A data team labels some {obj} with a class name that does not say what the class is.\n"
            f"Values of the field {fname} that occur in the data:\n" + "\n".join(lines) + "\n\n"
            f"Known: a {one} whose {fname} is {q(cand.A)} is in the class. Feedback: a {one} whose {fname} is "
            f"{q(cand.P_M[version])} is treated the same way, and a {one} whose {fname} is {q(cand.N_p)} is not.\n\n"
            f"{HINT_TITLE}\n{HINT}\n\n"
            "Question: write the category you think the class stands for, and list the values above that belong to "
            'it. Answer only with JSON of the form {"category": "...", "values": [...]}.')


def screen(chain_path, out_root):
    cfg = load_chain(chain_path)
    ds = Dataset(cfg["_inputs_root"], cfg["dataset"])
    out = Path(out_root) / "out" / cfg["dataset"]
    path = out / "SCREEN.json"
    result = json.loads(path.read_text()) if path.exists() else {}
    ep = Endpoint()
    items = []
    for spec in cfg["fields"]:
        fc = FieldContext(ds, cfg, spec["field"])
        cands, _ = candidates_for_slot(fc, set(), 1, limit=10 ** 6)
        for c in cands:
            if c.C in result:
                continue
            for v in range(3):
                items.append((c, v, screen_prompt(ds, c, v)))
    replies = ep.run_all([p for _, _, p in items])
    fresh = set()
    for (c, v, prompt), rep in zip(items, replies):
        obj = parse_json_answer(rep) or {}
        got = {str(x).strip().strip("'\"") for x in (obj.get("values") or [])}
        r = result.setdefault(c.C, {"field": c.field, "name": c.C_name, "versions": {}})
        fresh.add(c.C)
        r["versions"][str(v)] = {"soft": round(soft_score(c, v, got), 4), "category": obj.get("category")}
    for cid in fresh:
        r = result[cid]
        scores = [x["soft"] for x in r["versions"].values()]
        r["mean"] = round(sum(scores) / len(scores), 4)
        r["pass"] = r["mean"] >= 0.8 and min(scores) >= 0.6
    out.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=1, ensure_ascii=False, sort_keys=True))
    by_field = {}
    for cid, r in sorted(result.items()):
        by_field.setdefault(r["field"], [0, 0])
        by_field[r["field"]][0] += r["pass"]
        by_field[r["field"]][1] += 1
    for f, (p, n) in sorted(by_field.items()):
        print(f"screen {cfg['dataset']} {f}: {p}/{n} lists pass")
    return result
