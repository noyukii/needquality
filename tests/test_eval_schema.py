from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import eval as evaluator
from eval_schema import validate_baseline, validate_evals


class EvalSchemaTests(unittest.TestCase):
    def valid_data(self) -> dict:
        return {
            "version": 2,
            "evals": [
                {
                    "id": 1,
                    "name": "example-case",
                    "prompt": "Do the thing",
                    "files": [],
                    "critical": True,
                    "checks": [{"id": "route", "kind": "trace_absent"}],
                    "rubric": [],
                }
            ],
        }

    def test_accepts_version_two(self) -> None:
        self.assertEqual(validate_evals(self.valid_data()), [])

    def test_rejects_duplicate_assertion_ids_and_unsafe_paths(self) -> None:
        data = self.valid_data()
        case = data["evals"][0]
        case["files"] = ["../secret"]
        case["rubric"] = [{"id": "route", "text": "Something"}]
        errors = validate_evals(data)
        self.assertTrue(any("outside evals/files" in error for error in errors))
        self.assertTrue(any("duplicate assertion id" in error for error in errors))

    def test_normalizes_tool_events_and_redacts_secrets(self) -> None:
        output = '{"type":"tool_use","name":"web","input":{"api_key":"secret-value"}}\n'
        events, final = evaluator.normalize_output(output, "claude")
        self.assertEqual(events[0]["tool"], "web")
        self.assertEqual(events[0]["raw"]["input"]["api_key"], "<redacted>")
        self.assertEqual(final, "")

    def test_trace_check_uses_exact_order(self) -> None:
        case = {
            "checks": [
                {"id": "route", "kind": "trace_exact", "parts": ["job:implement", "load:python"]}
            ]
        }
        response = "`⚙︎ Used: job:implement · load:python`\nDone"
        result = evaluator.deterministic_checks(case, Path.cwd(), response, [])
        self.assertTrue(result[0]["pass"])

    def test_malformed_stream_is_detectable(self) -> None:
        events, final = evaluator.normalize_output("not json\n", "cursor")
        self.assertEqual(events[0]["type"], "raw")
        self.assertEqual(events[0]["raw_ref"], "stdout:1")
        self.assertEqual(final, "not json")
        self.assertTrue(any(event["type"] == "raw" for event in events))

    def test_captured_baseline_is_hash_valid_and_extractable(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(validate_baseline(root), [])
        with tempfile.TemporaryDirectory() as temp:
            extracted = evaluator.extract_baseline(
                root / "evals" / "baseline-runtime.tar.gz", Path(temp)
            )
            self.assertTrue((extracted / "SKILL.md").is_file())
            self.assertTrue(any(path.name == "SKILL.md" for path in extracted.rglob("SKILL.md")))


if __name__ == "__main__":
    unittest.main()
