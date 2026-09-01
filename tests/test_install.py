from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import install

SKILL = "needquality-fix"
LEGACY = install.LEGACY_SKILL_NAME


def fresh_install(destination: Path, sources: dict[str, Path]) -> None:
    previous = install.previous_files(destination, SKILL)
    drift = install.inspect(destination, sources, previous)
    install.sync(destination, SKILL, sources, previous, drift, False)


def write_skill(root: Path, name: str, *, references: bool = True) -> Path:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    (skill / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: test\n---\n\n# Test\n", encoding="utf-8"
    )
    if references:
        (skill / "references").mkdir()
        (skill / "references" / "one.md").write_text("# One\n", encoding="utf-8")
    return skill


class InstallerTests(unittest.TestCase):
    def test_skill_sources_cover_every_bundled_skill(self) -> None:
        sources = install.skill_sources()
        self.assertIn(SKILL, sources)
        self.assertTrue(all(name.startswith(install.SKILL_PREFIX) for name in sources))
        for files in sources.values():
            self.assertIn("SKILL.md", files)
        self.assertIn("references/fix.md", sources[SKILL])

    def test_clean_install_then_check_has_no_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            sources = install.skill_sources()[SKILL]
            previous = install.previous_files(destination, SKILL)
            self.assertEqual(previous, {})
            drift = install.inspect(destination, sources, previous)
            self.assertTrue(drift.missing)
            self.assertEqual(install.sync(destination, SKILL, sources, previous, drift, False), [])
            current = install.previous_files(destination, SKILL)
            self.assertFalse(install.inspect(destination, sources, current).any())

    def test_modified_managed_file_is_preserved_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            sources = install.skill_sources()[SKILL]
            fresh_install(destination, sources)
            target = destination / "SKILL.md"
            target.write_text("local change\n", encoding="utf-8")
            current = install.previous_files(destination, SKILL)
            drift = install.inspect(destination, sources, current)
            self.assertIn("SKILL.md", drift.conflicts)
            self.assertTrue(install.sync(destination, SKILL, sources, current, drift, False))
            self.assertEqual(target.read_text(encoding="utf-8"), "local change\n")
            self.assertEqual(install.sync(destination, SKILL, sources, current, drift, True), [])
            self.assertEqual(target.read_bytes(), sources["SKILL.md"].read_bytes())

    def test_stale_manifest_file_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            sources = install.skill_sources()[SKILL]
            fresh_install(destination, sources)
            stale = destination / "old" / "entry.md"
            stale.parent.mkdir()
            stale.write_text("old\n", encoding="utf-8")
            manifest = destination / install.MANIFEST_NAME
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"]["old/entry.md"] = hashlib.sha256(stale.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            current = install.previous_files(destination, SKILL)
            drift = install.inspect(destination, sources, current)
            self.assertEqual(drift.stale, ["old/entry.md"])
            install.sync(destination, SKILL, sources, current, drift, False)
            self.assertFalse(stale.exists())

    def test_legacy_v1_install_is_retired_when_unmodified(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "skills"
            destination = root / LEGACY
            old = destination / "references" / "flows" / "demo" / "SKILL.md"
            old.parent.mkdir(parents=True)
            old.write_text("legacy\n", encoding="utf-8")
            legacy = base / "legacy.json"
            legacy.write_text(
                json.dumps({"format": 1, "files": {"references/flows/demo/SKILL.md": hashlib.sha256(old.read_bytes()).hexdigest()}}),
                encoding="utf-8",
            )
            with patch.object(install, "LEGACY_MANIFEST", legacy):
                self.assertEqual(install.retire_legacy(root, check=True, force=False), 1)
                self.assertTrue(old.exists())
                self.assertEqual(install.retire_legacy(root, check=False, force=False), 0)
            self.assertFalse(destination.exists())

    def test_legacy_v2_manifest_install_is_retired(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skills"
            destination = root / LEGACY
            old = destination / "SKILL.md"
            old.parent.mkdir(parents=True)
            old.write_text("monolith\n", encoding="utf-8")
            (destination / install.MANIFEST_NAME).write_text(
                json.dumps({"format": 1, "skill": LEGACY, "files": {"SKILL.md": install.digest(old)}}),
                encoding="utf-8",
            )
            self.assertEqual(install.retire_legacy(root, check=False, force=False), 0)
            self.assertFalse(destination.exists())

    def test_modified_legacy_entry_is_preserved_as_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "skills"
            destination = root / LEGACY
            old = destination / "references" / "flows" / "demo" / "SKILL.md"
            old.parent.mkdir(parents=True)
            original = b"legacy\n"
            old.write_bytes(b"local legacy change\n")
            legacy = base / "legacy.json"
            legacy.write_text(
                json.dumps({"format": 1, "files": {"references/flows/demo/SKILL.md": hashlib.sha256(original).hexdigest()}}),
                encoding="utf-8",
            )
            with patch.object(install, "LEGACY_MANIFEST", legacy):
                self.assertEqual(install.retire_legacy(root, check=False, force=True), 1)
            self.assertEqual(old.read_bytes(), b"local legacy change\n")

    def test_per_skill_destination_without_manifest_is_fresh(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            destination.mkdir(parents=True)
            (destination / "SKILL.md").write_text("unmanaged\n", encoding="utf-8")
            sources = install.skill_sources()[SKILL]
            previous = install.previous_files(destination, SKILL)
            self.assertEqual(previous, {})
            drift = install.inspect(destination, sources, previous)
            self.assertIn("SKILL.md", drift.conflicts)

    def test_force_preserves_modified_stale_file_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            sources = install.skill_sources()[SKILL]
            fresh_install(destination, sources)
            stale = destination / "old" / "entry.md"
            stale.parent.mkdir()
            stale.write_text("installed\n", encoding="utf-8")
            manifest = destination / install.MANIFEST_NAME
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"]["old/entry.md"] = hashlib.sha256(stale.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            manifest_before = manifest.read_bytes()
            stale.write_text("local change\n", encoding="utf-8")

            current = install.previous_files(destination, SKILL)
            drift = install.inspect(destination, sources, current)
            self.assertIn("old/entry.md", drift.conflicts)
            self.assertTrue(install.sync(destination, SKILL, sources, current, drift, True))
            self.assertEqual(stale.read_text(encoding="utf-8"), "local change\n")
            self.assertEqual(manifest.read_bytes(), manifest_before)

    def test_force_never_replaces_conflicting_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            sources = install.skill_sources()[SKILL]
            fresh_install(destination, sources)
            target = destination / "SKILL.md"
            target.unlink()
            target.mkdir()
            (target / "local.txt").write_text("keep\n", encoding="utf-8")
            current = install.previous_files(destination, SKILL)
            drift = install.inspect(destination, sources, current)
            self.assertTrue(install.sync(destination, SKILL, sources, current, drift, True))
            self.assertTrue((target / "local.txt").is_file())

    def test_source_payload_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "checkout"
            skill = write_skill(root, "needquality-demo", references=False)
            (skill / "references").symlink_to(Path(temp), target_is_directory=True)
            with patch.object(install, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    install.skill_sources()

    def test_checkout_directory_name_does_not_change_install_names(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality-main"
            write_skill(root, "needquality-demo")
            with patch.object(install, "ROOT", root):
                self.assertEqual(list(install.skill_sources()), ["needquality-demo"])

    def test_skill_name_must_match_directory_and_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "checkout"
            skill = write_skill(root, "needquality-demo")
            (skill / "SKILL.md").write_text(
                "---\nname: needquality-other\ndescription: test\n---\n", encoding="utf-8"
            )
            with patch.object(install, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "match its directory"):
                    install.skill_sources()
            (skill / "SKILL.md").write_text(
                "---\nname: demo\ndescription: test\n---\n", encoding="utf-8"
            )
            with patch.object(install, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "must start with"):
                    install.skill_sources()

    def test_sync_preflights_every_source_before_creating_destination(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination = root / "skills" / SKILL
            missing = root / "missing.txt"
            drift = install.Drift(missing=["missing.txt"])
            with self.assertRaisesRegex(ValueError, "source"):
                install.sync(destination, SKILL, {"missing.txt": missing}, {}, drift, False)
            self.assertFalse(destination.exists())

    def test_manifest_rejects_unsafe_managed_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "manifest.json"
            manifest.write_text(
                json.dumps({"format": 1, "skill": SKILL, "files": {"../outside": "abc"}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "unsafe managed path"):
                install.read_manifest(manifest, SKILL)

    def test_current_manifest_rejects_foreign_skill_and_invalid_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "manifest.json"
            for payload in (
                {"format": 1, "skill": "another-skill", "files": {"SKILL.md": "a" * 64}},
                {"format": 1, "skill": SKILL, "files": {"SKILL.md": "not-a-sha256"}},
            ):
                with self.subTest(payload=payload):
                    manifest.write_text(json.dumps(payload), encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "invalid manifest"):
                        install.read_manifest(manifest, SKILL)

    def test_legacy_manifest_rejects_unknown_format(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            manifest = Path(temp) / "legacy.json"
            manifest.write_text(
                json.dumps({"format": 999, "files": {"SKILL.md": "a" * 64}}),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "invalid manifest"):
                install.read_manifest(manifest, LEGACY, legacy=True)

    def test_manifest_hashes_the_staged_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.txt"
            source.write_text("version one\n", encoding="utf-8")
            destination = root / "skills" / SKILL
            real_copy = install.atomic_copy

            def mutate_source_after_staging(staged: Path, output: Path) -> None:
                source.write_text("version two\n", encoding="utf-8")
                real_copy(staged, output)

            with patch.object(install, "atomic_copy", side_effect=mutate_source_after_staging):
                install.sync(
                    destination,
                    SKILL,
                    {"file.txt": source},
                    {},
                    install.Drift(missing=["file.txt"]),
                    False,
                )
            manifest = install.read_manifest(destination / install.MANIFEST_NAME, SKILL)
            self.assertEqual(manifest["file.txt"], install.digest(destination / "file.txt"))

    def test_failed_fresh_install_removes_created_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.txt"
            source.write_text("content\n", encoding="utf-8")
            destination = root / "skills" / SKILL
            with patch.object(install, "atomic_manifest", side_effect=OSError("manifest failed")):
                with self.assertRaisesRegex(OSError, "manifest failed"):
                    install.sync(
                        destination,
                        SKILL,
                        {"file.txt": source},
                        {},
                        install.Drift(missing=["file.txt"]),
                        False,
                    )
            self.assertFalse(destination.exists())
            self.assertFalse(destination.parent.exists())

    def test_abandoned_transaction_is_recovered_before_install(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            transaction = destination / ".transaction.crash"
            backup = transaction / "backups" / "SKILL.md"
            backup.parent.mkdir(parents=True)
            backup.write_text("before\n", encoding="utf-8")
            (destination / "SKILL.md").write_text("partial\n", encoding="utf-8")
            manifest = destination / install.MANIFEST_NAME
            manifest.write_text("partial manifest\n", encoding="utf-8")
            (transaction / install.MANIFEST_NAME).write_text("previous manifest\n", encoding="utf-8")
            (transaction / "journal.json").write_text(
                json.dumps(
                    {
                        "replacements": ["SKILL.md"],
                        "removals": [],
                        "previously_existing": ["SKILL.md"],
                        "manifest_existed": True,
                    }
                ),
                encoding="utf-8",
            )
            install.recover_transactions(destination)
            self.assertEqual((destination / "SKILL.md").read_text(), "before\n")
            self.assertEqual(manifest.read_text(), "previous manifest\n")
            self.assertFalse(transaction.exists())

    def test_dry_run_does_not_recover_abandoned_transaction(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            transaction = Path(temp) / "skills" / SKILL / ".transaction.interrupted"
            transaction.mkdir(parents=True)
            (transaction / "journal.json").write_text(
                json.dumps(
                    {
                        "state": "preparing",
                        "replacements": [],
                        "removals": [],
                        "previously_existing": [],
                        "manifest_existed": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "requires recovery"):
                install.recover_transactions(transaction.parent, dry_run=True)
            self.assertTrue(transaction.is_dir())

    def test_recovery_preflights_every_backup_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            transaction = destination / ".transaction.incomplete"
            backup = transaction / "backups" / "SKILL.md"
            backup.parent.mkdir(parents=True)
            backup.write_text("before\n", encoding="utf-8")
            target = destination / "SKILL.md"
            target.write_text("partial\n", encoding="utf-8")
            (transaction / "journal.json").write_text(
                json.dumps(
                    {
                        "state": "ready",
                        "replacements": ["SKILL.md"],
                        "removals": [],
                        "previously_existing": ["SKILL.md"],
                        "manifest_existed": True,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "manifest backup"):
                install.recover_transactions(destination)
            self.assertEqual(target.read_text(), "partial\n")

    def test_recovery_rejects_symlinked_backup_tree_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            destination = root / "skills" / SKILL
            transaction = destination / ".transaction.redirected"
            outside = root / "outside"
            outside.mkdir(parents=True)
            (outside / "SKILL.md").write_text("outside\n", encoding="utf-8")
            transaction.mkdir(parents=True)
            (transaction / "backups").symlink_to(outside, target_is_directory=True)
            target = destination / "SKILL.md"
            target.write_text("partial\n", encoding="utf-8")
            (transaction / "journal.json").write_text(
                json.dumps(
                    {
                        "state": "ready",
                        "replacements": ["SKILL.md"],
                        "removals": [],
                        "previously_existing": ["SKILL.md"],
                        "manifest_existed": False,
                    }
                ),
                encoding="utf-8",
            )
            with self.assertRaisesRegex(ValueError, "symlink"):
                install.recover_transactions(destination)
            self.assertEqual(target.read_text(), "partial\n")

    def test_failed_rollback_preserves_transaction_for_recovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.txt"
            source.write_text("new\n", encoding="utf-8")
            destination = root / "skills" / SKILL
            destination.mkdir(parents=True)
            target = destination / "file.txt"
            target.write_text("old\n", encoding="utf-8")
            old_hash = install.digest(target)
            calls = 0
            real_copy = install.atomic_copy

            def fail_rollback(source_path: Path, output: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("rollback failed")
                real_copy(source_path, output)

            with (
                patch.object(install, "atomic_copy", side_effect=fail_rollback),
                patch.object(install, "atomic_manifest", side_effect=OSError("commit failed")),
            ):
                with self.assertRaisesRegex(OSError, "rollback failed"):
                    install.sync(
                        destination,
                        SKILL,
                        {"file.txt": source},
                        {"file.txt": old_hash},
                        install.Drift(changed=["file.txt"]),
                        False,
                    )
            self.assertTrue(any(destination.glob(".transaction.*")))

    def test_transaction_rolls_back_when_a_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / SKILL
            sources = install.skill_sources()[SKILL]
            fresh_install(destination, sources)
            targets = [destination / "SKILL.md", destination / "references" / "fix.md"]
            for index, target in enumerate(targets, 1):
                target.write_text(f"managed old {index}\n", encoding="utf-8")
            previous = install.previous_files(destination, SKILL)
            manifest = destination / install.MANIFEST_NAME
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            for target in targets:
                rel = target.relative_to(destination).as_posix()
                previous[rel] = hashlib.sha256(target.read_bytes()).hexdigest()
                payload["files"][rel] = previous[rel]
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            drift = install.inspect(destination, sources, previous)
            real_copy = install.atomic_copy
            calls = 0

            def fail_second_copy(source: Path, output: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected")
                real_copy(source, output)

            with patch.object(install, "atomic_copy", side_effect=fail_second_copy):
                with self.assertRaisesRegex(OSError, "injected"):
                    install.sync(destination, SKILL, sources, previous, drift, False)
            self.assertEqual(
                [target.read_text(encoding="utf-8") for target in targets],
                ["managed old 1\n", "managed old 2\n"],
            )
            self.assertEqual(install.previous_files(destination, SKILL), previous)

    def test_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            destination = base / "skills" / SKILL
            outside = base / "outside"
            outside.mkdir()
            destination.mkdir(parents=True)
            (destination / "references").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                install.inspect(destination, install.skill_sources()[SKILL], {})

    def test_symlinked_manifest_is_rejected_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            destination = base / "skills" / SKILL
            destination.mkdir(parents=True)
            outside = base / "outside.json"
            outside.write_text('{"files": {}}\n', encoding="utf-8")
            (destination / install.MANIFEST_NAME).symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "manifest is a symlink"):
                install.previous_files(destination, SKILL)

    def test_selected_roots_are_canonicalized_once_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            first = base / "first"
            second = base / "second"
            first.mkdir()
            second.mkdir()
            alias = base / "alias"
            alias.symlink_to(first, target_is_directory=True)
            args = argparse.Namespace(root=[str(alias), str(first)], all=False, platform=None)
            destinations = install.selected_destinations(args, [SKILL, "needquality-test"])
            self.assertEqual(destinations, [(SKILL, first / SKILL), ("needquality-test", first / "needquality-test")])
            alias.unlink()
            alias.symlink_to(second, target_is_directory=True)
            self.assertEqual(destinations[0], (SKILL, first / SKILL))

    def test_exact_destination_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "skills"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            (root / SKILL).symlink_to(outside, target_is_directory=True)
            args = argparse.Namespace(root=[str(root)], all=False, platform=None)
            with self.assertRaisesRegex(ValueError, "destination is a symlink"):
                install.selected_destinations(args, [SKILL])

    def test_default_roots_detect_per_skill_and_legacy_installs(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skills"
            self.assertFalse(install.has_needquality_install(root))
            (root / "needquality-test").mkdir(parents=True)
            self.assertTrue(install.has_needquality_install(root))
            legacy_root = Path(temp) / "legacy"
            (legacy_root / LEGACY).mkdir(parents=True)
            self.assertTrue(install.has_needquality_install(legacy_root))

    def test_skill_filter_accepts_short_names_and_rejects_unknown(self) -> None:
        available = ["needquality-fix", "needquality-test"]
        args = argparse.Namespace(skill=["fix", "needquality-test", "fix"])
        self.assertEqual(install.selected_skill_names(args, available), available)
        with self.assertRaisesRegex(ValueError, "unknown skill"):
            install.selected_skill_names(argparse.Namespace(skill=["nope"]), available)

    def test_cli_check_exit_codes_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skills"
            command = [sys.executable, str(SCRIPTS / "install.py"), "--root", str(root), "--skill", "fix"]
            dry = subprocess.run([*command, "--check"], capture_output=True, text=True, check=False)
            self.assertEqual(dry.returncode, 1)
            self.assertFalse((root / SKILL).exists())
            installed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertTrue((root / SKILL / "SKILL.md").is_file())
            self.assertFalse((root / "needquality-test").exists())
            clean = subprocess.run([*command, "--check"], capture_output=True, text=True, check=False)
            self.assertEqual(clean.returncode, 0, clean.stderr)

    def test_cli_installs_every_skill_and_retires_legacy(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skills"
            legacy = root / LEGACY
            legacy.mkdir(parents=True)
            (legacy / "SKILL.md").write_text("monolith\n", encoding="utf-8")
            (legacy / install.MANIFEST_NAME).write_text(
                json.dumps({"format": 1, "skill": LEGACY, "files": {"SKILL.md": install.digest(legacy / "SKILL.md")}}),
                encoding="utf-8",
            )
            command = [sys.executable, str(SCRIPTS / "install.py"), "--root", str(root)]
            installed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            self.assertFalse(legacy.exists())
            names = sorted(entry.name for entry in root.iterdir())
            self.assertEqual(names, sorted(install.skill_sources()))


if __name__ == "__main__":
    unittest.main()
