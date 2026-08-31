"""Shared schema and fixture validation for NeedQuality evaluations."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

TRACE_LABEL_RE = re.compile(r"^(?:job|flow|load):[a-z0-9-]+$")
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
CHECK_KINDS = {
    "path_exists",
    "path_absent",
    "file_contains",
    "file_not_contains",
    "response_contains",
    "response_not_contains",
    "trace_exact",
    "trace_absent",
    "tool_used",
    "tool_absent",
}
PATH_KINDS = {"path_exists", "path_absent", "file_contains", "file_not_contains"}
PATTERN_KINDS = {
    "file_contains",
    "file_not_contains",
    "response_contains",
    "response_not_contains",
}
TOOL_KINDS = {"tool_used", "tool_absent"}


def load_evals(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def safe_relative(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return not path.is_absolute() and ".." not in path.parts


def validate_evals(data: object, root: Path | None = None) -> list[str]:
    errors: list[str] = []
    if not isinstance(data, dict):
        return ["evaluation data must be an object"]
    if data.get("version") != 2:
        errors.append("version must be 2")
    cases = data.get("evals")
    if not isinstance(cases, list) or not cases:
        return [*errors, "evals must be a non-empty list"]

    ids: set[int] = set()
    names: set[str] = set()
    for case in cases:
        if not isinstance(case, dict):
            errors.append("each eval must be an object")
            continue
        cid = case.get("id")
        if not isinstance(cid, int) or isinstance(cid, bool):
            errors.append(f"invalid eval id: {cid!r}")
            continue
        if cid in ids:
            errors.append(f"duplicate eval id: {cid}")
        ids.add(cid)
        name = case.get("name")
        if not isinstance(name, str) or not SLUG_RE.fullmatch(name):
            errors.append(f"eval {cid}: name must be a lowercase hyphenated slug")
        elif name in names:
            errors.append(f"eval {cid}: duplicate name {name!r}")
        else:
            names.add(name)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"eval {cid}: missing prompt")
        if type(case.get("critical")) is not bool:
            errors.append(f"eval {cid}: critical must be boolean")

        files = case.get("files")
        if not isinstance(files, list):
            errors.append(f"eval {cid}: files must be a list")
        else:
            for rel in files:
                path = Path(rel) if isinstance(rel, str) else Path()
                if (
                    not safe_relative(rel)
                    or path.parts[:2] != ("evals", "files")
                ):
                    errors.append(f"eval {cid}: fixture is outside evals/files: {rel!r}")
                elif root is not None and not (root / path).is_file():
                    errors.append(f"eval {cid}: missing fixture {rel}")

        checks = case.get("checks")
        rubric = case.get("rubric")
        if not isinstance(checks, list):
            errors.append(f"eval {cid}: checks must be a list")
            checks = []
        if not isinstance(rubric, list):
            errors.append(f"eval {cid}: rubric must be a list")
            rubric = []
        if not checks and not rubric:
            errors.append(f"eval {cid}: at least one check or rubric item is required")

        item_ids: set[str] = set()
        for check in checks:
            if not isinstance(check, dict):
                errors.append(f"eval {cid}: each check must be an object")
                continue
            check_id = check.get("id")
            kind = check.get("kind")
            if not isinstance(check_id, str) or not SLUG_RE.fullmatch(check_id):
                errors.append(f"eval {cid}: invalid check id {check_id!r}")
            elif check_id in item_ids:
                errors.append(f"eval {cid}: duplicate assertion id {check_id!r}")
            else:
                item_ids.add(check_id)
            if kind not in CHECK_KINDS:
                errors.append(f"eval {cid}: unsupported check kind {kind!r}")
                continue
            if kind in PATH_KINDS and not safe_relative(check.get("path")):
                errors.append(f"eval {cid}: {check_id} requires a safe path")
            if kind in PATTERN_KINDS:
                pattern = check.get("pattern")
                if not isinstance(pattern, str) or not pattern:
                    errors.append(f"eval {cid}: {check_id} requires pattern")
                else:
                    try:
                        re.compile(pattern)
                    except re.error as error:
                        errors.append(f"eval {cid}: {check_id} invalid pattern: {error}")
            if kind == "trace_exact":
                parts = check.get("parts")
                if not isinstance(parts, list) or not parts:
                    errors.append(f"eval {cid}: {check_id} requires trace parts")
                elif not all(isinstance(part, str) and TRACE_LABEL_RE.fullmatch(part) for part in parts):
                    errors.append(f"eval {cid}: {check_id} has invalid trace parts")
                elif len(parts) != len(set(parts)):
                    errors.append(f"eval {cid}: {check_id} trace parts must be unique")
            if kind in TOOL_KINDS and not isinstance(check.get("tool"), str):
                errors.append(f"eval {cid}: {check_id} requires tool")

        for item in rubric:
            if not isinstance(item, dict):
                errors.append(f"eval {cid}: each rubric item must be an object")
                continue
            item_id = item.get("id")
            if not isinstance(item_id, str) or not SLUG_RE.fullmatch(item_id):
                errors.append(f"eval {cid}: invalid rubric id {item_id!r}")
            elif item_id in item_ids:
                errors.append(f"eval {cid}: duplicate assertion id {item_id!r}")
            else:
                item_ids.add(item_id)
            if not isinstance(item.get("text"), str) or not item["text"].strip():
                errors.append(f"eval {cid}: rubric {item_id!r} requires text")
    return errors


def case_files(root: Path, case: dict) -> list[tuple[Path, str]]:
    files: list[tuple[Path, str]] = []
    for rel in case.get("files", []):
        source = root / rel
        inside = Path(rel).relative_to("evals/files")
        files.append((source, str(Path(*inside.parts[1:]))))
    return files


def assertion_count(case: dict) -> int:
    return len(case.get("checks", [])) + len(case.get("rubric", []))


def validate_baseline(root: Path) -> list[str]:
    metadata_path = root / "evals" / "baseline.json"
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        return [f"evaluation baseline metadata: {error}"]
    archive_name = metadata.get("archive") if isinstance(metadata, dict) else None
    expected = metadata.get("sha256") if isinstance(metadata, dict) else None
    revision = metadata.get("revision") if isinstance(metadata, dict) else None
    if (
        metadata.get("format") != 1
        or not isinstance(archive_name, str)
        or Path(archive_name).name != archive_name
        or not isinstance(expected, str)
        or not re.fullmatch(r"[0-9a-f]{64}", expected)
        or not isinstance(revision, str)
        or not re.fullmatch(r"[0-9a-f]{40}", revision)
    ):
        return ["evaluation baseline metadata: invalid format"]
    archive = metadata_path.parent / archive_name
    try:
        actual = hashlib.sha256(archive.read_bytes()).hexdigest()
    except OSError as error:
        return [f"evaluation baseline archive: {error}"]
    return [] if actual == expected else ["evaluation baseline archive: SHA-256 mismatch"]
