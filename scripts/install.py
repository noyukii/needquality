#!/usr/bin/env python3
"""Install or check NeedQuality in supported agent skill roots. Stdlib only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
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


def managed_relative(rel: str) -> Path:
    relative = Path(rel)
    if not rel or relative.is_absolute() or ".." in relative.parts:
        raise ValueError(f"unsafe managed path: {rel}")
    return relative


def read_manifest(path: Path, *, legacy: bool = False) -> dict[str, str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"cannot read manifest {path}: {error}") from error
    files = payload.get("files") if isinstance(payload, dict) else None
    if not isinstance(files, dict) or not all(
        isinstance(rel, str) and isinstance(value, str) for rel, value in files.items()
    ):
        raise ValueError(f"invalid manifest: {path}")
    for rel in files:
        managed_relative(rel)
    if not all(re.fullmatch(r"[0-9a-f]{64}", value) for value in files.values()):
        raise ValueError(f"invalid manifest hashes: {path}")
    if legacy and payload.get("format", 1) != 1:
        raise ValueError(f"invalid manifest format: {path}")
    if legacy and "skill" in payload and payload.get("skill") != skill_name():
        raise ValueError(f"invalid manifest identity: {path}")
    if not legacy and (
        payload.get("format") != 1 or payload.get("skill") != skill_name()
    ):
        raise ValueError(f"invalid manifest identity: {path}")
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
    return read_manifest(LEGACY_MANIFEST, legacy=True)


def safe_path(destination: Path, rel: str) -> Path:
    relative = managed_relative(rel)
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


def preflight_sync(
    destination: Path,
    sources: dict[str, Path],
    previous: dict[str, str],
    drift: Drift,
    force: bool,
) -> tuple[list[str], list[str], list[str], dict[str, Path]]:
    if destination.is_symlink():
        raise ValueError(f"destination is a symlink: {destination}")
    if destination.exists() and not destination.is_dir():
        raise ValueError(f"destination is not a directory: {destination}")
    manifest = destination / MANIFEST_NAME
    if manifest.is_symlink():
        raise ValueError(f"manifest is a symlink: {manifest}")
    if manifest.exists() and not manifest.is_file():
        raise ValueError(f"manifest is not a regular file: {manifest}")

    for rel, source in sources.items():
        managed_relative(rel)
        if source.is_symlink() or not source.is_file():
            raise ValueError(f"source is not a regular file: {source}")
        digest(source)
    for rel in previous:
        managed_relative(rel)

    replaceable_conflicts = {
        rel
        for rel in drift.conflicts
        if force
        and rel in previous
        and rel in sources
        and safe_path(destination, rel).is_file()
    }
    blocked = sorted(rel for rel in drift.conflicts if rel not in replaceable_conflicts)
    replacements = sorted({*drift.missing, *drift.changed, *replaceable_conflicts})
    removals = sorted(drift.stale)
    outputs = {
        rel: safe_path(destination, rel)
        for rel in (*replacements, *removals)
    }
    return blocked, replacements, removals, outputs


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


def recover_transactions(destination: Path, *, dry_run: bool = False) -> None:
    if not destination.exists():
        return
    if destination.is_symlink() or not destination.is_dir():
        raise ValueError(f"invalid transaction destination: {destination}")
    for transaction in sorted(destination.glob(".transaction.*")):
        if dry_run:
            raise ValueError(f"abandoned transaction requires recovery: {transaction}")
        if transaction.is_symlink() or not transaction.is_dir():
            raise ValueError(f"invalid abandoned transaction: {transaction}")
        symlink = next(
            (path for path in transaction.rglob("*") if path.is_symlink()),
            None,
        )
        if symlink:
            raise ValueError(f"abandoned transaction contains symlink: {symlink}")
        journal_path = transaction / "journal.json"
        try:
            journal = json.loads(journal_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise ValueError(
                f"cannot recover abandoned transaction {transaction}: {error}"
            ) from error
        if not isinstance(journal, dict):
            raise ValueError(f"invalid abandoned transaction journal: {journal_path}")
        state = journal.get("state", "ready")
        if state == "preparing":
            shutil.rmtree(transaction)
            continue
        replacements = journal.get("replacements")
        removals = journal.get("removals")
        existed = journal.get("previously_existing")
        manifest_existed = journal.get("manifest_existed")
        if (
            state != "ready"
            or not isinstance(replacements, list)
            or not isinstance(removals, list)
            or not isinstance(existed, list)
            or type(manifest_existed) is not bool
            or not all(isinstance(rel, str) for rel in [*replacements, *removals, *existed])
        ):
            raise ValueError(f"invalid abandoned transaction journal: {journal_path}")
        changed = set(replacements) | set(removals)
        existing = set(existed)
        if not existing <= changed:
            raise ValueError(f"invalid abandoned transaction journal: {journal_path}")
        recovery: list[tuple[str, Path, Path]] = []
        for rel in sorted(changed):
            managed_relative(rel)
            output = safe_path(destination, rel)
            backup = transaction / "backups" / rel
            if rel in existing:
                if backup.is_symlink() or not backup.is_file():
                    raise ValueError(f"missing transaction backup: {backup}")
            elif output.exists() and not output.is_file() and not output.is_symlink():
                raise ValueError(f"transaction output is not a file: {output}")
            recovery.append((rel, output, backup))
        manifest = destination / MANIFEST_NAME
        manifest_backup = transaction / MANIFEST_NAME
        if manifest.is_symlink():
            raise ValueError(f"transaction manifest is a symlink: {manifest}")
        if manifest_existed:
            if manifest_backup.is_symlink() or not manifest_backup.is_file():
                raise ValueError(f"missing transaction manifest backup: {manifest_backup}")
        elif manifest.exists() and not manifest.is_file() and not manifest.is_symlink():
            raise ValueError(f"transaction manifest is not a regular file: {manifest}")
        for rel, output, backup in recovery:
            if rel in existing:
                atomic_copy(backup, output)
            elif output.is_file() or output.is_symlink():
                output.unlink()
                prune_empty(output.parent, destination)
        if manifest_existed:
            atomic_copy(manifest_backup, manifest)
        elif manifest.is_file() or manifest.is_symlink():
            manifest.unlink()
        shutil.rmtree(transaction)


def sync(
    destination: Path,
    sources: dict[str, Path],
    previous: dict[str, str],
    drift: Drift,
    force: bool,
) -> list[str]:
    blocked, replacements, removals, outputs = preflight_sync(
        destination, sources, previous, drift, force
    )
    if blocked:
        return blocked

    created: list[Path] = []
    current = destination
    while not current.exists():
        created.append(current)
        current = current.parent
    transaction: Path | None = None
    mutation_started = False
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.mkdir(parents=True, exist_ok=True)
        manifest = destination / MANIFEST_NAME
        destination_device = destination.stat().st_dev
        for rel, output in outputs.items():
            existing_parent = output.parent
            while not existing_parent.exists():
                existing_parent = existing_parent.parent
            if existing_parent.stat().st_dev != destination_device:
                raise ValueError(f"managed path is on another filesystem: {rel}")

        transaction = Path(tempfile.mkdtemp(dir=destination, prefix=".transaction."))
        if transaction.stat().st_dev != destination_device:
            raise ValueError(
                "transaction staging is not on the destination filesystem"
            )
        staged = transaction / "staged"
        backups = transaction / "backups"
        journal_path = transaction / "journal.json"
        journal_path.write_text(
            json.dumps(
                {
                    "state": "preparing",
                    "replacements": replacements,
                    "removals": removals,
                    "previously_existing": [],
                    "manifest_existed": False,
                },
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        staged_sources: dict[str, Path] = {}
        for rel, source in sources.items():
            stage = staged / rel
            stage.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, stage)
            staged_sources[rel] = stage
        existed: set[str] = set()
        for rel, output in outputs.items():
            if output.exists():
                if not output.is_file():
                    raise ValueError(f"transaction output is not a file: {output}")
                backup = backups / rel
                backup.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(output, backup)
                existed.add(rel)
        manifest_backup = transaction / MANIFEST_NAME
        manifest_existed = manifest.is_file()
        if manifest_existed:
            shutil.copy2(manifest, manifest_backup)
        journal_path.write_text(
            json.dumps(
                {
                    "state": "ready",
                    "replacements": replacements,
                    "removals": removals,
                    "previously_existing": sorted(existed),
                    "manifest_existed": manifest_existed,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )

        mutation_started = True
        try:
            for rel in replacements:
                atomic_copy(staged_sources[rel], outputs[rel])
            for rel in removals:
                outputs[rel].unlink()
                prune_empty(outputs[rel].parent, destination)
            atomic_manifest(destination, staged_sources)
        except BaseException:
            try:
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
            except BaseException:
                raise
            shutil.rmtree(transaction)
            transaction = None
            raise
        shutil.rmtree(transaction)
        transaction = None
    except BaseException:
        if transaction and transaction.exists() and not mutation_started:
            shutil.rmtree(transaction)
        for path in created:
            try:
                path.rmdir()
            except OSError:
                pass
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
            recover_transactions(destination, dry_run=args.check)
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
