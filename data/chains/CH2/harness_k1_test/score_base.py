#!/usr/bin/env python3
"""Score one program on a task file's hidden instances: --candidate prog.py --task <task.json>."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import run_candidate


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--task", required=True)
    a = p.parse_args()
    code = Path(a.candidate).read_text(encoding="utf-8")
    task = json.loads(Path(a.task).read_text(encoding="utf-8"))
    rows = []
    for item in task["hidden"]:
        res = run_candidate(code, item["data"])
        rows.append({"stratum": item["stratum"], "expected": item["expected"], "result": res,
                     "passed": bool(res.get("ok") and res.get("value") == item["expected"])})
    print(json.dumps({"passed": sum(r["passed"] for r in rows), "total": len(rows),
                      "full_score": all(r["passed"] for r in rows), "instances": rows}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
