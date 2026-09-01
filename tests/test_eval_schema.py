from __future__ import annotations

import sys
import tarfile
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
            "version": 3,
            "evals": [
                {
                    "id": 1,
                    "name": "example-case",
                    "prompt": "Do the thing",
                    "skills": [],
                    "files": [],
                    "critical": True,
                    "checks": [{"id": "route", "kind": "skill_not_loaded"}],
                    "rubric": [],
                }
            ],
        }

    def test_accepts_version_three_and_rejects_older(self) -> None:
        self.assertEqual(validate_evals(self.valid_data()), [])
        data = self.valid_data()
        data["version"] = 2
        self.assertIn("version must be 3", validate_evals(data))

    def test_skill_expectations_must_name_known_skills(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = self.valid_data()
        case = data["evals"][0]
        case["skills"] = ["needquality-implement", "needquality-nope"]
        case["checks"] = [
            {"id": "loads", "kind": "skill_loaded", "skill": "needquality-implement"},
            {"id": "loads-missing", "kind": "skill_loaded", "skill": "needquality-nope"},
            {"id": "skips", "kind": "skill_not_loaded", "skill": "not-a-skill"},
        ]
        errors = validate_evals(data, root)
        self.assertIn("eval 1: unknown skill 'needquality-nope'", errors)
        self.assertIn("eval 1: loads-missing requires a known skill", errors)
        self.assertIn("eval 1: skips names an unknown skill", errors)
        self.assertFalse(any("loads requires" in error for error in errors))
        del case["skills"]
        self.assertTrue(any("skills must be a list" in error for error in validate_evals(data)))

    def test_diff_checks_require_patterns(self) -> None:
        data = self.valid_data()
        data["evals"][0]["checks"] = [
            {"id": "diff", "kind": "diff_not_contains"},
            {"id": "files", "kind": "no_new_files"},
        ]
        errors = validate_evals(data)
        self.assertEqual(errors, ["eval 1: diff requires pattern"])

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

    def test_incomplete_tool_evidence_cannot_pass_tool_used(self) -> None:
        result = evaluator.deterministic_checks(
            {"checks": [{"id": "used-web", "kind": "tool_used", "tool": "web"}]},
            Path.cwd(),
            "",
            [{"tool": "web"}],
            ["unrecognized tool-like record"],
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
                evaluator.save_text(
                    root / "final.md",
                    'api_key = "ordinary-fixture-secret-value"\n'
                    "sk-example-secret-123456789\n",
                )
                evaluator.save_text(root / "diff.patch", "STRIPE_WEBHOOK_SECRET=whsec_abcdefghijklmnopqrstuvwxyz123456\n")
                evaluator.save_json(root / "request.json", {"value": "environment-secret-value-123"})
                evaluator.save_events(
                    root / "events.jsonl",
                    [{"arguments": {"authorization": "Bearer abcdefghijklmnopqrstuvwxyz"}}],
                )
                evaluator.save_text(root / "types.ts", "token: string;\n")
            persisted = "\n".join(path.read_text(encoding="utf-8") for path in root.iterdir())
        self.assertNotIn("sk-example-secret", persisted)
        self.assertNotIn("environment-secret-value", persisted)
        self.assertNotIn("ordinary-fixture-secret-value", persisted)
        self.assertNotIn("abcdefghijklmnopqrstuvwxyz", persisted)
        self.assertNotIn("whsec_", persisted)
        self.assertIn("<redacted>", persisted)
        self.assertIn("token: string;", persisted)

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

    def test_codex_extracts_top_level_final_result(self) -> None:
        events, texts, errors = evaluator.adapter_for("codex").normalize_record(
            {"type": "result", "result": "final answer"},
            "stdout:9",
            datetime.now(UTC).isoformat(),
        )
        self.assertEqual(errors, [])
        self.assertEqual(texts, ["final answer"])
        self.assertEqual(events[0]["type"], "result")

    def test_codex_does_not_treat_tool_result_as_final_response(self) -> None:
        _, texts, errors = evaluator.adapter_for("codex").normalize_record(
            {
                "type": "item.completed",
                "item": {"type": "tool_result", "result": "internal tool output"},
                "result": "internal tool output",
            },
            "stdout:10",
            datetime.now(UTC).isoformat(),
        )
        self.assertTrue(errors)
        self.assertEqual(texts, [])

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

    def test_streaming_runner_ignores_blank_jsonl_lines(self) -> None:
        class FakeAdapter(evaluator.ProviderAdapter):
            name = "fake"
            executable = sys.executable

            def build_command(self, prompt, cwd, model, mode):
                script = (
                    "import json; "
                    "print(json.dumps({'type':'progress'})); "
                    "print(); "
                    "print(json.dumps({'type':'result','result':'done'}))"
                )
                return [sys.executable, "-u", "-c", script, prompt]

            def normalize_record(self, payload, raw_ref, timestamp):
                return (
                    [evaluator.event(payload["type"], raw_ref, timestamp)],
                    [payload["result"]] if isinstance(payload.get("result"), str) else [],
                    [],
                )

        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            result = FakeAdapter().execute("task", root, root, None, 2)
        self.assertFalse(result["malformed"])
        self.assertEqual(result["final"], "done")
        self.assertEqual(len(result["raw_events"]), 2)

    def test_judge_tool_event_is_inconclusive_and_attempt_evidence_is_redacted(self) -> None:
        class FakeJudgeAdapter(evaluator.ProviderAdapter):
            name = "claude"
            executable = sys.executable
            supports_tool_free_judge = True

            def __init__(self):
                self.prompts = []
                self.workspaces = []
                self.workspace_contents = []

            def build_command(self, prompt, cwd, model, mode):
                self.prompts.append((mode, prompt))
                self.workspaces.append((mode, cwd))
                self.workspace_contents.append((mode, list(cwd.iterdir())))
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
            "skills": [],
            "files": [],
            "critical": True,
            "checks": [{"id": "no-skill", "kind": "skill_not_loaded"}],
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
        self.assertEqual(adapter.workspace_contents[-1], ("judge", []))

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
            "skills": [],
            "files": [],
            "critical": True,
            "checks": [{"id": "route", "kind": "skill_not_loaded"}],
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

    def test_skill_loaded_reads_skill_files_from_tool_arguments(self) -> None:
        read = evaluator.event(
            "tool_call",
            "stdout:1",
            datetime.now(UTC).isoformat(),
            tool="read",
            arguments={"path": "/home/x/.cursor/skills/needquality-implement/SKILL.md"},
        )
        shell = evaluator.event(
            "tool_call",
            "stdout:2",
            datetime.now(UTC).isoformat(),
            tool="shell",
            arguments={"command": "cat ~/.codex/skills/needquality-python/SKILL.md"},
        )
        self.assertEqual(
            evaluator.skills_loaded([read, shell]),
            ["needquality-implement", "needquality-python"],
        )
        case = {
            "checks": [
                {"id": "loads", "kind": "skill_loaded", "skill": "needquality-implement"},
                {"id": "misses", "kind": "skill_loaded", "skill": "needquality-review"},
                {"id": "skips", "kind": "skill_not_loaded", "skill": "needquality-review"},
                {"id": "none", "kind": "skill_not_loaded"},
            ]
        }
        result = evaluator.deterministic_checks(case, Path.cwd(), "", [read, shell])
        self.assertEqual([row["status"] for row in result], ["PASS", "FAIL", "PASS", "FAIL"])
        quiet = evaluator.deterministic_checks(case, Path.cwd(), "", [])
        self.assertEqual([row["status"] for row in quiet], ["FAIL", "FAIL", "PASS", "PASS"])

    def test_skill_checks_are_inconclusive_without_complete_tool_evidence(self) -> None:
        case = {"checks": [{"id": "none", "kind": "skill_not_loaded"}]}
        result = evaluator.deterministic_checks(case, Path.cwd(), "", [], ["unrecognized tool-like record"])
        self.assertEqual(result[0]["status"], "INCONCLUSIVE")

    def test_diff_and_new_file_checks_read_the_workspace_diff(self) -> None:
        case = {
            "checks": [
                {"id": "no-any", "kind": "diff_not_contains", "pattern": r"^\+.*as any"},
                {"id": "adds-fn", "kind": "diff_contains", "pattern": r"^\+export function multiply"},
                {"id": "no-new", "kind": "no_new_files"},
            ]
        }
        diff = "+++ b/src/add.ts\n+export function multiply(a, b) {\n+  return (a as any) * b\n+}\n"
        result = evaluator.deterministic_checks(case, Path.cwd(), "", [], diff=diff, new_files=["src/utils.ts"])
        self.assertEqual([row["status"] for row in result], ["FAIL", "PASS", "FAIL"])
        self.assertIn("src/utils.ts", result[2]["why"])
        clean = evaluator.deterministic_checks(case, Path.cwd(), "", [], diff="+++ b/src/add.ts\n+export function multiply() {}\n")
        self.assertEqual([row["status"] for row in clean], ["PASS", "PASS", "PASS"])

    def test_added_files_are_detected_from_the_workspace(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            work = Path(temp)
            (work / "src").mkdir()
            (work / "src" / "add.ts").write_text("export {}\n", encoding="utf-8")
            (work / "src" / "utils.ts").write_text("export {}\n", encoding="utf-8")
            self.assertEqual(evaluator.added_files({"src/add.ts": "export {}\n"}, work), ["src/utils.ts"])

    def test_malformed_stream_is_detectable(self) -> None:
        events, final = evaluator.normalize_output("not json\n", "cursor")
        self.assertEqual(events[0]["type"], "raw")
        self.assertEqual(events[0]["raw_ref"], "stdout:1")
        self.assertEqual(final, "not json")
        self.assertTrue(any(event["type"] == "raw" for event in events))

    def test_variant_files_reject_symlinked_candidate_content(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp) / "checkout"
            skill = root / "skills" / "needquality-demo"
            skill.mkdir(parents=True)
            (skill / "SKILL.md").write_text(
                "---\nname: needquality-demo\ndescription: test\n---\n", encoding="utf-8"
            )
            (skill / "references").symlink_to(Path(temp), target_is_directory=True)
            with self.assertRaisesRegex(ValueError, "symlink"):
                evaluator.variant_files(root)

    def test_variant_files_install_each_skill_under_its_own_directory(self) -> None:
        root = Path(__file__).resolve().parents[1]
        destinations = {relative.parts[0] for _, relative in evaluator.variant_files(root)}
        self.assertIn("needquality-implement", destinations)
        self.assertIn("needquality-fix", destinations)
        self.assertNotIn("needquality", destinations)
        self.assertTrue(
            any(relative == Path("needquality-fix") / "SKILL.md" for _, relative in evaluator.variant_files(root))
        )
        self.assertEqual(len(evaluator.variant_hash(root)), 64)

    def test_captured_baseline_is_hash_valid_and_installs_as_legacy_monolith(self) -> None:
        root = Path(__file__).resolve().parents[1]
        self.assertEqual(validate_baseline(root), [])
        with tempfile.TemporaryDirectory() as temp:
            extracted = evaluator.extract_baseline(
                root / "evals" / "baseline-runtime.tar.gz", Path(temp)
            )
            self.assertTrue((extracted / "SKILL.md").is_file())
            destinations = {relative.parts[0] for _, relative in evaluator.variant_files(extracted)}
            self.assertEqual(destinations, {"needquality"})

    def test_baseline_rejects_special_archive_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = root / "unsafe.tar.gz"
            with tarfile.open(archive, "w:gz") as bundle:
                member = tarfile.TarInfo("pipe")
                member.type = tarfile.FIFOTYPE
                bundle.addfile(member)
            with self.assertRaisesRegex(ValueError, "unsafe archive member"):
                evaluator.extract_baseline(archive, root / "output")


if __name__ == "__main__":
    unittest.main()
