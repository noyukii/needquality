#!/usr/bin/env python3
"""Validate the installable skill shape. Stdlib only."""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
TRACE_LABEL_RE = re.compile(r"^(?:job|flow|load):[a-z0-9-]+$")
RESEARCH_PATH = ROOT / "references" / "flows" / "research" / "SKILL.md"


def frontmatter(text: str) -> dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    _, body, _ = text.split("---\n", 2)
    fields: dict[str, str] = {}
    lines = body.splitlines()
    for index, line in enumerate(lines):
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if key == "description" and value in {">", "|"}:
            folded: list[str] = []
            for continuation in lines[index + 1 :]:
                if not continuation.startswith("  "):
                    break
                folded.append(continuation.strip())
            value = " ".join(folded) if value == ">" else "\n".join(folded)
        fields.setdefault(key, value)
    return fields


def validate_docs(errors: list[str]) -> int:
    docs = [ROOT / "SKILL.md", *sorted((ROOT / "references").rglob("*.md"))]
    for path in docs:
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            target = target.split("#", 1)[0]
            if not target or "://" in target or target.startswith("mailto:"):
                continue
            if target == "link" or target.startswith("./src/"):
                continue
            resolved = (path.parent / target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: link escapes skill: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing link: {target}")
    skill = ROOT / "SKILL.md"
    fields = frontmatter(skill.read_text(encoding="utf-8"))
    if fields.get("name") != ROOT.name:
        errors.append(f"SKILL.md: name must be {ROOT.name!r}")
    if not fields.get("description"):
        errors.append("SKILL.md: missing description")
    if len(skill.read_text(encoding="utf-8").splitlines()) > 500:
        errors.append("SKILL.md: over 500 lines")
    if len(fields.get("description", "")) > 1024:
        errors.append("SKILL.md: description over 1024 characters")
    return len(docs)


def validate_research(errors: list[str]) -> None:
    skill_text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if "(references/flows/research/SKILL.md)" not in skill_text:
        errors.append("SKILL.md: missing research reference pointer")
    if not RESEARCH_PATH.is_file():
        errors.append("research: missing references/flows/research/SKILL.md")
        return
    text = RESEARCH_PATH.read_text(encoding="utf-8")
    required = {
        "`L0`": "L0 level",
        "`L1`": "L1 level",
        "`L2`": "L2 level",
        "`L3`": "L3 level",
        "Firecrawl is": "Firecrawl consent policy",
        "not the default": "Firecrawl default policy",
        "Do not run `firecrawl --status`": "Firecrawl pre-consent probe rule",
        "Stop when every material slot": "research stop rule",
        "one Markdown note": "research output contract",
    }
    for marker, label in required.items():
        if marker not in text:
            errors.append(f"research: missing {label}")


def validate_tells(errors: list[str]) -> int:
    path = ROOT / "data" / "tells.csv"
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"id", "domain", "tell", "fix"}
    headers = set(rows[0]) if rows else set()
    if headers != required:
        errors.append("data/tells.csv: headers must be id, domain, tell, fix")
    ids = [row.get("id", "") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("data/tells.csv: duplicate id")
    if any(not all(row.get(k, "").strip() for k in required) for row in rows):
        errors.append("data/tells.csv: blank field")
    return len(rows)


def validate_evals(errors: list[str]) -> int:
    path = ROOT / "evals" / "evals.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    cases = data.get("evals", [])
    ids: list[int] = []
    for case in cases:
        cid = case.get("id")
        ids.append(cid)
        if not case.get("prompt") or not case.get("expectations"):
            errors.append(f"eval {cid}: prompt and expectations required")
        if "trace" in case:
            trace = case["trace"]
            if not isinstance(trace, dict):
                errors.append(f"eval {cid}: trace must be an object")
            else:
                mode = trace.get("mode", "exact")
                if mode not in {"exact", "absent"}:
                    errors.append(f"eval {cid}: trace mode must be exact or absent")
                elif mode == "absent":
                    if set(trace) != {"mode"}:
                        errors.append(f"eval {cid}: absent trace cannot include parts")
                else:
                    parts = trace.get("parts")
                    if not isinstance(parts, list) or not parts:
                        errors.append(f"eval {cid}: exact trace needs non-empty parts")
                    elif not all(isinstance(part, str) and TRACE_LABEL_RE.fullmatch(part) for part in parts):
                        errors.append(f"eval {cid}: trace parts must use canonical labels")
                    elif len(parts) != len(set(parts)):
                        errors.append(f"eval {cid}: trace parts must be unique")
        for rel in case.get("files", []):
            path = Path(rel) if isinstance(rel, str) else Path()
            if (
                not isinstance(rel, str)
                or path.is_absolute()
                or path.parts[:2] != ("evals", "files")
                or ".." in path.parts
            ):
                errors.append(f"eval {cid}: fixture is outside evals/files {rel!r}")
                continue
            fixture = ROOT / path
            if not fixture.is_file():
                errors.append(f"eval {cid}: missing fixture {rel}")
    if len(ids) != len(set(ids)):
        errors.append("evals/evals.json: duplicate id")
    return len(cases)


def main() -> int:
    errors: list[str] = []
    docs = validate_docs(errors)
    validate_research(errors)
    tells = validate_tells(errors)
    evals = validate_evals(errors)
    if errors:
        print("invalid needquality:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    print(f"valid: {docs} docs, {tells} tells, {evals} evals")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
