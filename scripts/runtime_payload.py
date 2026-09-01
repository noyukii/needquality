"""Shared NeedQuality runtime payload and portable metadata rules."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

PAYLOAD = (
    "SKILL.md",
    "references",
    "data/tells.csv",
    "scripts/lookup.py",
    "agents/openai.yaml",
)
OPTIONAL_PAYLOAD = {"agents/openai.yaml"}
EXPECTED_SKILL_NAME = "needquality"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def frontmatter(text: str) -> tuple[dict[str, str], list[str]]:
    if not text.startswith("---\n"):
        return {}, ["missing YAML frontmatter"]
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
            folded = value == ">"
            continuation: list[str] = []
            index += 1
            while index < len(lines) and lines[index].startswith(("  ", "\t")):
                continuation.append(lines[index].strip())
                index += 1
            value = " ".join(continuation) if folded else "\n".join(continuation)
        else:
            index += 1
        fields[key] = value.strip('"\'')
    return fields, errors


def skill_metadata(root: Path) -> dict[str, str]:
    skill = root / "SKILL.md"
    try:
        text = skill.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot read root skill: {error}") from error
    fields, errors = frontmatter(text)
    if errors:
        raise ValueError("invalid root frontmatter: " + "; ".join(errors))
    if set(fields) != {"name", "description"}:
        raise ValueError("root frontmatter keys must be exactly name and description")
    name = fields.get("name", "")
    if not SKILL_NAME_RE.fullmatch(name):
        raise ValueError(f"invalid skill name: {name!r}")
    if name != EXPECTED_SKILL_NAME:
        raise ValueError(f"root skill name must be {EXPECTED_SKILL_NAME!r}, got {name!r}")
    if not fields.get("description"):
        raise ValueError("missing skill description")
    return fields


def skill_name(root: Path) -> str:
    return skill_metadata(root)["name"]


def _inside(root: Path, path: Path) -> None:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ValueError(f"payload path escapes skill: {path}") from error


def _tree_files(root: Path, source: Path) -> list[Path]:
    files: list[Path] = []
    for current, directories, names in os.walk(source, topdown=True, followlinks=False):
        parent = Path(current)
        for name in [*directories, *names]:
            path = parent / name
            if path.is_symlink():
                raise ValueError(f"payload contains symlink: {path}")
            _inside(root, path)
        directories[:] = [
            name for name in directories if name != "__pycache__" and name != ".git"
        ]
        for name in names:
            path = parent / name
            if name == ".DS_Store" or path.suffix == ".pyc":
                continue
            if not path.is_file():
                raise ValueError(f"payload entry is not a regular file: {path}")
            files.append(path)
    return files


def runtime_files(root: Path, *, require_metadata: bool = True) -> dict[str, Path]:
    root = root.absolute()
    if root.is_symlink():
        raise ValueError(f"skill root is a symlink: {root}")
    if not root.is_dir():
        raise ValueError(f"skill root is not a directory: {root}")
    skill_metadata(root)
    files: dict[str, Path] = {}
    for rel in PAYLOAD:
        source = root / rel
        if source.is_symlink():
            raise ValueError(f"payload contains symlink: {source}")
        if not source.exists():
            if not require_metadata and rel in OPTIONAL_PAYLOAD:
                continue
            raise ValueError(f"missing payload: {rel}")
        _inside(root, source)
        candidates = _tree_files(root, source) if source.is_dir() else [source]
        for path in candidates:
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"payload entry is not a regular file: {path}")
            _inside(root, path)
            files[path.relative_to(root).as_posix()] = path
    if not files:
        raise ValueError("no payload files found")
    return files


def payload_hash(root: Path, *, require_metadata: bool = True) -> str:
    digest = hashlib.sha256()
    for rel, path in sorted(runtime_files(root, require_metadata=require_metadata).items()):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
