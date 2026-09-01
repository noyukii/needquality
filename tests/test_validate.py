from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import validate

CONTRACT = "## Contract\n\n1. **Scope.** Name the files.\n"


def write_skill(
    root: Path,
    name: str,
    *,
    description: str = "Does a thing for tests. Use when the user says \"demo\".",
    body: str = "",
    files: dict[str, str] | None = None,
    contract: bool = True,
    metadata: bool = True,
) -> Path:
    skill = root / "skills" / name
    skill.mkdir(parents=True)
    parts = [f"---\nname: {name}\ndescription: {description}\n---\n\n# Demo\n"]
    if contract:
        parts.append(CONTRACT)
    parts.append(body)
    (skill / "SKILL.md").write_text("\n".join(parts), encoding="utf-8")
    if metadata:
        (skill / "agents").mkdir()
        (skill / "agents" / "openai.yaml").write_text(
            'interface:\n  display_name: "Demo"\n  short_description: "Demo"\n'
            '  default_prompt: "Use demo."\npolicy:\n  allow_implicit_invocation: true\n',
            encoding="utf-8",
        )
    for rel, text in (files or {}).items():
        path = skill / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    return skill


@contextmanager
def fake_repo():
    with tempfile.TemporaryDirectory() as temp:
        root = Path(temp) / "checkout"
        (root / "shared").mkdir(parents=True)
        (root / "shared" / "contract.md").write_text(CONTRACT, encoding="utf-8")
        with (
            patch.object(validate, "ROOT", root),
            patch.object(validate, "CONTRACT_PATH", root / "shared" / "contract.md"),
        ):
            yield root


def run_skill_checks(root: Path) -> list[str]:
    errors: list[str] = []
    skills = validate.validate_discovery(errors)
    reports = [report for skill in skills if (report := validate.validate_skill(skill, errors))]
    validate.validate_skill_set(reports, errors)
    return errors


class ValidationTests(unittest.TestCase):
    def test_repository_skills_validate(self) -> None:
        errors: list[str] = []
        validate.validate_contract_source(errors)
        skills = validate.validate_discovery(errors)
        reports = [report for skill in skills if (report := validate.validate_skill(skill, errors))]
        tokens = validate.validate_skill_set(reports, errors)
        validate.validate_research(errors)
        validate.validate_tells(errors)
        self.assertEqual(errors, [])
        self.assertEqual(len(reports), 31)
        self.assertLessEqual(tokens, validate.METADATA_TOKEN_BUDGET)
        self.assertTrue(all(report.name.startswith("needquality-") for report in reports))

    def test_frontmatter_rejects_duplicate_keys(self) -> None:
        _, errors = validate.frontmatter("---\nname: one\nname: two\ndescription: test\n---\n")
        self.assertTrue(any("duplicate" in error for error in errors))

    def test_well_formed_skill_passes(self) -> None:
        with fake_repo() as root:
            write_skill(
                root,
                "needquality-demo",
                body="[one](references/one.md)\n",
                files={"references/one.md": "# One\n"},
            )
            self.assertEqual(run_skill_checks(root), [])

    def test_unlinked_reference_and_nested_skill_fail(self) -> None:
        with fake_repo() as root:
            write_skill(
                root,
                "needquality-demo",
                body="[used](references/used.md)\n",
                files={
                    "references/used.md": "# Used\n",
                    "references/orphan.md": "# Orphan\n",
                    "references/child/SKILL.md": "---\nname: child\ndescription: child\n---\n",
                },
            )
            errors = run_skill_checks(root)
            self.assertTrue(any("orphan.md is not linked directly" in error for error in errors))
            self.assertTrue(any("nested SKILL.md" in error for error in errors))
            self.assertTrue(any("SKILL.md outside" in error for error in errors))

    def test_second_level_reference_must_still_link_from_root(self) -> None:
        with fake_repo() as root:
            write_skill(
                root,
                "needquality-demo",
                body="[one](references/one.md)\n",
                files={
                    "references/one.md": "[two](one/two.md)\n",
                    "references/one/two.md": "# Two\n",
                },
            )
            errors = run_skill_checks(root)
            self.assertEqual(
                errors, ["needquality-demo: references/one/two.md is not linked directly from SKILL.md"]
            )

    def test_unreachable_non_markdown_companion_fails(self) -> None:
        with fake_repo() as root:
            write_skill(
                root,
                "needquality-demo",
                body="[used](references/used.md)\n",
                files={"references/used.md": "# Used\n", "scripts/orphan.sh": "#!/bin/sh\n"},
            )
            errors = run_skill_checks(root)
            self.assertTrue(any("scripts/orphan.sh is not linked" in error for error in errors))

    def test_links_may_not_leave_the_skill(self) -> None:
        with fake_repo() as root:
            write_skill(root, "needquality-other")
            write_skill(
                root,
                "needquality-demo",
                body="[other](../needquality-other/SKILL.md)\n",
            )
            errors = run_skill_checks(root)
            self.assertTrue(any("link escapes skill" in error for error in errors))

    def test_cross_skill_mentions_must_resolve(self) -> None:
        with fake_repo() as root:
            write_skill(root, "needquality-demo", body="Hand off to `needquality-missing`.\n")
            errors = run_skill_checks(root)
            self.assertIn("needquality-demo: mentions unknown skill needquality-missing", errors)

    def test_duplicate_trigger_phrase_is_rejected(self) -> None:
        with fake_repo() as root:
            write_skill(root, "needquality-one", description='One thing for tests here. Use when the user says "review".')
            write_skill(root, "needquality-two", description='Another thing for tests. Use when the user says "Review".')
            errors = run_skill_checks(root)
            self.assertTrue(any("trigger phrase 'review' is claimed by" in error for error in errors))

    def test_description_requires_trigger_sentence_and_length(self) -> None:
        with fake_repo() as root:
            write_skill(root, "needquality-demo", description="Too short.")
            errors = run_skill_checks(root)
            self.assertTrue(any("under 50 characters" in error for error in errors))
            self.assertTrue(any("Use when" in error for error in errors))

    def test_contract_block_must_match_shared_source(self) -> None:
        with fake_repo() as root:
            write_skill(root, "needquality-demo", contract=False, body="## Contract\n\n1. Something else.\n")
            errors = run_skill_checks(root)
            self.assertTrue(any("shared contract block" in error for error in errors))

    def test_missing_openai_metadata_is_reported(self) -> None:
        with fake_repo() as root:
            write_skill(root, "needquality-demo", metadata=False)
            errors = run_skill_checks(root)
            self.assertIn("needquality-demo: missing agents/openai.yaml", errors)

    def test_metadata_budget_is_enforced(self) -> None:
        with fake_repo() as root:
            write_skill(root, "needquality-demo", description="Use when " + "word " * 200)
            with patch.object(validate, "METADATA_TOKEN_BUDGET", 10):
                errors = run_skill_checks(root)
            self.assertTrue(any("budget is 10" in error for error in errors))

    def test_portability_rejects_provider_commands_and_retired_vocabulary(self) -> None:
        with fake_repo() as root:
            write_skill(
                root,
                "needquality-demo",
                body="Use /clear and a bundled SKILL.md.\n[one](references/one.md)\n",
                files={"references/one.md": "Use ~/.claude/skills/tool and the Words table.\n"},
            )
            errors = run_skill_checks(root)
            labels = [error.split(": ", 1)[1] for error in errors]
            self.assertIn("provider-specific clear command: /clear", labels)
            self.assertIn("nested child-skill terminology: bundled SKILL.md", labels)
            self.assertIn("provider-specific specialist path: ~/.claude/skills/", labels)
            self.assertIn("retired router vocabulary: Words table", labels)

    def test_code_examples_do_not_create_links_but_invalid_prose_links_fail(self) -> None:
        with fake_repo() as root:
            write_skill(
                root,
                "needquality-demo",
                body=textwrap.dedent(
                    """
                    [used](references/used.md)

                    ```markdown
                    [example](/not-a-real-file)
                    ```

                    `[inline](./src/example.md)`
                    """
                ),
                files={"references/used.md": "[bad](/etc/passwd)\n[placeholder](link)\n"},
            )
            errors = run_skill_checks(root)
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

    def test_tells_domain_vocabulary_is_closed(self) -> None:
        with fake_repo() as root:
            cleanup = root / "skills" / validate.CLEANUP_SKILL
            (cleanup / "data").mkdir(parents=True)
            (cleanup / "scripts").mkdir()
            (cleanup / "data" / "tells.csv").write_text(
                "id,domain,tell,fix\nreal,ui,tell,fix\ntypo,uii,tell,fix\n",
                encoding="utf-8",
            )
            (cleanup / "scripts" / "lookup.py").write_text(
                'EXT_DOMAIN = {".py": ("py",), ".tsx": ("react", "ui")}\n', encoding="utf-8"
            )
            errors: list[str] = []
            validate.validate_tells(errors)
            self.assertTrue(any("unknown domains: uii" in error for error in errors))
            self.assertTrue(any("lookup.py domains with no rows: py, react" in error for error in errors))

    def test_missing_skills_directory_reports_error_without_crashing(self) -> None:
        with fake_repo() as root:
            errors: list[str] = []
            self.assertEqual(validate.validate_discovery(errors), [])
            self.assertTrue(any("missing skills directory" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
