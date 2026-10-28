#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from runner import run_candidate, FORMAT


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--candidate", required=True)
    p.add_argument("--input", required=True)
    a = p.parse_args()
    raw = Path(a.input).read_text(encoding="utf-8")
    data = raw if FORMAT == "text" else json.loads(raw)
    print(json.dumps(run_candidate(Path(a.candidate).read_text(encoding="utf-8"), data), ensure_ascii=False))


if __name__ == "__main__":
    main()
