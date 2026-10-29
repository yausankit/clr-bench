"""clrsynth make-chain: lint -> slots -> candidates -> probes (Hidden, Learnable, Solvable, in the context of the full
chain) -> build -> check -> reproducibility check. Resumable: pinned slots are kept in STATE.json."""
import json
import os
import signal
import sys
import time
from pathlib import Path

from .inputs import Dataset, load_chain
from .candidates import FieldContext, Candidate, allocate_slots, candidates_for_slot, build_candidate
from .chain import Chain, PlacementError, P1_LOW, P1_HIGH
from .probe import Endpoint, ProbeError, parse_json_answer, judge_p0, judge_p1h, judge_p1
from . import lint as lint_mod


class ChainStop(Exception):
    def __init__(self, step, why, need):
        super().__init__(f"{step}: {why}")
        self.step, self.why, self.need = step, why, need


_STOP = {"flag": False, "killed": False}


def _install_signals():
    try:
        if os.getpgid(0) != os.getpid():
            os.setpgid(0, 0)
    except OSError:
        pass

    def handler(signum, frame):
        _STOP["flag"] = True
        if not _STOP["killed"]:
            _STOP["killed"] = True
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            try:
                os.killpg(os.getpgid(0), signal.SIGTERM)
            except OSError:
                pass
            print(f"make-chain: interrupted by signal {signum}; state saved, rerun the same command to resume",
                  file=sys.stderr, flush=True)
            os._exit(130)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


def out_dir(cfg, repo_root):
    return Path(repo_root) / "out" / cfg["dataset"] / cfg["id"]


def log_root(cfg, repo_root):
    return Path(repo_root) / "logs" / cfg["dataset"] / cfg["id"]


def load_state(path):
    return json.loads(path.read_text()) if path.exists() else None


def save_state(path, state):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=1, ensure_ascii=False, sort_keys=True))
    tmp.replace(path)


def sibling_registry(state):
    """What the dataset's other chains tell this one: lists that failed a probe there (P0/P1H/P1 rarely pass
    on a retry) or failed the screen are skipped; concepts pinned there may be used again, built from other
    members ({C: A and P_M used by siblings})."""
    me = Path(state["_path"]).resolve()
    failed, used = set(), {}
    for other in sorted(me.parent.parent.glob("*/STATE.json")):
        if other.resolve() == me:
            continue
        try:
            st = json.loads(other.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        for s in st.get("slots", []):
            if s.get("pinned"):
                p = s["pinned"]
                used.setdefault(p["C"], set()).update([p["A"], *p["P_M"]])
            failed.update(s.get("tried", []))
    screen = me.parent.parent / "SCREEN.json"   # out/<dataset>/SCREEN.json from clrsynth screen
    if screen.exists():
        for c, r in json.loads(screen.read_text()).items():
            if not r.get("pass"):
                failed.add(c)
    return failed - set(used), used


def load_pool(state):
    """out/<dataset>/POOL.json from clrsynth certify, or None."""
    path = Path(state["_path"]).resolve().parent.parent / "POOL.json"
    return json.loads(path.read_text()) if path.exists() else None


def pool_candidates(fc, pool, excluded, blocked, used):
    """Certified variants for the slot's field, in template/salience order: concepts no sibling chain uses come
    first; a variant is skipped when its values meet the chain's other pools (H6) or a sibling's A/P_M of the same
    concept."""
    fresh, reuse = [], []
    for c in fc.c_order():
        entry = pool.get(c)
        if not entry or entry["field"] != fc.field or c in blocked:
            continue
        for v in entry["variants"]:
            if not v["pass"]:
                continue
            cert = Candidate.from_dict(v["cand"])
            if {cert.A, *cert.P_M} & (set(excluded) | set(used.get(c, ()))):
                continue
            # keep the certified members; choose N_p and N_t around the chain's other pools (H6)
            cand, _ = build_candidate(fc, c, excluded, 1, fixed=(cert.A, cert.P_M))
            if cand is None:
                continue
            (reuse if c in used else fresh).append(cand)
            break
    return fresh + reuse


def current_candidates(ds, cfg, state, contexts):
    """Assign a current candidate to every unpinned slot (same-field later slots exclude earlier pools)."""
    failed, used = sibling_registry(state)
    pool = load_pool(state)
    for s in sorted(state["slots"], key=lambda x: x["level"]):
        if s["pinned"]:
            s["current"] = s["pinned"]
            continue
        fc = contexts[s["field"]]
        # within a chain every level brings a new concept; sibling chains may reuse a concept with other members
        excluded, blocked = set(), set(s["tried"]) | failed
        for o in state["slots"]:
            if o is s:
                continue
            if contexts[o["field"]].uname == fc.uname:
                blocked |= set(o["tried"])  # a list that failed in one slot is not retried in another
            other = o["pinned"] or (o.get("current") if o["level"] < s["level"] else None)
            if not other:
                continue
            blocked.add(other["C"])
            if contexts[o["field"]].uname == fc.uname:
                excluded |= set(Candidate.from_dict(other).pool())
        if pool is not None:
            cands = pool_candidates(fc, pool, excluded, blocked, used)
            reasons = [f"{len(cands)} certified variants left"]
        else:
            cands, reasons = candidates_for_slot(fc, excluded, s["level"], tried=blocked, limit=1, avoid=used)
        if not cands:
            raise ChainStop("select", f"slot L{s['level']} ({s['field']}): no candidate left "
                            f"(tried {len(s['tried'])}; {'; '.join(reasons[-3:])})",
                            f"add lists or templates for field {s['field']} (each C needs a member in two "
                            f"competing lists)" + (" and rerun clrsynth certify" if pool is not None else ""))
        s["current"] = cands[0].to_dict()


def select(ds, cfg, state, repo_root, run_dir):
    contexts = {spec["field"]: FieldContext(ds, cfg, spec["field"]) for spec in cfg["fields"]}
    endpoint = Endpoint(stop_flag=lambda: _STOP["flag"])
    criterion = cfg["probe"].get("criterion", "soft")
    band = cfg["probe"].get("p1_band", [P1_LOW, P1_HIGH])
    while not all(s["pinned"] for s in state["slots"]):
        current_candidates(ds, cfg, state, contexts)
        slots = [{"level": s["level"], "field": s["field"], "cand": Candidate.from_dict(s["current"])}
                 for s in state["slots"]]
        try:
            chain = Chain(ds, cfg, slots)
            unpinned = [s["level"] for s in state["slots"] if not s["pinned"]]
            items = chain.probe_prompts(unpinned)
        except PlacementError as e:
            raise ChainStop("select", str(e), "make the dataset world larger or add background values")
        state["rounds"] += 1
        save_state(Path(state["_path"]), state)
        rdir = run_dir / "probe" / f"S{state['rounds']}"
        rdir.mkdir(parents=True, exist_ok=True)
        replies = endpoint.run_all([it["prompt"] for it in items])
        state["requests"] += len(items)
        for it, rep in zip(items, replies):
            it["reply"] = rep
            it["parsed"] = parse_json_answer(rep)
            name = f"{it['kind']}_L{it['level'] or 'all'}_v{it['version'] if it['version'] is not None else '-'}_{it['sample']}.json"
            (rdir / name).write_text(json.dumps({**it, "reasoning": endpoint.reasoning, "model": endpoint.model},
                                                ensure_ascii=False, indent=1))
        p0 = [it["parsed"] for it in items if it["kind"] == "P0"]
        verdicts = {}
        for j in unpinned:
            cand = chain.slot(j)["cand"]
            others = set()
            for o in chain.slots:
                if o["level"] != j:
                    others |= set(o["cand"].pool())
            v0 = judge_p0(cand, j, p0)
            v1 = judge_p1h(cand, j, [(it["version"], it["parsed"]) for it in items
                                     if it["kind"] == "P1H" and it["level"] == j], criterion, others - set(cand.pool()))
            v2 = judge_p1(cand, j, [(it["version"], it["parsed"]) for it in items
                                    if it["kind"] == "P1" and it["level"] == j], band) if band else {"pass": True}
            verdicts[j] = {"C": cand.C, "P0": v0, "P1H": v1, "P1": v2}
            s = next(x for x in state["slots"] if x["level"] == j)
            if v0["pass"] and v1["pass"] and v2["pass"]:
                s["pinned"] = s["current"]
            else:
                s["tried"].append(cand.C)
                s["current"] = None
        (rdir / "VERDICTS.json").write_text(json.dumps(verdicts, indent=1, ensure_ascii=False))
        state["history"].append({"round": state["rounds"], "verdicts": {
            str(j): {"C": v["C"], "P0": v["P0"]["pass"], "P1H": v["P1H"]["pass"],
                     "soft": v["P1H"]["mean_soft"], "P1": v["P1"]["pass"], "g": v["P1"].get("mean_g")}
            for j, v in verdicts.items()}})
        save_state(Path(state["_path"]), state)


def make_chain(chain_path, repo_root):
    _install_signals()
    t0 = time.time()
    cfg = load_chain(chain_path)
    ds = Dataset(cfg["_inputs_root"], cfg["dataset"])
    od = out_dir(cfg, repo_root)
    spath = od / "STATE.json"
    state = load_state(spath)
    step = "lint"
    try:
        errors = lint_mod.lint_dataset(ds)
        if errors:
            raise ChainStop("lint", f"{len(errors)} lint error(s): {errors[0]}", "fix the inputs reported by lint")
        if state is None:
            step = "slots"
            try:
                slots = allocate_slots(ds, cfg)
            except ValueError as e:
                raise ChainStop("slots", str(e), "add another trap field to the scenario and chain config")
            state = {"slots": [{**s, "pinned": None, "tried": [], "current": None} for s in slots],
                     "rounds": 0, "requests": 0, "stage": "select", "runs": 0, "history": []}
        state["_path"] = str(spath)
        state["runs"] += 1
        lroot = log_root(cfg, repo_root)
        n = 1
        while (lroot / f"run{n}").exists():
            n += 1
        run_dir = lroot / f"run{n}"
        run_dir.mkdir(parents=True)
        save_state(spath, state)
        if state["stage"] == "select":
            step = "select"
            select(ds, cfg, state, repo_root, run_dir)
            state["stage"] = "build"
            save_state(spath, state)
        from . import build as build_mod, check as check_mod
        if state["stage"] == "build":
            step = "build"
            build_mod.build(ds, cfg, state, od)
            state["stage"] = "check"
            save_state(spath, state)
        if state["stage"] == "check":
            step = "check"
            report = check_mod.check(ds, cfg, od)
            if not report["pass"]:
                raise ChainStop("check", f"zero check failed: {', '.join(report['failed'][:5])}",
                                f"see {od / 'ZERO_CHECK.json'}")
            state["stage"] = "repro"
            save_state(spath, state)
        if state["stage"] == "repro":
            step = "verify-repro"
            diffs = build_mod.verify_repro(ds, cfg, state, od)
            if diffs:
                raise ChainStop("verify-repro", f"{len(diffs)} file(s) differ: {diffs[:3]}",
                                "the build is not deterministic; report this as a bug")
            state["stage"] = "done"
            save_state(spath, state)
        pinned = ", ".join(f"L{s['level']}={s['pinned']['C']}" for s in state["slots"])
        print(f"make-chain OK {cfg['id']}: {pinned}; rounds {state['rounds']}; probe requests "
              f"{state['requests']}; {time.time() - t0:.0f}s")
        return 0
    except ChainStop as e:
        if state is not None:
            save_state(spath, state)
        print(f"make-chain FAILED {cfg['id']} at {e.step}: {e.why}\n  needed: {e.need}", file=sys.stderr)
        return 2
    except ProbeError as e:
        if state is not None:
            save_state(spath, state)
        print(f"make-chain FAILED {cfg['id']} at {step}: probe endpoint error: {e}\n  needed: check "
              f"CLRSYNTH_ENDPOINT / key / model; rerun to resume", file=sys.stderr)
        return 3
    except Exception as e:  # every failure ends in a summary, never a bare traceback
        if state is not None:
            save_state(spath, state)
        print(f"make-chain FAILED {cfg['id']} at {step}: {type(e).__name__}: {e}\n  needed: see the message; "
              f"rerun the same command to resume after fixing", file=sys.stderr)
        return 4
