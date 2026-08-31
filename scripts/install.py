#!/usr/bin/env python3
"""Mirror the runtime skill files into every agent skills root. Stdlib only.

  python scripts/install.py --check
  python scripts/install.py
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ROOTS = [
    Path.home() / ".agents" / "skills",
    Path.home() / ".claude" / "skills",
    Path.home() / ".cursor" / "skills",
]
PAYLOAD = ["SKILL.md", "references", "data", "scripts/lookup.py"]


def sources() -> tuple[list[tuple[Path, str]], list[str]]:
    out: list[tuple[Path, str]] = []
    missing: list[str] = []
    for rel in PAYLOAD:
        src = ROOT / rel
        if src.is_dir():
            out += [(p, str(p.relative_to(ROOT))) for p in sorted(src.rglob("*")) if p.is_file()]
        elif src.is_file():
            out.append((src, rel))
        else:
            missing.append(rel)
    return out, missing


def targets(*, new_roots: bool) -> list[Path]:
    """Existing installs only, unless --all explicitly creates the destination."""
    if new_roots:
        return [root / ROOT.name for root in ROOTS]
    return [root / ROOT.name for root in ROOTS if (root / ROOT.name).is_dir()]


def main() -> int:
    p = argparse.ArgumentParser(description="Install or check the needquality skill")
    p.add_argument("--check", action="store_true", help="report drift, write nothing")
    p.add_argument("--all", action="store_true", help="also install into roots that lack it")
    args = p.parse_args()

    dests = targets(new_roots=args.all)
    if not dests:
        print("no skills root found", file=sys.stderr)
        return 2

    files, missing = sources()
    if missing:
        print(f"missing payload: {', '.join(missing)}", file=sys.stderr)
        return 2
    if not files:
        print("no payload files found", file=sys.stderr)
        return 2
    drift = 0
    for dest in dests:
        for src, rel in files:
            out = dest / rel
            if out.is_file() and filecmp.cmp(src, out, shallow=False):
                continue
            drift += 1
            if args.check:
                print(f"drift: {out}")
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)

    if args.check:
        print(f"{drift} file(s) differ across {len(dests)} root(s)")
        return 1 if drift else 0
    print(f"synced {drift} file(s) to {len(dests)} root(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
