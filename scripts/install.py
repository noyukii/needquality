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

from runtime_payload import runtime_files, skill_name as payload_skill_name

ROOT = Path(__file__).resolve().parent.parent
MANIFEST_NAME = ".needquality-manifest.json"
LEGACY_MANIFEST = ROOT / "data" / "legacy-v1-manifest.json"


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


def skill_name() -> str:
    return payload_skill_name(ROOT)


def source_files() -> dict[str, Path]:
    return runtime_files(ROOT)


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
    if manifest.is_symlink():
        raise ValueError(f"manifest is a symlink: {manifest}")
    if manifest.exists():
        if not manifest.is_file():
            raise ValueError(f"manifest is not a regular file: {manifest}")
        return read_manifest(manifest)
    if LEGACY_MANIFEST.is_symlink():
        raise ValueError(f"legacy manifest is a symlink: {LEGACY_MANIFEST}")
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
        "skill": skill_name(),
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
    replaceable_conflicts = {
        rel
        for rel in drift.conflicts
        if force
        and rel in previous
        and rel in sources
        and safe_path(destination, rel).is_file()
    }
    blocked = [rel for rel in drift.conflicts if rel not in replaceable_conflicts]
    if blocked:
        return blocked

    replacements = sorted({*drift.missing, *drift.changed, *replaceable_conflicts})
    removals = sorted(drift.stale)
    outputs = {rel: safe_path(destination, rel) for rel in (*replacements, *removals)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(parents=True, exist_ok=True)
    manifest = destination / MANIFEST_NAME

    with tempfile.TemporaryDirectory(
        dir=destination.parent, prefix=f".{destination.name}.transaction."
    ) as temp:
        transaction = Path(temp)
        staged = transaction / "staged"
        backups = transaction / "backups"
        existed: set[str] = set()
        for rel in replacements:
            stage = staged / rel
            stage.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(sources[rel], stage)
        for rel, output in outputs.items():
            if output.exists():
                if not output.is_file():
                    return [rel]
                backup = backups / rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output, backup)
                existed.add(rel)
        manifest_backup = transaction / MANIFEST_NAME
        manifest_existed = manifest.is_file()
        if manifest_existed:
            shutil.copy2(manifest, manifest_backup)

        try:
            for rel in replacements:
                atomic_copy(staged / rel, outputs[rel])
            for rel in removals:
                outputs[rel].unlink()
                prune_empty(outputs[rel].parent, destination)
            atomic_manifest(destination, sources)
        except BaseException:
            for rel, output in outputs.items():
                backup = backups / rel
                if rel in existed:
                    atomic_copy(backup, output)
                elif output.is_file() or output.is_symlink():
                    output.unlink()
                    prune_empty(output.parent, destination)
            if manifest_existed:
                atomic_copy(manifest_backup, manifest)
            elif manifest.exists():
                manifest.unlink()
            raise
    return []


def selected_destinations(args: argparse.Namespace) -> list[Path]:
    roots = standard_roots()
    name = skill_name()
    if args.root and (args.all or args.platform):
        raise ValueError("--root cannot be combined with --all or --platform")
    if args.root:
        selected = [Path(value).expanduser() for value in args.root]
    elif args.platform:
        selected = [roots[name] for name in args.platform]
    elif args.all:
        selected = list(roots.values())
    else:
        selected = [root for root in roots.values() if (root / name).is_dir()]

    destinations: list[Path] = []
    seen: set[Path] = set()
    for root in selected:
        selected_root = root.expanduser().absolute()
        unresolved_destination = selected_root / name
        if unresolved_destination.is_symlink():
            raise ValueError(f"destination is a symlink: {unresolved_destination}")
        canonical = selected_root.resolve(strict=False) / name
        if canonical in seen:
            continue
        seen.add(canonical)
        destinations.append(canonical)
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
