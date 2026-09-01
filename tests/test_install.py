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


class InstallerTests(unittest.TestCase):
    def test_clean_install_then_check_has_no_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / "needquality"
            sources = install.source_files()
            previous = install.previous_files(destination)
            drift = install.inspect(destination, sources, previous)
            self.assertTrue(drift.missing)
            self.assertEqual(install.sync(destination, sources, previous, drift, False), [])
            current = install.previous_files(destination)
            self.assertFalse(install.inspect(destination, sources, current).any())

    def test_modified_managed_file_is_preserved_without_force(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / "needquality"
            sources = install.source_files()
            previous = install.previous_files(destination)
            install.sync(destination, sources, previous, install.inspect(destination, sources, previous), False)
            target = destination / "SKILL.md"
            target.write_text("local change\n", encoding="utf-8")
            current = install.previous_files(destination)
            drift = install.inspect(destination, sources, current)
            self.assertIn("SKILL.md", drift.conflicts)
            self.assertTrue(install.sync(destination, sources, current, drift, False))
            self.assertEqual(target.read_text(encoding="utf-8"), "local change\n")
            self.assertEqual(install.sync(destination, sources, current, drift, True), [])
            self.assertEqual(target.read_bytes(), sources["SKILL.md"].read_bytes())

    def test_stale_manifest_file_is_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / "needquality"
            sources = install.source_files()
            previous = install.previous_files(destination)
            install.sync(destination, sources, previous, install.inspect(destination, sources, previous), False)
            stale = destination / "old" / "entry.md"
            stale.parent.mkdir()
            stale.write_text("old\n", encoding="utf-8")
            manifest = destination / install.MANIFEST_NAME
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"]["old/entry.md"] = hashlib.sha256(stale.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            current = install.previous_files(destination)
            drift = install.inspect(destination, sources, current)
            self.assertEqual(drift.stale, ["old/entry.md"])
            install.sync(destination, sources, current, drift, False)
            self.assertFalse(stale.exists())

    def test_legacy_entry_is_removed_only_when_unmodified(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            destination = base / "skills" / "needquality"
            old = destination / "references" / "flows" / "demo" / "SKILL.md"
            old.parent.mkdir(parents=True)
            old.write_text("legacy\n", encoding="utf-8")
            legacy = base / "legacy.json"
            legacy.write_text(
                json.dumps({"format": 1, "files": {"references/flows/demo/SKILL.md": hashlib.sha256(old.read_bytes()).hexdigest()}}),
                encoding="utf-8",
            )
            with patch.object(install, "LEGACY_MANIFEST", legacy):
                previous = install.previous_files(destination)
                sources = install.source_files()
                drift = install.inspect(destination, sources, previous)
                self.assertIn("references/flows/demo/SKILL.md", drift.stale)
                install.sync(destination, sources, previous, drift, False)
            self.assertFalse(old.exists())

    def test_modified_legacy_entry_is_preserved_as_conflict(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            destination = base / "skills" / "needquality"
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
                previous = install.previous_files(destination)
                sources = install.source_files()
                drift = install.inspect(destination, sources, previous)
                self.assertIn("references/flows/demo/SKILL.md", drift.conflicts)
                self.assertTrue(install.sync(destination, sources, previous, drift, False))
            self.assertEqual(old.read_bytes(), b"local legacy change\n")

    def test_force_preserves_modified_stale_file_and_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / "needquality"
            sources = install.source_files()
            previous = install.previous_files(destination)
            install.sync(destination, sources, previous, install.inspect(destination, sources, previous), False)
            stale = destination / "old" / "entry.md"
            stale.parent.mkdir()
            stale.write_text("installed\n", encoding="utf-8")
            manifest = destination / install.MANIFEST_NAME
            payload = json.loads(manifest.read_text(encoding="utf-8"))
            payload["files"]["old/entry.md"] = hashlib.sha256(stale.read_bytes()).hexdigest()
            manifest.write_text(json.dumps(payload), encoding="utf-8")
            manifest_before = manifest.read_bytes()
            stale.write_text("local change\n", encoding="utf-8")

            current = install.previous_files(destination)
            drift = install.inspect(destination, sources, current)
            self.assertIn("old/entry.md", drift.conflicts)
            self.assertTrue(install.sync(destination, sources, current, drift, True))
            self.assertEqual(stale.read_text(encoding="utf-8"), "local change\n")
            self.assertEqual(manifest.read_bytes(), manifest_before)

    def test_force_never_replaces_conflicting_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / "needquality"
            sources = install.source_files()
            previous = install.previous_files(destination)
            install.sync(destination, sources, previous, install.inspect(destination, sources, previous), False)
            target = destination / "SKILL.md"
            target.unlink()
            target.mkdir()
            (target / "local.txt").write_text("keep\n", encoding="utf-8")
            current = install.previous_files(destination)
            drift = install.inspect(destination, sources, current)
            self.assertTrue(install.sync(destination, sources, current, drift, True))
            self.assertTrue((target / "local.txt").is_file())

    def test_source_payload_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "renamed-checkout"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: needquality\ndescription: test\n---\n", encoding="utf-8"
            )
            (root / "references").symlink_to(Path(temp), target_is_directory=True)
            (root / "data").mkdir()
            (root / "data" / "tells.csv").write_text("id,domain,tell,fix\n", encoding="utf-8")
            (root / "scripts").mkdir()
            (root / "scripts" / "lookup.py").write_text("", encoding="utf-8")
            (root / "agents").mkdir()
            (root / "agents" / "openai.yaml").write_text("", encoding="utf-8")
            with patch.object(install, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "symlink"):
                    install.source_files()

    def test_checkout_directory_name_does_not_change_install_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality-main"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: needquality\ndescription: test\n---\n", encoding="utf-8"
            )
            for rel in ("references", "data", "scripts", "agents"):
                (root / rel).mkdir()
            (root / "references" / "one.md").write_text("# One\n", encoding="utf-8")
            (root / "data" / "tells.csv").write_text("id,domain,tell,fix\n", encoding="utf-8")
            (root / "scripts" / "lookup.py").write_text("", encoding="utf-8")
            (root / "agents" / "openai.yaml").write_text("", encoding="utf-8")
            with patch.object(install, "ROOT", root):
                self.assertEqual(install.skill_name(), "needquality")

    def test_transaction_rolls_back_when_a_copy_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            destination = Path(temp) / "skills" / "needquality"
            sources = install.source_files()
            previous = install.previous_files(destination)
            install.sync(destination, sources, previous, install.inspect(destination, sources, previous), False)
            targets = [destination / "SKILL.md", destination / "references" / "jobs" / "a11y.md"]
            for index, target in enumerate(targets, 1):
                target.write_text(f"managed old {index}\n", encoding="utf-8")
            previous = install.previous_files(destination)
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
                    install.sync(destination, sources, previous, drift, False)
            self.assertEqual(
                [target.read_text(encoding="utf-8") for target in targets],
                ["managed old 1\n", "managed old 2\n"],
            )
            self.assertEqual(install.previous_files(destination), previous)

    def test_symlink_escape_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            destination = base / "skills" / "needquality"
            outside = base / "outside"
            outside.mkdir()
            destination.mkdir(parents=True)
            (destination / "references").symlink_to(outside, target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                install.inspect(destination, install.source_files(), {})

    def test_symlinked_manifest_is_rejected_before_reading(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            destination = base / "skills" / "needquality"
            destination.mkdir(parents=True)
            outside = base / "outside.json"
            outside.write_text('{"files": {}}\n', encoding="utf-8")
            (destination / install.MANIFEST_NAME).symlink_to(outside)
            with self.assertRaisesRegex(ValueError, "manifest is a symlink"):
                install.previous_files(destination)

    def test_selected_roots_are_canonicalized_once_and_deduplicated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            first = base / "first"
            second = base / "second"
            first.mkdir()
            second.mkdir()
            alias = base / "alias"
            alias.symlink_to(first, target_is_directory=True)
            args = argparse.Namespace(
                root=[str(alias), str(first)], all=False, platform=None
            )
            destinations = install.selected_destinations(args)
            self.assertEqual(destinations, [first / "needquality"])
            alias.unlink()
            alias.symlink_to(second, target_is_directory=True)
            self.assertEqual(destinations, [first / "needquality"])

    def test_exact_destination_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            root = base / "skills"
            outside = base / "outside"
            root.mkdir()
            outside.mkdir()
            (root / "needquality").symlink_to(outside, target_is_directory=True)
            args = argparse.Namespace(root=[str(root)], all=False, platform=None)
            with self.assertRaisesRegex(ValueError, "destination is a symlink"):
                install.selected_destinations(args)

    def test_cli_check_exit_codes_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "skills"
            command = [sys.executable, str(SCRIPTS / "install.py"), "--root", str(root)]
            dry = subprocess.run([*command, "--check"], capture_output=True, text=True, check=False)
            self.assertEqual(dry.returncode, 1)
            self.assertFalse((root / "needquality").exists())
            installed = subprocess.run(command, capture_output=True, text=True, check=False)
            self.assertEqual(installed.returncode, 0, installed.stderr)
            clean = subprocess.run([*command, "--check"], capture_output=True, text=True, check=False)
            self.assertEqual(clean.returncode, 0, clean.stderr)


if __name__ == "__main__":
    unittest.main()
