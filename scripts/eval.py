#!/usr/bin/env python3
"""Check that eval fixture files exist. Stdlib only.

  python scripts/eval.py
  python scripts/eval.py --list
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS_PATH = ROOT / "evals" / "evals.json"


def load() -> dict:
    return json.loads(EVALS_PATH.read_text(encoding="utf-8"))


def check(data: dict) -> int:
    missing: list[str] = []
    for case in data.get("evals", []):
        eid = case.get("id")
        for rel in case.get("files", []):
            path = ROOT / rel
            if not path.is_file():
                missing.append(f"eval {eid}: {rel}")
    if missing:
        print("missing fixtures:", file=sys.stderr)
        for line in missing:
            print(f"  {line}", file=sys.stderr)
        return 1
    n = len(data.get("evals", []))
    print(f"{n} evals, all fixture files exist")
    return 0


def list_cases(data: dict) -> int:
    for case in data.get("evals", []):
        prompt = str(case.get("prompt", "")).split("\n", 1)[0]
        print(f"{case.get('id')}\t{prompt}")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Noslop eval fixture check")
    p.add_argument("--list", action="store_true", help="print id and prompt")
    args = p.parse_args()
    if not EVALS_PATH.is_file():
        print(f"missing {EVALS_PATH}", file=sys.stderr)
        return 2
    data = load()
    if args.list:
        return list_cases(data)
    return check(data)


if __name__ == "__main__":
    raise SystemExit(main())
