#!/usr/bin/env python3
"""Validate the NeedQuality source and installable skill shape. Stdlib only."""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

from eval_schema import load_evals, validate_baseline, validate_evals

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
TABLE_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RESEARCH_PATH = ROOT / "references" / "flows" / "research.md"


def frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    if not text.startswith("---\n"):
        return {}, []
    try:
        _, body, _ = text.split("---\n", 2)
    except ValueError:
        return {}, ["unclosed YAML frontmatter"]
    fields: dict[str, str] = {}
    errors: list[str] = []
    lines = body.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.strip():
            index += 1
            continue
        if line.startswith((" ", "\t")) or ":" not in line:
            errors.append(f"invalid frontmatter line: {line!r}")
            index += 1
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if key in fields:
            errors.append(f"duplicate frontmatter key: {key}")
        if value in {">", "|"}:
            continuation: list[str] = []
            index += 1
            while index < len(lines) and lines[index].startswith("  "):
                continuation.append(lines[index].strip())
                index += 1
            value = " ".join(continuation) if value == ">" else "\n".join(continuation)
        else:
            index += 1
        fields[key] = value.strip('"\'')
    return fields, errors


def local_target(source: Path, target: str) -> Path | None:
    clean = target.split("#", 1)[0]
    if not clean or "://" in clean or clean.startswith(("mailto:", "/")):
        return None
    if clean == "link" or clean.startswith("./src/"):
        return None
    return (source.parent / clean).resolve(strict=False)


def validate_docs(errors: list[str]) -> int:
    root_skill = ROOT / "SKILL.md"
    references = sorted((ROOT / "references").rglob("*.md"))
    docs = [root_skill, *references]
    root_resolved = ROOT.resolve()
    graph: dict[Path, set[Path]] = defaultdict(set)

    skill_files = sorted(
        path for path in ROOT.rglob("SKILL.md") if ".git" not in path.parts
    )
    if skill_files != [root_skill]:
        shown = ", ".join(str(path.relative_to(ROOT)) for path in skill_files)
        errors.append(f"discovery: expected only root SKILL.md, found {shown}")

    for path in docs:
        text = path.read_text(encoding="utf-8")
        for target in LINK_RE.findall(text):
            resolved = local_target(path, target)
            if resolved is None:
                continue
            try:
                resolved.relative_to(root_resolved)
            except ValueError:
                errors.append(f"{path.relative_to(ROOT)}: link escapes skill: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{path.relative_to(ROOT)}: missing link: {target}")
                continue
            if resolved.suffix == ".md":
                graph[path.resolve()].add(resolved)

    reachable: set[Path] = set()
    queue = deque([root_skill.resolve()])
    while queue:
        path = queue.popleft()
        if path in reachable:
            continue
        reachable.add(path)
        queue.extend(graph[path] - reachable)
    for path in references:
        if path.resolve() not in reachable:
            errors.append(f"references: unreachable from SKILL.md: {path.relative_to(ROOT)}")

    fields, metadata_errors = frontmatter(root_skill.read_text(encoding="utf-8"))
    errors.extend(f"SKILL.md: {error}" for error in metadata_errors)
    if set(fields) != {"name", "description"}:
        errors.append("SKILL.md: frontmatter keys must be exactly name and description")
    if fields.get("name") != ROOT.name:
        errors.append(f"SKILL.md: name must be {ROOT.name!r}")
    if not fields.get("description"):
        errors.append("SKILL.md: missing description")
    if len(root_skill.read_text(encoding="utf-8").splitlines()) > 500:
        errors.append("SKILL.md: over 500 lines")
    if len(fields.get("description", "")) > 1024:
        errors.append("SKILL.md: description over 1024 characters")
    return len(docs)


def words_rows() -> list[tuple[str, str]]:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    section = text.split("## Words", 1)[1].split("## Load", 1)[0]
    rows: list[tuple[str, str]] = []
    for line in section.splitlines():
        if not line.startswith("|") or line.startswith(("|---", "| They say")):
            continue
        cells = [cell.strip() for cell in line.strip("|").split("|")]
        if len(cells) != 3:
            continue
        links = TABLE_LINK_RE.findall(cells[2])
        rows.append((cells[0], links[0] if links else ""))
    return rows


def validate_routes(errors: list[str]) -> tuple[int, int]:
    rows = words_rows()
    phrases: dict[str, str] = {}
    targets: dict[str, list[str]] = defaultdict(list)
    for phrase_cell, target in rows:
        for phrase in phrase_cell.split(","):
            normalized = re.sub(r"[`*]", "", phrase).strip().lower()
            if not normalized:
                continue
            if normalized in phrases:
                errors.append(
                    f"routes: duplicate phrase {normalized!r} in {phrases[normalized]!r} and {phrase_cell!r}"
                )
            phrases[normalized] = phrase_cell
        if target:
            targets[target].append(phrase_cell)

    expected_jobs = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "references" / "jobs").glob("*.md")
    }
    expected_flows = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "references" / "flows").glob("*.md")
    }
    actual = {
        (ROOT / target).resolve().relative_to(ROOT.resolve()).as_posix()
        for target in targets
    }
    for target in sorted(expected_jobs | expected_flows):
        if target not in actual:
            errors.append(f"routes: missing Words row for {target}")
    for target, owners in targets.items():
        if len(owners) > 1:
            errors.append(f"routes: target {target} is owned by multiple rows: {owners}")
    return len(expected_jobs), len(expected_flows)


def validate_research(errors: list[str]) -> None:
    if not RESEARCH_PATH.is_file():
        errors.append("research: missing references/flows/research.md")
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
    if any(not all(row.get(key, "").strip() for key in required) for row in rows):
        errors.append("data/tells.csv: blank field")
    return len(rows)


def validate_metadata(errors: list[str]) -> None:
    path = ROOT / "agents" / "openai.yaml"
    required = {
        'display_name: "NeedQuality"',
        'short_description: "Route software work to focused quality guidance"',
        'default_prompt: "Use $needquality to route this task and apply the smallest reliable workflow."',
        "allow_implicit_invocation: true",
    }
    if not path.is_file():
        errors.append("agents/openai.yaml: missing")
        return
    text = path.read_text(encoding="utf-8")
    for marker in required:
        if marker not in text:
            errors.append(f"agents/openai.yaml: missing {marker}")


def validate_legacy_manifest(errors: list[str]) -> None:
    path = ROOT / "data" / "legacy-v1-manifest.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        errors.append(f"legacy manifest: {error}")
        return
    files = payload.get("files") if isinstance(payload, dict) else None
    if payload.get("format") != 1 or not isinstance(files, dict) or not files:
        errors.append("legacy manifest: expected format 1 with files")
    elif not any(rel.endswith("/SKILL.md") for rel in files):
        errors.append("legacy manifest: missing nested flow entrypoints")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate NeedQuality")
    parser.add_argument("--stats", action="store_true", help="print inventory as JSON")
    args = parser.parse_args()
    errors: list[str] = []
    docs = validate_docs(errors)
    jobs, flows = validate_routes(errors)
    validate_research(errors)
    tells = validate_tells(errors)
    validate_metadata(errors)
    validate_legacy_manifest(errors)
    eval_data = load_evals(ROOT / "evals" / "evals.json")
    errors.extend(validate_evals(eval_data, ROOT))
    errors.extend(validate_baseline(ROOT))
    evals = len(eval_data.get("evals", []))
    if errors:
        print("invalid needquality:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 1
    stats = {"docs": docs, "jobs": jobs, "flows": flows, "tells": tells, "evals": evals}
    if args.stats:
        print(json.dumps(stats, sort_keys=True))
    else:
        print(
            f"valid: {docs} docs, {jobs} jobs, {flows} flows, "
            f"{tells} tells, {evals} evals"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
