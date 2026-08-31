#!/usr/bin/env python3
"""Run auditable NeedQuality candidate-versus-baseline evaluations. Stdlib only."""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tarfile
import tempfile
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from eval_schema import assertion_count, case_files, load_evals, validate_baseline, validate_evals

ROOT = Path(__file__).resolve().parent.parent
EVALS_PATH = ROOT / "evals" / "evals.json"
RUNS_DIR = ROOT / "evals" / ".runs"
BASELINE_ARCHIVE = ROOT / "evals" / "baseline-runtime.tar.gz"
RUNNERS = ("cursor", "codex", "claude")
TRACE_LINE_RE = re.compile(r"(?m)^\s*`⚙︎ Used: ([^`\n]+)`\s*$")
SECRET_KEY_RE = re.compile(r"(?:authorization|cookie|password|secret|token|api[_-]?key)", re.I)
SECRET_VALUE_RE = re.compile(r"\b(?:sk|pk|AKIA|ghp|github_pat|Bearer)[-_A-Za-z0-9]{8,}\b")

JUDGE_PROMPT = """Grade one agent attempt. Use only the supplied task, original files,
final diff, final response, and normalized tool events. Do not run tools. A rubric item
passes only when the evidence plainly supports it. Missing evidence fails.

TASK:
{prompt}

ORIGINAL FILES:
{original}

FINAL DIFF:
{diff}

FINAL RESPONSE:
{response}

NORMALIZED TOOL EVENTS:
{events}

RUBRIC:
{rubric}

Reply with JSON only:
{{"results":[{{"id":"rubric-id","pass":true,"why":"brief evidence"}}]}}
Return one result for every rubric id in the same order."""


def now() -> str:
    return datetime.now(UTC).isoformat()


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            str(key): "<redacted>" if SECRET_KEY_RE.search(str(key)) else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        return SECRET_VALUE_RE.sub("<redacted>", value)
    return value


def find_tool(payload: Any) -> tuple[str | None, Any, str | None]:
    if not isinstance(payload, dict):
        return None, None, None
    kind = str(payload.get("type", ""))
    if kind in {"tool_use", "tool_call", "function_call"}:
        return str(payload.get("name") or payload.get("tool") or "unknown"), payload.get("input") or payload.get("arguments"), None
    if kind in {"command_execution", "shell_command"}:
        return "shell", payload.get("command") or payload.get("input"), payload.get("status")
    if kind in {"mcp_tool_call", "mcp_call"}:
        name = payload.get("name") or payload.get("tool")
        server = payload.get("server")
        return f"{server}.{name}" if server and name else str(name or "mcp"), payload.get("arguments"), payload.get("status")
    if kind in {"web_search", "web_search_call"}:
        return "web", payload.get("query") or payload.get("arguments"), payload.get("status")
    for key in ("item", "content", "message", "delta"):
        child = payload.get(key)
        if isinstance(child, dict):
            found = find_tool(child)
            if found[0]:
                return found
        elif isinstance(child, list):
            for entry in child:
                found = find_tool(entry)
                if found[0]:
                    return found
    return None, None, None


def find_text(payload: Any) -> list[str]:
    texts: list[str] = []
    if isinstance(payload, list):
        for item in payload:
            texts.extend(find_text(item))
        return texts
    if not isinstance(payload, dict):
        return texts
    kind = str(payload.get("type", ""))
    if kind in {"agent_message", "text", "output_text"} and isinstance(payload.get("text"), str):
        texts.append(payload["text"])
    if kind == "result" and isinstance(payload.get("result"), str):
        texts.append(payload["result"])
    for key in ("item", "content", "message"):
        if key in payload:
            texts.extend(find_text(payload[key]))
    return texts


def normalize_output(stdout: str, runner: str) -> tuple[list[dict], str]:
    events: list[dict] = []
    final_parts: list[str] = []
    for index, line in enumerate(stdout.splitlines(), 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
        except json.JSONDecodeError:
            raw = {"type": "raw", "text": line}
        safe = redact(raw)
        tool, arguments, status = find_tool(safe)
        event = {
            "index": index,
            "raw_ref": f"stdout:{index}",
            "timestamp": now(),
            "runner": runner,
            "type": str(safe.get("type", "unknown")) if isinstance(safe, dict) else "unknown",
            "tool": tool,
            "arguments": arguments,
            "status": status,
            "raw": safe,
        }
        events.append(event)
        final_parts.extend(find_text(safe))
    final = final_parts[-1].strip() if final_parts else ""
    if not final and stdout.strip() and not any(event["type"] != "raw" for event in events):
        final = stdout.strip()
    return events, final


class Runner:
    def __init__(self, name: str):
        self.name = name

    @property
    def executable(self) -> str:
        return {"cursor": "cursor-agent", "codex": "codex", "claude": "claude"}[self.name]

    def available(self) -> bool:
        return shutil.which(self.executable) is not None

    def command(self, prompt: str, cwd: Path, home: Path, model: str | None, readonly: bool) -> list[str]:
        if self.name == "cursor":
            command = [
                "cursor-agent", "--print", "--output-format", "stream-json", "--trust",
                "--workspace", str(cwd), "--sandbox", "enabled",
            ]
            command += ["--mode", "ask"] if readonly else ["--force"]
        elif self.name == "codex":
            command = [
                "codex", "exec", "--json", "--ephemeral", "--ignore-user-config",
                "--ignore-rules", "--skip-git-repo-check", "--sandbox",
                "read-only" if readonly else "workspace-write", "-C", str(cwd),
            ]
            if not readonly:
                command.append("--approve-for-me")
        else:
            command = [
                "claude", "--print", "--output-format", "stream-json",
                "--no-session-persistence", "--permission-mode",
                "plan" if readonly else "bypassPermissions",
            ]
            if not readonly:
                command.append("--allow-dangerously-skip-permissions")
        if model:
            command += ["--model", model]
        command.append(prompt)
        return command

    def execute(
        self,
        prompt: str,
        cwd: Path,
        home: Path,
        model: str | None,
        timeout: int,
        readonly: bool = False,
    ) -> dict:
        environment = os.environ.copy()
        environment.update(
            {
                "HOME": str(home),
                "CODEX_HOME": str(home / ".codex"),
                "XDG_CONFIG_HOME": str(home / ".config"),
            }
        )
        command = self.command(prompt, cwd, home, model, readonly)
        started = time.monotonic()
        try:
            done = subprocess.run(
                command,
                cwd=cwd,
                env=environment,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False,
            )
            events, final = normalize_output(done.stdout, self.name)
            return {
                "returncode": done.returncode,
                "seconds": round(time.monotonic() - started, 3),
                "events": events,
                "final": final,
                "malformed": any(event["type"] == "raw" for event in events),
                "stderr": redact(done.stderr),
                "command": [*command[:-1], "<prompt>"],
            }
        except (OSError, subprocess.TimeoutExpired) as error:
            return {
                "returncode": None,
                "seconds": round(time.monotonic() - started, 3),
                "events": [],
                "final": "",
                "malformed": False,
                "stderr": str(error),
                "command": [*command[:-1], "<prompt>"],
            }


def runtime_files(skill: Path) -> list[tuple[Path, Path]]:
    files: list[tuple[Path, Path]] = []
    for rel in (
        "SKILL.md",
        "references",
        "data/tells.csv",
        "scripts/lookup.py",
        "agents/openai.yaml",
    ):
        source = skill / rel
        if not source.exists():
            if rel == "agents/openai.yaml":
                continue
            raise ValueError(f"skill variant is missing {rel}: {skill}")
        candidates = sorted(path for path in source.rglob("*") if path.is_file()) if source.is_dir() else [source]
        files.extend((path, path.relative_to(skill)) for path in candidates if "__pycache__" not in path.parts)
    return files


def extract_baseline(archive: Path, destination: Path) -> Path:
    if not archive.is_file():
        raise ValueError(f"captured baseline is missing: {archive}")
    with tarfile.open(archive, "r:gz") as bundle:
        for member in bundle.getmembers():
            relative = Path(member.name)
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"unsafe path in baseline archive: {member.name}")
            if member.issym() or member.islnk():
                raise ValueError(f"link in baseline archive: {member.name}")
        bundle.extractall(destination)
    runtime_files(destination)
    return destination


def profile_for(base: Path, runner: str, multi: bool) -> Path:
    candidate = base / runner
    if candidate.is_dir():
        return candidate
    if not multi and base.is_dir():
        return base
    raise ValueError(f"missing dedicated {runner} profile under {base}")


def validate_profile(profile: Path) -> None:
    resolved = profile.resolve()
    live = {
        Path.home().resolve(),
        (Path.home() / ".codex").resolve(strict=False),
        (Path.home() / ".cursor").resolve(strict=False),
        (Path.home() / ".claude").resolve(strict=False),
        (Path.home() / ".agents").resolve(strict=False),
    }
    if resolved in live or resolved == ROOT.resolve():
        raise ValueError(f"refusing live agent profile: {resolved}")
    if not profile.is_dir():
        raise ValueError(f"evaluation profile does not exist: {profile}")
    symlink = next((path for path in profile.rglob("*") if path.is_symlink()), None)
    if symlink:
        raise ValueError(f"evaluation profile contains symlink: {symlink}")


def install_variant(home: Path, runner: str, skill: Path | None) -> None:
    roots = {
        "cursor": home / ".cursor" / "skills",
        "codex": home / ".codex" / "skills",
        "claude": home / ".claude" / "skills",
        "agents": home / ".agents" / "skills",
    }
    for root in roots.values():
        if root.exists():
            shutil.rmtree(root)
    root = roots[runner]
    destination = root / "needquality"
    if skill is None:
        return
    for source, relative in runtime_files(skill):
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, output)


class IsolatedHome:
    def __init__(self, profile: Path, runner: str, skill: Path | None):
        self.profile = profile
        self.runner = runner
        self.skill = skill
        self.temporary: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> Path:
        validate_profile(self.profile)
        self.temporary = tempfile.TemporaryDirectory(prefix=f"needquality-{self.runner}-")
        home = Path(self.temporary.name) / "home"
        shutil.copytree(self.profile, home)
        install_variant(home, self.runner, self.skill)
        return home

    def __exit__(self, *_: object) -> None:
        if self.temporary:
            self.temporary.cleanup()


def workspace_diff(original: dict[str, str], work: Path) -> str:
    paths = set(original)
    paths.update(str(path.relative_to(work)) for path in work.rglob("*") if path.is_file())
    chunks: list[str] = []
    for rel in sorted(paths):
        before = original.get(rel, "")
        path = work / rel
        after = path.read_text(encoding="utf-8", errors="replace") if path.is_file() else ""
        if before == after:
            continue
        chunks.extend(
            difflib.unified_diff(
                before.splitlines(keepends=True),
                after.splitlines(keepends=True),
                fromfile=f"a/{rel}",
                tofile=f"b/{rel}",
            )
        )
    return "".join(chunks)


def trace_parts(response: str) -> list[str] | None:
    matches = TRACE_LINE_RE.findall(response)
    if len(matches) != 1:
        return None
    return [part.strip() for part in matches[0].split("·")]


def deterministic_checks(case: dict, work: Path, response: str, events: list[dict]) -> list[dict]:
    results: list[dict] = []
    tools = [str(event.get("tool", "")) for event in events if event.get("tool")]
    for check in case.get("checks", []):
        kind = check["kind"]
        passed = False
        why = ""
        if kind in {"path_exists", "path_absent"}:
            exists = (work / check["path"]).exists()
            passed = exists if kind == "path_exists" else not exists
            why = f"path {'exists' if exists else 'is absent'}"
        elif kind in {"file_contains", "file_not_contains"}:
            path = work / check["path"]
            matched = path.is_file() and re.search(check["pattern"], path.read_text(encoding="utf-8", errors="replace"), re.S) is not None
            passed = matched if kind == "file_contains" else not matched
            why = f"pattern {'matched' if matched else 'did not match'}"
        elif kind in {"response_contains", "response_not_contains"}:
            matched = re.search(check["pattern"], response, re.S) is not None
            passed = matched if kind == "response_contains" else not matched
            why = f"response pattern {'matched' if matched else 'did not match'}"
        elif kind == "trace_exact":
            actual = trace_parts(response)
            passed = actual == check["parts"]
            why = f"trace {actual!r}; expected {check['parts']!r}"
        elif kind == "trace_absent":
            actual = trace_parts(response)
            passed = actual is None and not TRACE_LINE_RE.search(response)
            why = "trace absent" if passed else f"trace present: {actual!r}"
        elif kind in {"tool_used", "tool_absent"}:
            wanted = check["tool"].lower()
            used = any(wanted in tool.lower() for tool in tools)
            passed = used if kind == "tool_used" else not used
            why = f"observed tools: {tools!r}"
        results.append({"id": check["id"], "pass": passed, "why": why, "kind": "check"})
    return results


def parse_judge(text: str, rubric: list[dict]) -> list[dict]:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("judge returned no JSON object")
    payload = json.loads(text[start : end + 1])
    rows = payload.get("results") if isinstance(payload, dict) else None
    expected = [item["id"] for item in rubric]
    if not isinstance(rows, list) or [row.get("id") for row in rows if isinstance(row, dict)] != expected:
        raise ValueError("judge result ids are missing or out of order")
    results: list[dict] = []
    for row in rows:
        if type(row.get("pass")) is not bool or not isinstance(row.get("why"), str):
            raise ValueError(f"invalid judge result for {row.get('id')}")
        results.append({"id": row["id"], "pass": row["pass"], "why": row["why"], "kind": "rubric"})
    return results


def save_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(redact(value), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def save_events(path: Path, events: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for event in events:
            handle.write(json.dumps(redact(event), ensure_ascii=False) + "\n")


def run_attempt(
    case: dict,
    variant_name: str,
    skill: Path | None,
    runner: Runner,
    profile: Path,
    attempt_dir: Path,
    model: str | None,
    timeout: int,
) -> dict:
    attempt_dir.mkdir(parents=True, exist_ok=True)
    request = {
        "case": case["id"], "name": case["name"], "variant": variant_name,
        "runner": runner.name, "model": model or "default", "started_at": now(),
    }
    save_json(attempt_dir / "request.json", request)
    with tempfile.TemporaryDirectory(prefix=f"needquality-case-{case['id']}-") as temp:
        work = Path(temp) / "workspace"
        work.mkdir()
        original: dict[str, str] = {}
        for source, rel in case_files(ROOT, case):
            output = work / rel
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output)
            original[rel] = output.read_text(encoding="utf-8", errors="replace")
        with IsolatedHome(profile, runner.name, skill) as home:
            task = runner.execute(case["prompt"], work, home, model, timeout)
        save_events(attempt_dir / "events.jsonl", task["events"])
        (attempt_dir / "final.md").write_text(task["final"], encoding="utf-8")
        diff = workspace_diff(original, work)
        (attempt_dir / "diff.patch").write_text(diff, encoding="utf-8")
        save_json(
            attempt_dir / "timing.json",
            {"seconds": task["seconds"], "returncode": task["returncode"], "stderr": task["stderr"]},
        )

        if task["returncode"] != 0 or task["malformed"] or not task["final"]:
            grade = {
                "status": "INCONCLUSIVE",
                "reason": task["stderr"] or ("malformed event stream" if task["malformed"] else "runner returned no final response"),
                "results": [], "passed": 0, "total": assertion_count(case),
                "seconds": task["seconds"],
            }
            save_json(attempt_dir / "grade.json", grade)
            return grade

        results = deterministic_checks(case, work, task["final"], task["events"])
        rubric = case.get("rubric", [])
        if rubric:
            original_blob = "\n\n".join(f"--- {rel} ---\n{text}" for rel, text in sorted(original.items())) or "(none)"
            event_blob = json.dumps(task["events"], ensure_ascii=False)[:30000]
            rubric_blob = json.dumps(rubric, ensure_ascii=False)
            prompt = JUDGE_PROMPT.format(
                prompt=case["prompt"], original=original_blob, diff=diff or "(empty)",
                response=task["final"], events=event_blob, rubric=rubric_blob,
            )
            with IsolatedHome(profile, runner.name, None) as judge_home:
                judge = runner.execute(prompt, work, judge_home, model, timeout, readonly=True)
            save_events(attempt_dir / "judge-events.jsonl", judge["events"])
            (attempt_dir / "judge-final.md").write_text(judge["final"], encoding="utf-8")
            try:
                if judge["returncode"] != 0 or judge["malformed"] or not judge["final"]:
                    raise ValueError(
                        judge["stderr"]
                        or ("malformed event stream" if judge["malformed"] else "judge returned no final response")
                    )
                results.extend(parse_judge(judge["final"], rubric))
            except (ValueError, json.JSONDecodeError) as error:
                grade = {
                    "status": "INCONCLUSIVE", "reason": f"judge: {error}", "results": results,
                    "passed": sum(row["pass"] for row in results), "total": assertion_count(case),
                    "seconds": task["seconds"] + judge["seconds"],
                }
                save_json(attempt_dir / "grade.json", grade)
                return grade

        passed = sum(row["pass"] for row in results)
        grade = {
            "status": "PASSED" if passed == len(results) else "FAILED",
            "results": results, "passed": passed, "total": len(results),
            "seconds": task["seconds"] + (judge["seconds"] if rubric else 0),
        }
        save_json(attempt_dir / "grade.json", grade)
        return grade


def run_suite(
    data: dict,
    runner_name: str,
    profile: Path,
    baseline: Path | None,
    candidate: Path,
    only: int | None,
    repetitions: int,
    jobs: int,
    model: str | None,
    timeout: int,
    run_dir: Path,
) -> dict:
    runner = Runner(runner_name)
    if not runner.available():
        return {"runner": runner_name, "status": "UNAVAILABLE", "reason": "executable not found"}
    cases = [case for case in data["evals"] if only is None or case["id"] == only]
    if not cases:
        return {"runner": runner_name, "status": "INCONCLUSIVE", "reason": f"no eval {only}"}
    variants = [("baseline", baseline), ("candidate", candidate)]
    tasks = []
    for case in cases:
        for variant, skill in variants:
            for attempt in range(1, repetitions + 1):
                attempt_dir = run_dir / runner_name / variant / f"case-{case['id']}" / f"attempt-{attempt}"
                tasks.append((case, variant, skill, attempt, attempt_dir))

    grades: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(jobs, 1)) as pool:
        futures = {
            pool.submit(run_attempt, case, variant, skill, runner, profile, output, model, timeout):
            (case, variant, attempt, output)
            for case, variant, skill, attempt, output in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            case, variant, attempt, output = futures[future]
            try:
                grade = future.result()
            except Exception as error:
                grade = {"status": "INCONCLUSIVE", "reason": f"harness: {error}", "passed": 0, "total": assertion_count(case), "results": [], "seconds": 0}
                save_json(output / "grade.json", grade)
            row = {"case": case["id"], "name": case["name"], "critical": case["critical"], "variant": variant, "attempt": attempt, **grade}
            grades.append(row)
            print(f"{runner_name} {variant} case {case['id']}: {grade['status']}", flush=True)

    baseline_rows = [row for row in grades if row["variant"] == "baseline"]
    candidate_rows = [row for row in grades if row["variant"] == "candidate"]
    baseline_passed = sum(row["passed"] for row in baseline_rows)
    candidate_passed = sum(row["passed"] for row in candidate_rows)
    baseline_total = sum(row["total"] for row in baseline_rows)
    candidate_total = sum(row["total"] for row in candidate_rows)
    regressions: list[dict] = []
    improvements: list[dict] = []
    unchanged_failures: list[dict] = []
    index = {(row["case"], row["attempt"], result["id"]): result["pass"] for row in baseline_rows for result in row.get("results", [])}
    for row in candidate_rows:
        for result in row.get("results", []):
            key = (row["case"], row["attempt"], result["id"])
            prior = index.get(key)
            item = {"case": row["case"], "attempt": row["attempt"], "id": result["id"]}
            if prior is True and not result["pass"]:
                regressions.append(item)
            elif prior is False and result["pass"]:
                improvements.append(item)
            elif prior is False and not result["pass"]:
                unchanged_failures.append(item)
    critical_failed = any(row["critical"] and row["status"] != "PASSED" for row in candidate_rows)
    inconclusive = any(row["status"] == "INCONCLUSIVE" for row in grades)
    status = "PASSED"
    if inconclusive:
        status = "INCONCLUSIVE"
    elif critical_failed or regressions or candidate_passed < baseline_passed:
        status = "FAILED"
    return {
        "runner": runner_name, "status": status, "baseline_passed": baseline_passed,
        "candidate_passed": candidate_passed,
        "baseline_total": baseline_total,
        "candidate_total": candidate_total,
        "pass_rate_delta": round(
            (candidate_passed / candidate_total if candidate_total else 0)
            - (baseline_passed / baseline_total if baseline_total else 0),
            4,
        ),
        "runtime_seconds": {
            "baseline": round(sum(row.get("seconds", 0) for row in baseline_rows), 3),
            "candidate": round(sum(row.get("seconds", 0) for row in candidate_rows), 3),
        },
        "improvements": improvements,
        "regressions": regressions,
        "unchanged_failures": unchanged_failures,
        "attempts": grades,
    }


def smoke_runner(runner_name: str, profile: Path, candidate: Path, model: str | None, timeout: int, output: Path) -> dict:
    runner = Runner(runner_name)
    if not runner.available():
        return {"runner": runner_name, "status": "UNAVAILABLE", "reason": "executable not found"}
    prompts = [
        ("active", "Review the current workspace. Do not modify files; report only the route you selected.", ["job:review"]),
        ("inactive", "What is two plus two?", None),
    ]
    rows = []
    with tempfile.TemporaryDirectory(prefix="needquality-smoke-") as temp:
        work = Path(temp) / "workspace"
        work.mkdir()
        for name, prompt, expected in prompts:
            with IsolatedHome(profile, runner_name, candidate) as home:
                result = runner.execute(prompt, work, home, model, timeout, readonly=True)
            save_events(output / runner_name / f"{name}-events.jsonl", result["events"])
            actual = trace_parts(result["final"])
            usable = result["returncode"] == 0 and not result["malformed"] and bool(result["final"])
            passed = usable and (actual == expected if expected is not None else actual is None and not TRACE_LINE_RE.search(result["final"]))
            rows.append({"name": name, "passed": passed, "expected": expected, "actual": actual, "returncode": result["returncode"], "status": "INCONCLUSIVE" if not usable else ("PASSED" if passed else "FAILED")})
    status = "INCONCLUSIVE" if any(row["status"] == "INCONCLUSIVE" for row in rows) else ("PASSED" if all(row["passed"] for row in rows) else "FAILED")
    return {"runner": runner_name, "status": status, "checks": rows}


def check(data: dict) -> int:
    errors = [*validate_evals(data, ROOT), *validate_baseline(ROOT)]
    if errors:
        print("invalid eval data:", file=sys.stderr)
        for error in errors:
            print(f"  {error}", file=sys.stderr)
        return 2
    print(f"{len(data['evals'])} evals, schema and fixture files valid")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="NeedQuality evaluations")
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument("--list", action="store_true", help="print case id, name, and prompt")
    actions.add_argument("--check", action="store_true", help="validate schema and fixtures")
    actions.add_argument("--run", action="store_true", help="run candidate versus baseline")
    actions.add_argument("--smoke", action="store_true", help="test native discovery")
    actions.add_argument("--matrix", action="store_true", help="run all configured providers")
    parser.add_argument("--runner", choices=(*RUNNERS, "all"), default="cursor")
    parser.add_argument("--profile-dir", type=Path, help="dedicated evaluation profile or parent")
    parser.add_argument(
        "--baseline",
        type=Path,
        help="baseline skill directory; defaults to the captured implementation-start snapshot",
    )
    parser.add_argument("--candidate", type=Path, default=ROOT, help="candidate skill directory")
    parser.add_argument("--without-skill", action="store_true", help="use no skill as baseline")
    parser.add_argument("--case", type=int)
    parser.add_argument("--repetitions", type=int)
    parser.add_argument("--jobs", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=600)
    parser.add_argument("--model")
    args = parser.parse_args()

    data = load_evals(EVALS_PATH)
    if args.list:
        for case in data.get("evals", []):
            print(f"{case['id']}\t{case['name']}\t{case['prompt'].splitlines()[0]}")
        return 0
    if args.check or not (args.run or args.smoke or args.matrix):
        return check(data)
    if check(data):
        return 2
    if not args.profile_dir:
        parser.error("--profile-dir is required for agent runs")
    if args.without_skill and args.baseline:
        parser.error("--without-skill cannot be combined with --baseline")
    if args.run and args.runner == "all":
        parser.error("--run accepts one runner; use --matrix for all")
    if args.smoke and args.case is not None:
        parser.error("--case does not apply to --smoke")

    candidate = args.candidate.resolve()
    baseline_temp: tempfile.TemporaryDirectory[str] | None = None
    if args.without_skill:
        baseline = None
    elif args.baseline:
        baseline = args.baseline.resolve()
    else:
        baseline_temp = tempfile.TemporaryDirectory(prefix="needquality-baseline-")
        baseline = extract_baseline(BASELINE_ARCHIVE, Path(baseline_temp.name))
    runtime_files(candidate)
    if baseline:
        runtime_files(baseline)
    stamp = datetime.now(UTC).strftime("%Y%m%d-%H%M%S")
    run_dir = RUNS_DIR / stamp
    run_dir.mkdir(parents=True, exist_ok=True)

    runner_names = list(RUNNERS) if args.matrix or (args.smoke and args.runner == "all") else [args.runner]
    multi = len(runner_names) > 1
    profiles: dict[str, Path] = {}
    profile_errors: dict[str, str] = {}
    for name in runner_names:
        try:
            profile = profile_for(args.profile_dir, name, multi)
            validate_profile(profile)
            profiles[name] = profile
        except ValueError as error:
            profile_errors[name] = str(error)

    results: list[dict] = []
    if args.smoke:
        for name in runner_names:
            if name in profile_errors:
                results.append({"runner": name, "status": "UNAVAILABLE", "reason": profile_errors[name]})
            else:
                results.append(smoke_runner(name, profiles[name], candidate, args.model, args.timeout, run_dir))
    else:
        repetitions = args.repetitions or (3 if args.matrix else 1)
        if repetitions < 1:
            parser.error("--repetitions must be positive")
        for name in runner_names:
            if name in profile_errors:
                results.append({"runner": name, "status": "UNAVAILABLE", "reason": profile_errors[name]})
                continue
            results.append(
                run_suite(
                    data, name, profiles[name], baseline, candidate, args.case,
                    repetitions, args.jobs, args.model, args.timeout, run_dir,
                )
            )

    summary = {
        "created_at": now(), "mode": "smoke" if args.smoke else "matrix" if args.matrix else "run",
        "candidate": str(candidate), "baseline": str(baseline) if baseline else "without-skill",
        "results": results,
    }
    save_json(run_dir / "summary.json", summary)
    for result in results:
        print(f"{result['runner']}: {result['status']}")
    print(f"report: {run_dir.relative_to(ROOT) / 'summary.json'}")
    exit_code = 0 if results and all(result["status"] == "PASSED" for result in results) else 1
    if baseline_temp:
        baseline_temp.cleanup()
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
