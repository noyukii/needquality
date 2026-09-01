"""Shared NeedQuality runtime payload and portable metadata rules."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

SKILLS_DIR = "skills"
SKILL_PREFIX = "needquality-"
SKILL_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
LEGACY_SKILL_NAME = "needquality"
IGNORED_NAMES = {".DS_Store", "__pycache__", ".git"}


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


def skill_metadata(skill_root: Path) -> dict[str, str]:
    skill = skill_root / "SKILL.md"
    try:
        text = skill.read_text(encoding="utf-8")
    except OSError as error:
        raise ValueError(f"cannot read skill {skill_root.name}: {error}") from error
    fields, errors = frontmatter(text)
    if errors:
        raise ValueError(f"invalid frontmatter in {skill_root.name}: " + "; ".join(errors))
    if set(fields) != {"name", "description"}:
        raise ValueError(
            f"{skill_root.name}: frontmatter keys must be exactly name and description"
        )
    name = fields.get("name", "")
    if not SKILL_NAME_RE.fullmatch(name):
        raise ValueError(f"invalid skill name: {name!r}")
    if not name.startswith(SKILL_PREFIX):
        raise ValueError(f"skill name must start with {SKILL_PREFIX!r}, got {name!r}")
    if name != skill_root.name:
        raise ValueError(
            f"skill name {name!r} must match its directory name {skill_root.name!r}"
        )
    if not fields.get("description"):
        raise ValueError(f"{name}: missing skill description")
    return fields


def skill_name(skill_root: Path) -> str:
    return skill_metadata(skill_root)["name"]


def discover_skills(repo_root: Path) -> list[Path]:
    skills_dir = repo_root / SKILLS_DIR
    if skills_dir.is_symlink():
        raise ValueError(f"skills directory is a symlink: {skills_dir}")
    if not skills_dir.is_dir():
        raise ValueError(f"missing skills directory: {skills_dir}")
    found: list[Path] = []
    for entry in sorted(skills_dir.iterdir()):
        if entry.name in IGNORED_NAMES:
            continue
        if entry.is_symlink():
            raise ValueError(f"skill directory is a symlink: {entry}")
        if not entry.is_dir():
            raise ValueError(f"unexpected entry in skills directory: {entry}")
        found.append(entry)
    if not found:
        raise ValueError(f"no skills found under {skills_dir}")
    return found


def _inside(root: Path, path: Path) -> None:
    try:
        path.resolve(strict=False).relative_to(root.resolve(strict=True))
    except (OSError, ValueError) as error:
        raise ValueError(f"payload path escapes skill: {path}") from error


def runtime_files(skill_root: Path) -> dict[str, Path]:
    skill_root = skill_root.absolute()
    if skill_root.is_symlink():
        raise ValueError(f"skill root is a symlink: {skill_root}")
    if not skill_root.is_dir():
        raise ValueError(f"skill root is not a directory: {skill_root}")
    skill_metadata(skill_root)
    files: dict[str, Path] = {}
    for current, directories, names in os.walk(skill_root, topdown=True, followlinks=False):
        parent = Path(current)
        for name in [*directories, *names]:
            path = parent / name
            if name in IGNORED_NAMES:
                continue
            if path.is_symlink():
                raise ValueError(f"payload contains symlink: {path}")
            _inside(skill_root, path)
        directories[:] = [name for name in directories if name not in IGNORED_NAMES]
        for name in names:
            path = parent / name
            if name in IGNORED_NAMES or path.suffix == ".pyc":
                continue
            if not path.is_file():
                raise ValueError(f"payload entry is not a regular file: {path}")
            files[path.relative_to(skill_root).as_posix()] = path
    if "SKILL.md" not in files:
        raise ValueError(f"missing SKILL.md in {skill_root}")
    return files


def payload_hash(skill_root: Path) -> str:
    digest = hashlib.sha256()
    for rel, path in sorted(runtime_files(skill_root).items()):
        digest.update(rel.encode("utf-8"))
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()
