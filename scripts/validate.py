#!/usr/bin/env python3
"""Validate the NeedQuality source and installable skill shape. Stdlib only."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict, deque
from pathlib import Path
from urllib.parse import unquote, urlsplit

from eval_schema import load_evals, validate_baseline, validate_evals
from lookup import EXT_DOMAIN
from runtime_payload import frontmatter, runtime_files

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK_RE = re.compile(r"!?\[([^\]]+)\]\[([^\]]*)\]")
REFERENCE_DEFINITION_RE = re.compile(r"(?m)^ {0,3}\[([^\]]+)\]:\s*(\S+)")
TABLE_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
RESEARCH_PATH = ROOT / "references" / "flows" / "research.md"
EXPECTED_DESCRIPTION = (
    "Route agent tasks to focused guidance for implementation, debugging, "
    "code review, architecture, testing, delivery, technical research, "
    "software documentation, UI/UX, trust boundaries, agent-workflow design, "
    "structured writing, and teaching. Use for repository work, technical "
    "artifacts, and the bundled writing and teaching flows; do not use for "
    "unrelated general knowledge."
)
TELL_DOMAINS = {
    "agent",
    "copy",
    "domain",
    "go",
    "js",
    "py",
    "react",
    "rs",
    "sql",
    "test",
    "trust",
    "ts",
    "ui",
}
FORBIDDEN_PORTABLE_TEXT = {
    "/clear": "provider-specific clear command",
    "/compact": "provider-specific compact command",
    "~/.claude/skills/": "provider-specific specialist path",
    "bundled SKILL.md": "nested child-skill terminology",
    "model-invoked references": "nested discovery terminology",
    "Model-invoked": "nested discovery terminology",
    "Do not load frontend-design": "external skill suppression",
    "Firecrawl skill is also loaded": "external skill precedence claim",
}


def prose_without_code(text: str) -> str:
    kept: list[str] = []
    fence: str | None = None
    for line in text.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if fence:
            if marker == fence:
                fence = None
            continue
        if marker in {"```", "~~~"}:
            fence = marker
            continue
        kept.append(re.sub(r"(?P<ticks>`+).*?(?P=ticks)", "", line))
    return "\n".join(kept)


def clean_link_target(target: str) -> str:
    target = target.strip()
    if target.startswith("<") and ">" in target:
        return target[1 : target.index(">")]
    return target.split(maxsplit=1)[0] if target else ""


def local_target(source: Path, target: str) -> Path | None:
    target = clean_link_target(target)
    parsed = urlsplit(target)
    if parsed.scheme:
        if parsed.scheme in {"http", "https", "mailto"}:
            return None
        raise ValueError(f"unsupported link scheme: {target}")
    if not parsed.path:
        return source.resolve() if parsed.fragment else None
    if parsed.path.startswith("/"):
        raise ValueError(f"absolute local link: {target}")
    return (source.parent / unquote(parsed.path)).resolve(strict=False)


def document_targets(text: str, errors: list[str], label: str) -> list[str]:
    prose = prose_without_code(text)
    targets = LINK_RE.findall(prose)
    definitions: dict[str, str] = {}
    for name, target in REFERENCE_DEFINITION_RE.findall(prose):
        key = " ".join(name.lower().split())
        if key in definitions:
            errors.append(f"{label}: duplicate reference-link definition: {name}")
        definitions[key] = target
    for text_label, reference in REFERENCE_LINK_RE.findall(prose):
        key = " ".join((reference or text_label).lower().split())
        if key not in definitions:
            errors.append(f"{label}: missing reference-link definition: {reference or text_label}")
        else:
            targets.append(definitions[key])
    return targets


def heading_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = defaultdict(int)
    prose = prose_without_code(text)
    for heading in re.findall(r"(?m)^ {0,3}#{1,6}\s+(.+?)\s*#*\s*$", prose):
        label = re.sub(r"!?\[([^\]]+)\]\([^)]+\)", r"\1", heading)
        label = re.sub(r"<[^>]+>|[*_~]", "", label).strip().lower()
        base = re.sub(r"[^\w\- ]", "", label)
        base = re.sub(r"[ \t]+", "-", base)
        index = counts[base]
        counts[base] += 1
        anchors.add(base if index == 0 else f"{base}-{index}")
    anchors.update(
        match
        for match in re.findall(r"(?i)<a\s+(?:id|name)=[\"']([^\"']+)[\"']", prose)
    )
    return anchors


def reference_files(root: Path, errors: list[str]) -> list[Path]:
    references = root / "references"
    if not references.is_dir():
        errors.append("references: missing directory")
        return []
    files: list[Path] = []
    for current, directories, names in os.walk(references, topdown=True, followlinks=False):
        parent = Path(current)
        for name in [*directories, *names]:
            path = parent / name
            if path.is_symlink():
                errors.append(f"references: symlink is not allowed: {path.relative_to(root)}")
        directories[:] = [name for name in directories if not (parent / name).is_symlink()]
        files.extend(
            parent / name
            for name in names
            if name != ".DS_Store" and not (parent / name).is_symlink()
        )
    return sorted(files)


def validate_docs(errors: list[str]) -> int:
    root_skill = ROOT / "SKILL.md"
    if not root_skill.is_file():
        errors.append("discovery: missing root SKILL.md")
        return 0
    references = reference_files(ROOT, errors)
    markdown = [path for path in references if path.suffix.lower() == ".md"]
    docs = [root_skill, *markdown]
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
        for target in document_targets(text, errors, path.relative_to(ROOT).as_posix()):
            try:
                resolved = local_target(path, target)
            except ValueError as error:
                errors.append(f"{path.relative_to(ROOT)}: {error}")
                continue
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
            if not resolved.is_file():
                errors.append(f"{path.relative_to(ROOT)}: link is not a regular file: {target}")
                continue
            fragment = unquote(urlsplit(clean_link_target(target)).fragment)
            if fragment and resolved.suffix.lower() == ".md":
                if fragment not in heading_anchors(resolved.read_text(encoding="utf-8")):
                    errors.append(f"{path.relative_to(ROOT)}: missing fragment: {target}")
                    continue
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
    if fields.get("name") != "needquality":
        errors.append("SKILL.md: name must be 'needquality'")
    if not fields.get("description"):
        errors.append("SKILL.md: missing description")
    elif fields["description"] != EXPECTED_DESCRIPTION:
        errors.append("SKILL.md: description does not match the supported scope")
    if len(root_skill.read_text(encoding="utf-8").splitlines()) > 500:
        errors.append("SKILL.md: over 500 lines")
    if len(fields.get("description", "")) > 1024:
        errors.append("SKILL.md: description over 1024 characters")
    return len(docs)


def table_rows(
    section: str,
    label: str,
    expected_header: list[str],
    errors: list[str] | None,
) -> list[list[str]]:
    lines = [line for line in section.splitlines() if line.startswith("|")]
    if len(lines) < 2:
        if errors is not None:
            errors.append(f"routes: missing {label} table")
        return []
    parsed = [[cell.strip() for cell in line.strip("|").split("|")] for line in lines]
    if parsed[0] != expected_header and errors is not None:
        errors.append(
            f"routes: {label} header must be {' | '.join(expected_header)}"
        )
    if len(parsed[1]) != len(expected_header) or not all(
        re.fullmatch(r":?-{3,}:?", cell) for cell in parsed[1]
    ):
        if errors is not None:
            errors.append(f"routes: malformed {label} table separator")
    rows: list[list[str]] = []
    for number, cells in enumerate(parsed[2:], 1):
        if len(cells) != len(expected_header) or any(not cell for cell in cells):
            if errors is not None:
                errors.append(f"routes: malformed {label} row {number}: {lines[number + 1]}")
            continue
        rows.append(cells)
    return rows


def words_rows(errors: list[str] | None = None) -> list[tuple[str, str]]:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    if "## Words" not in text or "## Load" not in text:
        if errors is not None:
            errors.append("routes: SKILL.md must contain Words and Load sections")
        return []
    after_words = text.split("## Words", 1)[1]
    if "## Load" not in after_words:
        if errors is not None:
            errors.append("routes: Load must follow Words")
        return []
    section = after_words.split("## Load", 1)[0]
    rows: list[tuple[str, str]] = []
    for cells in table_rows(section, "Words", ["They say", "Do", "Read"], errors):
        links = TABLE_LINK_RE.findall(cells[2])
        root_owned = cells[2].strip().lower() == "this file"
        if (len(links) != 1 and not root_owned) or (links and root_owned):
            if errors is not None:
                errors.append(
                    f"routes: Words row must contain one target link or 'this file': {cells[0]}"
                )
        rows.append((cells[0], links[0] if links else ""))
    return rows


def validate_load_table(errors: list[str]) -> None:
    text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    match = re.search(r"(?ms)^## Load\s*$\n(.*?)(?=^## |\Z)", text)
    if not match:
        errors.append("routes: missing Load section")
        return
    rows = table_rows(match.group(1), "Load", ["Touching", "Read before editing"], errors)
    for cells in rows:
        if not TABLE_LINK_RE.search(cells[1]):
            errors.append(f"routes: Load row has no reference link: {cells[0]}")


def validate_routes(errors: list[str]) -> tuple[int, int]:
    rows = words_rows(errors)
    validate_load_table(errors)
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
            try:
                canonical = (ROOT / clean_link_target(target)).resolve().relative_to(
                    ROOT.resolve()
                ).as_posix()
            except (OSError, ValueError):
                errors.append(f"routes: target escapes or is missing: {target}")
            else:
                targets[canonical].append(phrase_cell)

    expected_jobs = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "references" / "jobs").glob("*.md")
    }
    expected_flows = {
        path.relative_to(ROOT).as_posix() for path in (ROOT / "references" / "flows").glob("*.md")
    }
    actual = set(targets)
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
    domains = {row.get("domain", "") for row in rows}
    unknown = sorted(domains - TELL_DOMAINS - {""})
    if unknown:
        errors.append(f"data/tells.csv: unknown domains: {', '.join(unknown)}")
    mapped = {domain for values in EXT_DOMAIN.values() for domain in values}
    unmatched = sorted(mapped - domains)
    if unmatched:
        errors.append(
            f"data/tells.csv: lookup.py domains with no rows: {', '.join(unmatched)}"
        )
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


def validate_portability(errors: list[str]) -> None:
    paths = [ROOT / "SKILL.md", *(ROOT / "references").rglob("*.md")]
    for path in paths:
        text = path.read_text(encoding="utf-8")
        for marker, label in FORBIDDEN_PORTABLE_TEXT.items():
            if marker in text:
                errors.append(f"{path.relative_to(ROOT)}: {label}: {marker}")


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
    try:
        runtime_files(ROOT)
    except ValueError as error:
        errors.append(f"runtime payload: {error}")
    docs = validate_docs(errors)
    jobs, flows = validate_routes(errors)
    validate_research(errors)
    tells = validate_tells(errors)
    validate_metadata(errors)
    validate_portability(errors)
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
