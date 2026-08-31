from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate


class ValidationTests(unittest.TestCase):
    def test_repository_has_one_skill_and_complete_routes(self) -> None:
        errors: list[str] = []
        validate.validate_docs(errors)
        jobs, flows = validate.validate_routes(errors)
        self.assertEqual((jobs, flows), (17, 35))
        self.assertEqual(errors, [])

    def test_frontmatter_rejects_duplicate_keys(self) -> None:
        _, errors = validate.frontmatter("---\nname: one\nname: two\ndescription: test\n---\n")
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_unreachable_reference_and_nested_skill_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality"
            references = root / "references"
            references.mkdir(parents=True)
            (root / "SKILL.md").write_text(
                "---\nname: needquality\ndescription: test\n---\n\n[used](references/used.md)\n",
                encoding="utf-8",
            )
            (references / "used.md").write_text("# Used\n", encoding="utf-8")
            (references / "orphan.md").write_text("# Orphan\n", encoding="utf-8")
            nested = references / "child" / "SKILL.md"
            nested.parent.mkdir()
            nested.write_text("---\nname: child\ndescription: child\n---\n", encoding="utf-8")
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                validate.validate_docs(errors)
            self.assertTrue(any("expected only root SKILL.md" in error for error in errors))
            self.assertTrue(any("unreachable" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
