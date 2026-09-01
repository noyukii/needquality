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
        validate.validate_portability(errors)
        self.assertEqual((jobs, flows), (18, 35))
        self.assertEqual(errors, [])

    def test_portability_rejects_provider_commands_and_child_skill_language(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality"
            references = root / "references"
            references.mkdir(parents=True)
            (root / "SKILL.md").write_text("Use /clear and a bundled SKILL.md.\n", encoding="utf-8")
            (references / "one.md").write_text("Use ~/.claude/skills/tool.\n", encoding="utf-8")
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                validate.validate_portability(errors)
            self.assertEqual(len(errors), 3)

    def test_tells_domain_vocabulary_is_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "data").mkdir()
            (root / "data" / "tells.csv").write_text(
                "id,domain,tell,fix\nreal,ui,tell,fix\ntypo,uii,tell,fix\n",
                encoding="utf-8",
            )
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                validate.validate_tells(errors)
            self.assertTrue(any("unknown domains: uii" in error for error in errors))
            self.assertTrue(
                any("lookup.py domains with no rows" in error for error in errors)
            )

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

    def test_unreachable_non_markdown_companion_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "renamed-checkout"
            references = root / "references"
            references.mkdir(parents=True)
            (root / "SKILL.md").write_text(
                "---\nname: needquality\ndescription: test\n---\n\n[used](references/used.md)\n",
                encoding="utf-8",
            )
            (references / "used.md").write_text("# Used\n", encoding="utf-8")
            (references / "orphan.sh").write_text("#!/bin/sh\n", encoding="utf-8")
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                validate.validate_docs(errors)
            self.assertTrue(any("orphan.sh" in error and "unreachable" in error for error in errors))
            self.assertFalse(any("name must be" in error for error in errors))

    def test_code_examples_do_not_create_links_but_invalid_prose_links_fail(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality"
            references = root / "references"
            references.mkdir(parents=True)
            (root / "SKILL.md").write_text(
                """---
name: needquality
description: test
---

[used](references/used.md)

```markdown
[example](/not-a-real-file)
```

`[inline](./src/example.md)`
""",
                encoding="utf-8",
            )
            (references / "used.md").write_text("[bad](/etc/passwd)\n[placeholder](link)\n", encoding="utf-8")
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                validate.validate_docs(errors)
            self.assertTrue(any("absolute local link" in error for error in errors))
            self.assertTrue(any("missing link: link" in error for error in errors))
            self.assertFalse(any("not-a-real-file" in error for error in errors))
            self.assertFalse(any("src/example.md" in error for error in errors))

    def test_multiline_inline_code_does_not_create_reference_links(self) -> None:
        errors: list[str] = []
        targets = validate.document_targets(
            "Prompt debris: `[Insert\nstatistic]`, `[Your Name]`, and `oaicite`.",
            errors,
            "example.md",
        )
        self.assertEqual(targets, [])
        self.assertEqual(errors, [])

    def test_unmatched_backtick_cannot_hide_links_in_later_paragraphs(self) -> None:
        errors: list[str] = []
        targets = validate.document_targets(
            "An unmatched ` delimiter.\n"
            "# A new block\n"
            "[real link](missing.md)\n"
            "A later `code span`.",
            errors,
            "example.md",
        )
        self.assertEqual(targets, ["missing.md"])
        self.assertEqual(errors, [])

    def test_malformed_words_section_reports_error_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality"
            root.mkdir()
            (root / "SKILL.md").write_text(
                "---\nname: needquality\ndescription: test\n---\n\n# Missing tables\n",
                encoding="utf-8",
            )
            (root / "references").mkdir()
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                jobs, flows = validate.validate_routes(errors)
            self.assertEqual((jobs, flows), (0, 0))
            self.assertTrue(any("Words" in error for error in errors))

    def test_malformed_words_and_load_rows_are_reported(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality"
            root.mkdir()
            (root / "SKILL.md").write_text(
                """---
name: needquality
description: test
---

## Words

| They say | Do | Read |
|---|---|---|
| broken | only two cells |

## Load

| Touching | Read before editing |
|---|---|
| `.py` |
""",
                encoding="utf-8",
            )
            (root / "references" / "jobs").mkdir(parents=True)
            (root / "references" / "flows").mkdir()
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                validate.validate_routes(errors)
            self.assertTrue(any("malformed Words row" in error for error in errors))
            self.assertTrue(any("malformed Load row" in error for error in errors))

    def test_missing_root_skill_reports_route_error_without_crashing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "needquality"
            root.mkdir()
            errors: list[str] = []
            with patch.object(validate, "ROOT", root):
                jobs, flows = validate.validate_routes(errors)
                validate.validate_portability(errors)
            self.assertEqual((jobs, flows), (0, 0))
            self.assertTrue(any("missing SKILL.md" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
