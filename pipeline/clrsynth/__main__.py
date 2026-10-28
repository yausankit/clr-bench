"""Command line: python -m clrsynth <command> ..."""
import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def main(argv=None):
    p = argparse.ArgumentParser(prog="clrsynth")
    sub = p.add_subparsers(dest="cmd", required=True)
    for name in ("lint", "salience"):
        sp = sub.add_parser(name)
        sp.add_argument("dataset")
        sp.add_argument("--inputs-root", default=str(REPO / "inputs"))
    for name in ("make-chain", "build", "check", "verify-repro", "screen"):
        sp = sub.add_parser(name)
        sp.add_argument("chain")
        sp.add_argument("--out-root", default=str(REPO))
    sp = sub.add_parser("certify")
    sp.add_argument("chains", nargs="+", help="all chain configs of one dataset")
    sp.add_argument("--out-root", default=str(REPO))
    a = p.parse_args(argv)
    if a.cmd == "certify":
        from .certify import certify
        return certify(a.chains, a.out_root)
    if a.cmd == "lint":
        from .lint import lint_main
        return lint_main(a.dataset, a.inputs_root)
    if a.cmd == "salience":
        from .salience import merge_salience
        for k, v in merge_salience(Path(a.inputs_root).resolve() / a.dataset).items():
            print(f"{k}: {v}")
        return 0
    if a.cmd == "screen":
        from .screen import screen
        screen(a.chain, a.out_root)
        return 0
    if a.cmd == "make-chain":
        from .makechain import make_chain
        return make_chain(a.chain, a.out_root)
    from .inputs import Dataset, load_chain
    from .makechain import out_dir, load_state
    cfg = load_chain(a.chain)
    ds = Dataset(cfg["_inputs_root"], cfg["dataset"])
    od = out_dir(cfg, a.out_root)
    state = load_state(od / "STATE.json")
    if state is None or not all(s.get("pinned") for s in state["slots"]):
        print(f"{a.cmd}: chain {cfg['id']} has unpinned slots; run make-chain first", file=sys.stderr)
        return 2
    from . import build as b, check as c
    if a.cmd == "build":
        b.build(ds, cfg, state, od)
        print(f"build OK: {od}")
        return 0
    if a.cmd == "check":
        r = c.check(ds, cfg, od)
        print(f"check {'OK' if r['pass'] else 'FAILED'}: {r['checks']} checks, failed: {r['failed'][:10]}")
        return 0 if r["pass"] else 1
    diffs = b.verify_repro(ds, cfg, state, od)
    print("verify-repro OK" if not diffs else f"verify-repro FAILED: {diffs[:10]}")
    return 0 if not diffs else 1


if __name__ == "__main__":
    sys.exit(main())
