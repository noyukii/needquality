from __future__ import annotations

import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

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
        self.assertEqual(events[0]["arguments"]["api_key"], "<redacted>")
        self.assertEqual(final, "")

    def test_cursor_nested_tool_and_claude_multiple_tools_are_all_normalized(self) -> None:
        cursor = {
            "type": "tool_call",
            "subtype": "completed",
            "call_id": "cursor-1",
            "tool_call": {
                "webSearchToolCall": {
                    "args": {"query": "postgres rls"},
                },
                "readToolCall": {"args": {"path": "SKILL.md"}},
            },
        }
        cursor_events, _, cursor_errors = evaluator.adapter_for("cursor").normalize_record(
            cursor, "stdout:1", datetime.now(UTC).isoformat()
        )
        self.assertEqual([event["tool"] for event in cursor_events], ["web", "read"])
        self.assertEqual(cursor_events[0]["status"], "completed")
        self.assertEqual(cursor_events[1]["status"], "completed")
        self.assertEqual(cursor_errors, [])

        claude = {
            "type": "assistant",
            "message": {
                "content": [
                    {"type": "tool_use", "id": "one", "name": "Bash", "input": {"command": "pwd"}},
                    {"type": "tool_use", "id": "two", "name": "WebSearch", "input": {"query": "docs"}},
                ]
            },
        }
        claude_events, _, claude_errors = evaluator.adapter_for("claude").normalize_record(
            claude, "stdout:1", datetime.now(UTC).isoformat()
        )
        self.assertEqual([event["tool"] for event in claude_events], ["shell", "web"])
        self.assertEqual(claude_errors, [])

    def test_unknown_tool_makes_absence_check_inconclusive(self) -> None:
        raw = {"type": "tool_call", "tool_call": {"mysteryToolCall": {"args": {}}}}
        events, _, errors = evaluator.adapter_for("cursor").normalize_record(
            raw, "stdout:1", datetime.now(UTC).isoformat()
        )
        result = evaluator.deterministic_checks(
            {"checks": [{"id": "no-web", "kind": "tool_absent", "tool": "web"}]},
            Path.cwd(),
            "",
            events,
            errors,
        )
        self.assertEqual(result[0]["status"], "INCONCLUSIVE")
        self.assertIsNone(result[0]["pass"])

    def test_invalid_generic_tool_names_make_evidence_inconclusive(self) -> None:
        records = {
            "cursor": {"type": "tool_call", "tool_call": {"name": None}},
            "codex": {"type": "tool_call", "name": " !!! "},
            "claude": {"type": "assistant", "message": {"content": [{"type": "tool_use", "name": "   "}]}},
        }
        for runner, raw in records.items():
            with self.subTest(runner=runner):
                events, _, errors = evaluator.adapter_for(runner).normalize_record(
                    raw, "stdout:1", datetime.now(UTC).isoformat()
                )
                result = evaluator.deterministic_checks(
                    {"checks": [{"id": "no-web", "kind": "tool_absent", "tool": "web"}]},
                    Path.cwd(),
                    "",
                    events,
                    errors,
                )
                self.assertTrue(errors)
                self.assertEqual(result[0]["status"], "INCONCLUSIVE")

    def test_tool_checks_use_exact_canonical_names(self) -> None:
        events = [{"tool": "webhook"}]
        result = evaluator.deterministic_checks(
            {"checks": [{"id": "no-web", "kind": "tool_absent", "tool": "web"}]},
            Path.cwd(),
            "",
            events,
            [],
        )
        self.assertEqual(result[0]["status"], "PASS")

    def test_file_not_contains_requires_a_regular_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = evaluator.deterministic_checks(
                {
                    "checks": [
                        {
                            "id": "not-there",
                            "kind": "file_not_contains",
                            "path": "missing.txt",
                            "pattern": "secret",
                        }
                    ]
                },
                Path(temp),
                "",
                [],
                [],
            )
        self.assertEqual(result[0]["status"], "FAIL")
        self.assertIn("regular file", result[0]["why"])

    def test_candidate_only_failure_fails_the_suite(self) -> None:
        self.assertEqual(
            evaluator.suite_status(
                critical_failed=False,
                regressions=[],
                candidate_only_failures=[{"case": 1, "id": "quality"}],
                quality_regressed=False,
                inconclusive=True,
            ),
            "FAILED",
        )

    def test_known_failure_dominates_inconclusive_evidence(self) -> None:
        grade = evaluator.grade_results(
            [
                evaluator.result_row("known", "FAIL", "failed", "check"),
                evaluator.result_row("missing", "INCONCLUSIVE", "missing", "rubric"),
            ],
            0,
        )
        self.assertEqual(grade["status"], "FAILED")

    def test_every_persistence_format_redacts_secret_values(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.dict("os.environ", {"SERVICE_TOKEN": "environment-secret-value-123"}, clear=False):
                evaluator.save_text(root / "final.md", "sk-example-secret-123456789\n")
                evaluator.save_text(root / "diff.patch", "STRIPE_WEBHOOK_SECRET=whsec_abcdefghijklmnopqrstuvwxyz123456\n")
                evaluator.save_json(root / "request.json", {"value": "environment-secret-value-123"})
                evaluator.save_events(
                    root / "events.jsonl",
                    [{"arguments": {"authorization": "Bearer abcdefghijklmnopqrstuvwxyz"}}],
                )
            persisted = "\n".join(path.read_text(encoding="utf-8") for path in root.iterdir())
        self.assertNotIn("sk-example-secret", persisted)
        self.assertNotIn("environment-secret-value", persisted)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", persisted)
        self.assertNotIn("whsec_", persisted)
        self.assertIn("<redacted>", persisted)

    def test_judge_requires_enforced_tool_free_mode(self) -> None:
        self.assertFalse(evaluator.adapter_for("cursor").supports_tool_free_judge)
        self.assertFalse(evaluator.adapter_for("codex").supports_tool_free_judge)
        self.assertTrue(evaluator.adapter_for("claude").supports_tool_free_judge)

    def test_unsupported_tool_free_judge_is_refused_before_launch(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with self.assertRaisesRegex(ValueError, "tool-free"):
                evaluator.adapter_for("cursor").execute(
                    "grade", root, root, None, 1, mode="judge"
                )

    def test_provider_command_check_rejects_unformatted_commands_and_arguments(self) -> None:
        case = {
            "checks": [
                {
                    "id": "no-command",
                    "kind": "response_not_contains",
                    "pattern": r"(?i)(?<![A-Za-z0-9_])/(?:clear|compact)\b",
                }
            ]
        }
        for response in ("Use /clear", "/compact now", "Try `/clear`"):
            with self.subTest(response=response):
                result = evaluator.deterministic_checks(case, Path.cwd(), response, [], [])
                self.assertEqual(result[0]["status"], "FAIL")

    def test_codex_web_event_preserves_status_call_id_and_timestamp(self) -> None:
        timestamp = datetime.now(UTC).isoformat()
        events, _, errors = evaluator.adapter_for("codex").normalize_record(
            {
                "type": "item.completed",
                "item": {"id": "web-1", "type": "web_search", "query": "docs"},
            },
            "stdout:4",
            timestamp,
        )
        self.assertEqual(errors, [])
        self.assertEqual(events[0]["tool"], "web")
        self.assertEqual(events[0]["status"], "completed")
        self.assertEqual(events[0]["call_id"], "web-1")
        self.assertEqual(events[0]["timestamp"], timestamp)

    def test_codex_multi_tool_record_normalizes_every_item(self) -> None:
        events, _, errors = evaluator.adapter_for("codex").normalize_record(
            {
                "type": "response.completed",
                "items": [
                    {"id": "shell-1", "type": "command_execution", "command": "pwd"},
                    {"id": "web-1", "type": "web_search", "query": "docs"},
                ],
            },
            "stdout:8",
            datetime.now(UTC).isoformat(),
        )
        self.assertEqual(errors, [])
        self.assertEqual([row["tool"] for row in events], ["shell", "web"])

    def test_streaming_runner_timestamps_events_and_times_out(self) -> None:
        class FakeAdapter(evaluator.ProviderAdapter):
            name = "fake"
            executable = sys.executable

            def __init__(self, script: str):
                self.script = script

            def build_command(self, prompt, cwd, model, mode):
                return [sys.executable, "-u", "-c", self.script, prompt]

            def normalize_record(self, payload, raw_ref, timestamp):
                return [evaluator.event(payload["type"], raw_ref, timestamp)], [payload.get("result", "")], []

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            streamed = FakeAdapter(
                "import json,time; "
                "print(json.dumps({'type':'progress'}), flush=True); "
                "time.sleep(0.05); "
                "print(json.dumps({'type':'result','result':'done'}), flush=True)"
            ).execute("task", root, root, None, 2)
            self.assertEqual(streamed["returncode"], 0)
            self.assertEqual(streamed["final"], "done")
            self.assertLess(
                streamed["raw_events"][0]["timestamp"],
                streamed["raw_events"][1]["timestamp"],
            )

            timed = FakeAdapter("import time; time.sleep(2)").execute(
                "task", root, root, None, 1
            )
            self.assertTrue(timed["timed_out"])
            self.assertNotEqual(timed["returncode"], 0)

    def test_judge_tool_event_is_inconclusive_and_attempt_evidence_is_redacted(self) -> None:
        class FakeJudgeAdapter(evaluator.ProviderAdapter):
            name = "claude"
            executable = sys.executable
            supports_tool_free_judge = True

            def __init__(self):
                self.prompts = []
                self.workspaces = []

            def build_command(self, prompt, cwd, model, mode):
                self.prompts.append((mode, prompt))
                self.workspaces.append((mode, cwd, sorted(Path(cwd).iterdir())))
                if mode == "judge":
                    script = (
                        "import json; "
                        "print(json.dumps({'type':'tool_use','name':'web','input':{'query':'x'}})); "
                        "print(json.dumps({'type':'result','result':'{\\\"results\\\":[{\\\"id\\\":\\\"quality\\\",\\\"pass\\\":true,\\\"why\\\":\\\"ok\\\"}]}' }))"
                    )
                else:
                    script = "import json; print(json.dumps({'type':'result','result':'done sk-example-secret-123456789'}))"
                return [sys.executable, "-u", "-c", script, prompt]

            def normalize_record(self, payload, raw_ref, timestamp):
                if payload["type"] == "tool_use":
                    return [evaluator.event("tool_call", raw_ref, timestamp, tool=payload["name"], arguments=payload.get("input"))], [], []
                return [evaluator.event(payload["type"], raw_ref, timestamp)], [payload.get("result", "")], []

        case = {
            "id": 999,
            "name": "fake-judge",
            "prompt": "Do the task",
            "files": [],
            "critical": True,
            "checks": [{"id": "no-trace", "kind": "trace_absent"}],
            "rubric": [{"id": "quality", "text": "Good result"}],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / "profile"
            profile.mkdir()
            attempt = root / "attempt"
            adapter = FakeJudgeAdapter()
            grade = evaluator.run_attempt(
                case, "candidate", None, adapter, profile, attempt, None, 5
            )
            persisted = "\n".join(
                path.read_text(encoding="utf-8", errors="replace")
                for path in attempt.rglob("*")
                if path.is_file()
            )
        self.assertEqual(grade["status"], "INCONCLUSIVE")
        self.assertEqual(grade["results"][0]["status"], "PASS")
        self.assertEqual(grade["results"][1]["status"], "INCONCLUSIVE")
        self.assertNotIn("sk-example-secret", persisted)
        self.assertIn('"tool": "web"', persisted)
        self.assertNotIn("sk-example-secret", adapter.prompts[-1][1])
        self.assertNotEqual(adapter.workspaces[0][1], adapter.workspaces[-1][1])
        self.assertEqual(adapter.workspaces[-1][0], "judge")
        self.assertEqual(adapter.workspaces[-1][2], [])

    def test_malformed_task_attempt_grades_every_assertion_inconclusive(self) -> None:
        class MalformedAdapter(evaluator.ProviderAdapter):
            name = "cursor"
            executable = sys.executable

            def build_command(self, prompt, cwd, model, mode):
                return [sys.executable, "-u", "-c", "print('not json')", prompt]

            def normalize_record(self, payload, raw_ref, timestamp):
                return [], [], []

        case = {
            "id": 998,
            "name": "malformed",
            "prompt": "Do the task",
            "files": [],
            "critical": True,
            "checks": [{"id": "route", "kind": "trace_absent"}],
            "rubric": [{"id": "quality", "text": "Good result"}],
        }
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            profile = root / "profile"
            profile.mkdir()
            grade = evaluator.run_attempt(
                case, "candidate", None, MalformedAdapter(), profile, root / "attempt", None, 5
            )
        self.assertEqual(grade["status"], "INCONCLUSIVE")
        self.assertEqual([row["status"] for row in grade["results"]], ["INCONCLUSIVE", "INCONCLUSIVE"])

    def test_trace_check_uses_exact_order(self) -> None:
        case = {
            "checks": [
                {"id": "route", "kind": "trace_exact", "parts": ["job:implement", "load:python"]}
            ]
        }
        response = "`⚙︎ Used: job:implement · load:python`\nDone"
        result = evaluator.deterministic_checks(case, Path.cwd(), response, [])
        self.assertEqual(result[0]["status"], "PASS")

    def test_trace_check_parses_phase_separators(self) -> None:
        parts = ["job:implement", "load:ui", "‖", "job:document", "load:copy"]
        case = {"checks": [{"id": "route", "kind": "trace_exact", "parts": parts}]}
        response = "Done\n`⚙︎ Used: job:implement · load:ui ‖ job:document · load:copy`"
        result = evaluator.deterministic_checks(case, Path.cwd(), response, [])
        self.assertEqual(result[0]["status"], "PASS")
        data = self.valid_data()
        data["evals"][0]["checks"] = [{"id": "route", "kind": "trace_exact", "parts": parts}]
        self.assertEqual(validate_evals(data), [])
        data["evals"][0]["checks"] = [
            {"id": "route", "kind": "trace_exact", "parts": ["‖", "job:document"]}
        ]
        errors = validate_evals(data)
        self.assertTrue(any("misplaced phase separator" in error for error in errors))

    def test_reasoning_check_reads_thinking_stream_or_is_inconclusive(self) -> None:
        case = {
            "checks": [
                {"id": "flag", "kind": "reasoning_contains", "pattern": "⚙︎ Load: ui"}
            ]
        }
        raw = [
            {
                "payload": {
                    "type": "assistant",
                    "message": {
                        "content": [
                            {"type": "thinking", "thinking": "⚙︎ Load: ui then edit"}
                        ]
                    },
                }
            }
        ]
        result = evaluator.deterministic_checks(case, Path.cwd(), "Done", [], None, raw)
        self.assertEqual(result[0]["status"], "PASS")
        result = evaluator.deterministic_checks(case, Path.cwd(), "Done", [], None, [])
        self.assertEqual(result[0]["status"], "INCONCLUSIVE")

    def test_malformed_stream_is_detectable(self) -> None:
        events, final = evaluator.normalize_output("not json\n", "cursor")
        self.assertEqual(events[0]["type"], "raw")
        self.assertEqual(events[0]["raw_ref"], "stdout:1")
        self.assertEqual(final, "not json")
        self.assertTrue(any(event["type"] == "raw" for event in events))

    def test_runtime_payload_rejects_symlinked_candidate_content(self) -> None:
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
            with self.assertRaisesRegex(ValueError, "symlink"):
                evaluator.runtime_files(root)

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
