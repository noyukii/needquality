from __future__ import annotations

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
