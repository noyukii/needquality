#!/usr/bin/env python3
"""Validate the NeedQuality skill set and its installable shape. Stdlib only."""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import unquote, urlsplit

from eval_schema import load_evals, validate_baseline, validate_evals
from runtime_payload import (
    SKILL_PREFIX,
    SKILLS_DIR,
    discover_skills,
    frontmatter,
    runtime_files,
    skill_metadata,
)

ROOT = Path(__file__).resolve().parent.parent
LINK_RE = re.compile(r"!?\[[^\]]*\]\(([^)]+)\)")
REFERENCE_LINK_RE = re.compile(r"!?\[([^\]]+)\]\[([^\]]*)\]")
REFERENCE_DEFINITION_RE = re.compile(r"(?m)^ {0,3}\[([^\]]+)\]:\s*(\S+)")
SKILL_MENTION_RE = re.compile(r"`(needquality-[a-z0-9-]+)`")
QUOTED_PHRASE_RE = re.compile(r'"([^"]+)"')
CONTRACT_PATH = ROOT / "shared" / "contract.md"
RESEARCH_SKILL = "needquality-research"
CLEANUP_SKILL = "needquality-cleanup"
DESCRIPTION_MIN_CHARS = 50
DESCRIPTION_MAX_CHARS = 1024
SKILL_MAX_LINES = 500
# Descriptions of every skill sit in context on every turn; keep the total
# under a budget (chars / 4 as a token estimate).
METADATA_TOKEN_BUDGET = 3200
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
    "Words table": "retired router vocabulary",
    "Load table": "retired router vocabulary",
    "$needquality": "retired router invocation",
}
OPENAI_METADATA_KEYS = (
    "display_name:",
    "short_description:",
    "default_prompt:",
    "allow_implicit_invocation:",
)


@dataclass
class SkillReport:
    name: str
    description: str
    root: Path
    files: dict[str, Path] = field(default_factory=dict)
    quoted_phrases: list[str] = field(default_factory=list)
    mentions: set[str] = field(default_factory=set)

    @property
    def markdown(self) -> list[Path]:
        return sorted(path for path in self.files.values() if path.suffix.lower() == ".md")


def strip_inline_code(block: str) -> str:
    output: list[str] = []
    index = 0
    while index < len(block):
        if block[index] != "`":
            output.append(block[index])
            index += 1
            continue
        end = index
        while end < len(block) and block[end] == "`":
            end += 1
        delimiter = block[index:end]
        closing = block.find(delimiter, end)
        while closing >= 0 and (
            (closing > 0 and block[closing - 1] == "`")
            or (
                closing + len(delimiter) < len(block)
                and block[closing + len(delimiter)] == "`"
            )
        ):
            closing = block.find(delimiter, closing + 1)
        if closing < 0:
            output.append(delimiter)
            index = end
            continue
        output.append("\n" * block[end:closing].count("\n"))
        index = closing + len(delimiter)
    return "".join(output)


def prose_without_code(text: str) -> str:
    blocks: list[str] = []
    current: list[str] = []
    fence: str | None = None

    def flush() -> None:
        if current:
            blocks.append("\n".join(current))
            current.clear()

    for line in text.splitlines():
        stripped = line.lstrip()
        marker = stripped[:3]
        if fence:
            if marker == fence:
                fence = None
            continue
        if marker in {"```", "~~~"}:
            flush()
            fence = marker
            continue
        if not stripped:
            flush()
            continue
        if current and re.match(
            r"^(?:#{1,6}\s|>|[-+*]\s|\d+[.)]\s|\|)",
            stripped,
        ):
            flush()
        current.append(line)
    flush()
    return "\n\n".join(strip_inline_code(block) for block in blocks)


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


def contract_text() -> str:
    return CONTRACT_PATH.read_text(encoding="utf-8").strip()


def validate_skill(skill_root: Path, errors: list[str]) -> SkillReport | None:
    label = skill_root.name
    try:
        fields = skill_metadata(skill_root)
        files = runtime_files(skill_root)
    except ValueError as error:
        errors.append(f"{label}: {error}")
        return None
    report = SkillReport(fields["name"], fields["description"], skill_root, files)
    skill_file = skill_root / "SKILL.md"
    text = skill_file.read_text(encoding="utf-8")

    description = report.description
    if len(description) < DESCRIPTION_MIN_CHARS:
        errors.append(f"{label}: description under {DESCRIPTION_MIN_CHARS} characters")
    if len(description) > DESCRIPTION_MAX_CHARS:
        errors.append(f"{label}: description over {DESCRIPTION_MAX_CHARS} characters")
    if "Use when" not in description:
        errors.append(f"{label}: description must state when to use it ('Use when ...')")
    report.quoted_phrases = [phrase.strip().lower() for phrase in QUOTED_PHRASE_RE.findall(description)]
    if len(text.splitlines()) > SKILL_MAX_LINES:
        errors.append(f"{label}: SKILL.md over {SKILL_MAX_LINES} lines")

    nested = [rel for rel in files if rel != "SKILL.md" and Path(rel).name == "SKILL.md"]
    for rel in nested:
        errors.append(f"{label}: nested SKILL.md is not allowed: {rel}")

    if CONTRACT_PATH.is_file() and contract_text() not in text:
        errors.append(f"{label}: SKILL.md does not contain the shared contract block verbatim")

    if not (skill_root / "agents" / "openai.yaml").is_file():
        errors.append(f"{label}: missing agents/openai.yaml")
    else:
        metadata = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")
        for key in OPENAI_METADATA_KEYS:
            if key not in metadata:
                errors.append(f"{label}: agents/openai.yaml missing {key}")

    skill_resolved = skill_root.resolve()
    linked_from_root: set[Path] = set()
    for path in report.markdown:
        doc_label = f"{label}/{path.relative_to(skill_root).as_posix()}"
        doc_text = path.read_text(encoding="utf-8")
        report.mentions.update(SKILL_MENTION_RE.findall(doc_text))
        for marker, reason in FORBIDDEN_PORTABLE_TEXT.items():
            if marker in doc_text:
                errors.append(f"{doc_label}: {reason}: {marker}")
        for target in document_targets(doc_text, errors, doc_label):
            try:
                resolved = local_target(path, target)
            except ValueError as error:
                errors.append(f"{doc_label}: {error}")
                continue
            if resolved is None:
                continue
            try:
                resolved.relative_to(skill_resolved)
            except ValueError:
                errors.append(f"{doc_label}: link escapes skill: {target}")
                continue
            if not resolved.exists():
                errors.append(f"{doc_label}: missing link: {target}")
                continue
            if not resolved.is_file():
                errors.append(f"{doc_label}: link is not a regular file: {target}")
                continue
            fragment = unquote(urlsplit(clean_link_target(target)).fragment)
            if fragment and resolved.suffix.lower() == ".md":
                if fragment not in heading_anchors(resolved.read_text(encoding="utf-8")):
                    errors.append(f"{doc_label}: missing fragment: {target}")
                    continue
            if path == skill_file:
                linked_from_root.add(resolved)

    # Every bundled file is one link away from SKILL.md so a host that reads
    # only the root still sees the whole skill.
    for rel, path in files.items():
        if rel == "SKILL.md" or rel.startswith("agents/"):
            continue
        if path.resolve() not in linked_from_root:
            errors.append(f"{label}: {rel} is not linked directly from SKILL.md")
    return report


def validate_skill_set(reports: list[SkillReport], errors: list[str]) -> int:
    names = {report.name for report in reports}
    owners: dict[str, list[str]] = defaultdict(list)
    for report in reports:
        for phrase in report.quoted_phrases:
            owners[phrase].append(report.name)
        for mention in sorted(report.mentions):
            if mention not in names:
                errors.append(f"{report.name}: mentions unknown skill {mention}")
    for phrase, skills in sorted(owners.items()):
        if len(skills) > 1:
            errors.append(f"trigger phrase {phrase!r} is claimed by {', '.join(sorted(skills))}")
    metadata_chars = sum(len(report.name) + len(report.description) for report in reports)
    metadata_tokens = metadata_chars // 4
    if metadata_tokens > METADATA_TOKEN_BUDGET:
        errors.append(
            f"skill metadata is ~{metadata_tokens} tokens; budget is {METADATA_TOKEN_BUDGET}"
        )
    return metadata_tokens


def validate_discovery(errors: list[str]) -> list[Path]:
    try:
        skills = discover_skills(ROOT)
    except ValueError as error:
        errors.append(f"discovery: {error}")
        return []
    allowed = {(skill / "SKILL.md").resolve() for skill in skills}
    for path in ROOT.rglob("SKILL.md"):
        if ".git" in path.parts:
            continue
        if path.resolve() not in allowed:
            errors.append(
                f"discovery: SKILL.md outside {SKILLS_DIR}/<{SKILL_PREFIX}*>/: "
                f"{path.relative_to(ROOT)}"
            )
    return skills


def validate_research(errors: list[str]) -> None:
    path = ROOT / SKILLS_DIR / RESEARCH_SKILL / "SKILL.md"
    if not path.is_file():
        errors.append(f"research: missing {RESEARCH_SKILL}/SKILL.md")
        return
    text = path.read_text(encoding="utf-8")
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


def lookup_extension_domains() -> dict[str, tuple[str, ...]]:
    """EXT_DOMAIN from the cleanup skill's bundled lookup script."""
    path = ROOT / SKILLS_DIR / CLEANUP_SKILL / "scripts" / "lookup.py"
    spec = importlib.util.spec_from_file_location("needquality_lookup", path)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.EXT_DOMAIN


def validate_tells(errors: list[str]) -> int:
    path = ROOT / SKILLS_DIR / CLEANUP_SKILL / "data" / "tells.csv"
    if not path.is_file():
        errors.append(f"tells: missing {CLEANUP_SKILL}/data/tells.csv")
        return 0
    with path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    required = {"id", "domain", "tell", "fix"}
    headers = set(rows[0]) if rows else set()
    if headers != required:
        errors.append("tells.csv: headers must be id, domain, tell, fix")
    ids = [row.get("id", "") for row in rows]
    if len(ids) != len(set(ids)):
        errors.append("tells.csv: duplicate id")
    if any(not all(row.get(key, "").strip() for key in required) for row in rows):
        errors.append("tells.csv: blank field")
    domains = {row.get("domain", "") for row in rows}
    unknown = sorted(domains - TELL_DOMAINS - {""})
    if unknown:
        errors.append(f"tells.csv: unknown domains: {', '.join(unknown)}")
    try:
        mapped = {domain for values in lookup_extension_domains().values() for domain in values}
    except (OSError, ValueError, AttributeError) as error:
        errors.append(f"tells.csv: cannot read lookup.py domains: {error}")
        return len(rows)
    unmatched = sorted(mapped - domains)
    if unmatched:
        errors.append(f"tells.csv: lookup.py domains with no rows: {', '.join(unmatched)}")
    return len(rows)


def validate_contract_source(errors: list[str]) -> None:
    if not CONTRACT_PATH.is_file():
        errors.append("contract: missing shared/contract.md")
        return
    if "## Contract" not in contract_text():
        errors.append("contract: shared/contract.md must start with a '## Contract' heading")


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
    elif "SKILL.md" not in files:
        errors.append("legacy manifest: missing the monolith root SKILL.md entry")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate NeedQuality")
    parser.add_argument("--stats", action="store_true", help="print inventory as JSON")
    args = parser.parse_args()
    errors: list[str] = []
    validate_contract_source(errors)
    skills = validate_discovery(errors)
    reports = [report for skill in skills if (report := validate_skill(skill, errors))]
    metadata_tokens = validate_skill_set(reports, errors)
    validate_research(errors)
    tells = validate_tells(errors)
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
    docs = sum(len(report.markdown) for report in reports)
    references = sum(len(report.files) - 1 for report in reports)
    stats = {
        "skills": len(reports),
        "docs": docs,
        "references": references,
        "tells": tells,
        "evals": evals,
        "metadata_tokens": metadata_tokens,
    }
    if args.stats:
        print(json.dumps(stats, sort_keys=True))
    else:
        print(
            f"valid: {len(reports)} skills, {docs} docs, {references} references, "
            f"{tells} tells, {evals} evals, ~{metadata_tokens} metadata tokens"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
