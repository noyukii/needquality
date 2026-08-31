#!/usr/bin/env python3
"""Install or check NeedQuality in supported agent skill roots. Stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = ROOT.name
MANIFEST_NAME = ".needquality-manifest.json"
LEGACY_MANIFEST = ROOT / "data" / "legacy-v1-manifest.json"
PAYLOAD = (
    "SKILL.md",
    "references",
    "data/tells.csv",
    "scripts/lookup.py",
    "agents/openai.yaml",
)


@dataclass
class Drift:
    missing: list[str] = field(default_factory=list)
    changed: list[str] = field(default_factory=list)
    stale: list[str] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)

    def any(self) -> bool:
        return any((self.missing, self.changed, self.stale, self.conflicts))


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def standard_roots() -> dict[str, Path]:
    codex_home = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
    return {
        "agents": Path.home() / ".agents" / "skills",
        "claude": Path.home() / ".claude" / "skills",
        "cursor": Path.home() / ".cursor" / "skills",
        "codex": codex_home / "skills",
    }


def source_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for rel in PAYLOAD:
        source = ROOT / rel
        if not source.exists():
            raise ValueError(f"missing payload: {rel}")
        candidates = (
            sorted(path for path in source.rglob("*") if path.is_file())
            if source.is_dir()
            else [source]
        )
        for path in candidates:
            if path.name == ".DS_Store" or "__pycache__" in path.parts:
                continue
            files[path.relative_to(ROOT).as_posix()] = path
    if not files:
        raise ValueError("no payload files found")
    return files


def read_manifest(path: Path) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read manifest {path}: {error}") from error
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, dict) or not all(
        isinstance(rel, str) and isinstance(value, str) for rel, value in files.items()
    ):
        raise ValueError(f"invalid manifest: {path}")
    return files


def previous_files(destination: Path) -> dict[str, str]:
    manifest = destination / MANIFEST_NAME
    if manifest.is_file():
        return read_manifest(manifest)
    return read_manifest(LEGACY_MANIFEST)


def safe_path(destination: Path, rel: str) -> Path:
    relative = Path(rel)
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe managed path: {rel}")
    if destination.is_symlink():
        raise ValueError(f"destination is a symlink: {destination}")
    output = destination / relative
    parent = output.parent
    while parent != destination.parent:
        if parent.exists() and parent.is_symlink():
            raise ValueError(f"managed path crosses symlink: {output}")
        if parent == destination:
            break
        parent = parent.parent
    if output.is_symlink():
        raise ValueError(f"managed file is a symlink: {output}")
    try:
        output.resolve(strict=False).relative_to(destination.resolve(strict=False))
    except ValueError as error:
        raise ValueError(f"managed path escapes destination: {output}") from error
    return output


def inspect(destination: Path, sources: dict[str, Path], previous: dict[str, str]) -> Drift:
    drift = Drift()
    for rel, source in sources.items():
        output = safe_path(destination, rel)
        if not output.exists():
            drift.missing.append(rel)
            continue
        if not output.is_file():
            drift.conflicts.append(rel)
            continue
        current = digest(output)
        if current == digest(source):
            continue
        if previous.get(rel) == current:
            drift.changed.append(rel)
        else:
            drift.conflicts.append(rel)

    for rel, old_hash in previous.items():
        if rel in sources:
            continue
        output = safe_path(destination, rel)
        if not output.exists():
            continue
        if output.is_file() and digest(output) == old_hash:
            drift.stale.append(rel)
        else:
            drift.conflicts.append(rel)
    return drift


def atomic_copy(source: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        dir=output.parent, prefix=f".{output.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()


def atomic_manifest(destination: Path, sources: dict[str, Path]) -> None:
    payload = {
        "format": 1,
        "skill": SKILL_NAME,
        "files": {rel: digest(path) for rel, path in sorted(sources.items())},
    }
    destination.mkdir(parents=True, exist_ok=True)
    output = destination / MANIFEST_NAME
    with tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        dir=destination,
        prefix=f".{MANIFEST_NAME}.",
        delete=False,
    ) as handle:
        temporary = Path(handle.name)
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")
    try:
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()


def prune_empty(parent: Path, destination: Path) -> None:
    while parent != destination and parent.is_dir():
        try:
            parent.rmdir()
        except OSError:
            return
        parent = parent.parent


def sync(
    destination: Path,
    sources: dict[str, Path],
    previous: dict[str, str],
    drift: Drift,
    force: bool,
) -> list[str]:
    unmanaged = [rel for rel in drift.conflicts if rel not in previous]
    if drift.conflicts and (not force or unmanaged):
        return unmanaged or drift.conflicts

    for rel in (*drift.missing, *drift.changed):
        atomic_copy(sources[rel], safe_path(destination, rel))
    for rel in drift.conflicts:
        output = safe_path(destination, rel)
        if rel in sources:
            atomic_copy(sources[rel], output)
        elif output.is_file():
            output.unlink()
            prune_empty(output.parent, destination)
    for rel in drift.stale:
        output = safe_path(destination, rel)
        output.unlink()
        prune_empty(output.parent, destination)
    atomic_manifest(destination, sources)
    return []


def selected_destinations(args: argparse.Namespace) -> list[Path]:
    roots = standard_roots()
    if args.root and (args.all or args.platform):
        raise ValueError("--root cannot be combined with --all or --platform")
    if args.root:
        selected = [Path(value).expanduser() for value in args.root]
    elif args.platform:
        selected = [roots[name] for name in args.platform]
    elif args.all:
        selected = list(roots.values())
    else:
        selected = [root for root in roots.values() if (root / SKILL_NAME).is_dir()]

    destinations: list[Path] = []
    seen: set[Path] = set()
    for root in selected:
        destination = root.expanduser().absolute() / SKILL_NAME
        canonical = destination.resolve(strict=False)
        if canonical in seen:
            continue
        seen.add(canonical)
        destinations.append(destination)
    return destinations


def print_drift(destination: Path, drift: Drift) -> None:
    for label in ("missing", "changed", "stale", "conflicts"):
        singular = "conflict" if label == "conflicts" else label.removesuffix("s")
        for rel in getattr(drift, label):
            print(f"{singular}: {destination / rel}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install or check the NeedQuality skill")
    parser.add_argument("--check", action="store_true", help="report drift, write nothing")
    parser.add_argument("--all", action="store_true", help="install into every standard root")
    parser.add_argument(
        "--platform",
        action="append",
        choices=tuple(standard_roots()),
        help="install into one standard root",
    )
    parser.add_argument("--root", action="append", help="install into a custom skills root")
    parser.add_argument("--force", action="store_true", help="replace modified manifest-managed files")
    args = parser.parse_args()
    if args.check and args.force:
        parser.error("--check cannot be combined with --force")

    try:
        sources = source_files()
        destinations = selected_destinations(args)
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2
    if not destinations:
        print("no NeedQuality install found; use --all, --platform, or --root", file=sys.stderr)
        return 2

    exit_code = 0
    for destination in destinations:
        try:
            previous = previous_files(destination)
            drift = inspect(destination, sources, previous)
            print_drift(destination, drift)
            if args.check:
                if drift.any():
                    exit_code = 1
                continue
            blocked = sync(destination, sources, previous, drift, args.force)
            if blocked:
                print(f"conflicts left unchanged in {destination}", file=sys.stderr)
                exit_code = 1
                continue
            count = sum(len(getattr(drift, label)) for label in ("missing", "changed", "stale", "conflicts"))
            print(f"synced {count} file(s) to {destination}")
        except (OSError, ValueError) as error:
            print(f"{destination}: {error}", file=sys.stderr)
            exit_code = 2

    if args.check:
        print(f"checked {len(destinations)} destination(s)")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
