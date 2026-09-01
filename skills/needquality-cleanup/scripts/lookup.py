#!/usr/bin/env python3
"""Fingerprint lookup for a needquality cleanup pass. Stdlib only.

  python scripts/lookup.py --ext .py
  python scripts/lookup.py --domain sql
  python scripts/lookup.py n+1
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = ROOT / "data" / "tells.csv"
EXT_DOMAIN = {
    ".js": ("js",),
    ".mjs": ("js",),
    ".cjs": ("js",),
    ".ts": ("js", "ts"),
    ".mts": ("js", "ts"),
    ".cts": ("js", "ts"),
    ".jsx": ("react", "js", "ui"),
    ".tsx": ("react", "js", "ts", "ui"),
    ".vue": ("js", "ui"),
    ".svelte": ("js", "ui"),
    ".py": ("py",),
    ".go": ("go",),
    ".rs": ("rs",),
    ".sql": ("sql", "trust"),
    ".prisma": ("sql", "trust"),
}


def rows() -> list[dict[str, str]]:
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def haystack(row: dict[str, str]) -> str:
    raw = " ".join(row.get(k, "") for k in ("id", "domain", "tell", "fix"))
    return raw.lower().replace("+", " plus ").replace("-", " ")


def match(
    row: dict[str, str],
    *,
    domains: tuple[str, ...] | None,
    query: str | None,
) -> bool:
    if domains and row.get("domain") not in domains:
        return False
    if query:
        needle = query.lower().replace("+", " plus ").replace("-", " ")
        if needle not in haystack(row):
            return False
    return True


def main() -> int:
    p = argparse.ArgumentParser(description="NeedQuality tell lookup")
    p.add_argument("query", nargs="?", help="substring over id/tell/fix")
    p.add_argument("--domain", "-d", help="ui copy ts js react py go rs sql trust test")
    p.add_argument("--ext", "-e", help="file extension, e.g. .tsx")
    p.add_argument("--limit", "-n", type=int, default=20)
    p.add_argument("--json", action="store_true", help="emit matching rows as JSON")
    args = p.parse_args()
    if args.limit < 1:
        p.error("--limit must be at least 1")
    domain = args.domain
    domains: tuple[str, ...] | None = (domain,) if domain else None
    if args.ext:
        ext = args.ext if args.ext.startswith(".") else f".{args.ext}"
        mapped = EXT_DOMAIN.get(ext.lower())
        if not mapped:
            print(f"no domain for {ext}; pass --domain", file=sys.stderr)
            return 2
        domains = mapped if domains is None else tuple(dict.fromkeys((*domains, *mapped)))
    hits = [r for r in rows() if match(r, domains=domains, query=args.query)]
    if args.json:
        print(json.dumps(hits[: args.limit], ensure_ascii=False, indent=2))
        return 0
    if not hits:
        print("no matches")
        return 0
    for row in hits[: args.limit]:
        print(f"## {row['id']} ({row['domain']})")
        print(f"- tell: {row['tell']}")
        print(f"- fix: {row['fix']}")
        print()
    if len(hits) > args.limit:
        print(f"… {len(hits) - args.limit} more; raise --limit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
