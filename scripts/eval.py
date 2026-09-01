#!/usr/bin/env python3
"""Run auditable NeedQuality candidate-versus-baseline evaluations. Stdlib only."""

from __future__ import annotations

import argparse
import concurrent.futures
import difflib
import hashlib
import json
import os
import re
import shutil
import sys
import tarfile
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from eval_adapters import ProviderAdapter, adapter_for, canonical_tool, event, now
from eval_evidence import redact, save_events, save_json, save_text
from eval_schema import case_files, load_evals, validate_baseline, validate_evals
from runtime_payload import payload_hash, runtime_files as payload_runtime_files

ROOT = Path(__file__).resolve().parent.parent
EVALS_PATH = ROOT / "evals" / "evals.json"
RUNS_DIR = ROOT / "evals" / ".runs"
BASELINE_ARCHIVE = ROOT / "evals" / "baseline-runtime.tar.gz"
RUNNERS = ("cursor", "codex", "claude")
HARNESS_VERSION = 3
PROFILE_CUSTOMIZATIONS = (
    ".agents/skills",
    ".codex/skills",
    ".codex/plugins",
    ".codex/agents",
    ".codex/AGENTS.md",
    ".cursor/skills",
    ".cursor/rules",
    ".cursor/commands",
    ".cursor/agents",
    ".cursor/plugins",
    ".claude/skills",
    ".claude/plugins",
    ".claude/commands",
    ".claude/agents",
    ".claude/CLAUDE.md",
    "AGENTS.md",
    "CLAUDE.md",
)
TRACE_LINE_RE = re.compile(r"(?m)^\s*`⚙︎ Used: ([^`\n]+)`\s*$")

JUDGE_PROMPT = """Grade one agent attempt. Use only the supplied task, original files,
final diff, final response, and normalized tool events. Tools are disabled. A rubric item
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


def normalize_output(stdout: str, runner: str) -> tuple[list[dict], str]:
    adapter = adapter_for(runner)
    events: list[dict] = []
    final_parts: list[str] = []
    raw_only = True
    for index, line in enumerate(stdout.splitlines(), 1):
        if not line.strip():
            continue
        raw_ref = f"stdout:{index}"
        timestamp = now()
        try:
            payload = json.loads(line)
            raw_only = False
        except json.JSONDecodeError:
            payload = {"type": "raw", "text": line}
        if payload.get("type") == "raw":
            events.append(event("raw", raw_ref, timestamp))
            continue
        normalized, texts, _ = adapter.normalize_record(payload, raw_ref, timestamp)
        events.extend(normalized)
        final_parts.extend(texts)
    final = final_parts[-1].strip() if final_parts else ""
    if not final and raw_only and stdout.strip():
        final = stdout.strip()
    return events, final


def runtime_files(skill: Path, *, require_metadata: bool = True) -> list[tuple[Path, Path]]:
    return [
        (path, Path(rel))
        for rel, path in payload_runtime_files(skill, require_metadata=require_metadata).items()
    ]


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
    runtime_files(destination, require_metadata=False)
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
    for relative in PROFILE_CUSTOMIZATIONS:
        path = home / relative
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists() or path.is_symlink():
            path.unlink()
    if skill is None:
        return
    destination = roots[runner] / "needquality"
    require_metadata = (skill / "agents" / "openai.yaml").is_file()
    for source, relative in runtime_files(skill, require_metadata=require_metadata):
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


def workspace_files(work: Path) -> tuple[dict[str, Path], set[str]]:
    files: dict[str, Path] = {}
    found_directories: set[str] = set()
    for current, directories, names in os.walk(work, topdown=True, followlinks=False):
        parent = Path(current)
        for name in [*directories, *names]:
            path = parent / name
            if path.is_symlink():
                raise ValueError(f"workspace contains symlink: {path.relative_to(work)}")
        found_directories.update(
            (parent / name).relative_to(work).as_posix() for name in directories
        )
        for name in names:
            path = parent / name
            if path.is_file():
                files[path.relative_to(work).as_posix()] = path
    return files, found_directories


def workspace_diff(original: dict[str, str], work: Path) -> str:
    current, current_directories = workspace_files(work)
    original_directories = {
        parent.as_posix()
        for rel in original
        for parent in Path(rel).parents
        if parent != Path(".")
    }
    chunks: list[str] = []
    for rel in sorted(original_directories - current_directories):
        chunks.append(f"directory deleted: {rel}\n")
    for rel in sorted(current_directories - original_directories):
        chunks.append(f"directory added: {rel}\n")
    for rel in sorted(set(original) | set(current)):
        before = original.get(rel, "")
        path = current.get(rel)
        after = path.read_text(encoding="utf-8", errors="replace") if path else ""
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


def result_row(item_id: str, status: str, why: str, kind: str) -> dict:
    return {
        "id": item_id,
        "status": status,
        "pass": True if status == "PASS" else False if status == "FAIL" else None,
        "why": why,
        "kind": kind,
    }


def deterministic_checks(
    case: dict,
    work: Path,
    response: str,
    events: list[dict],
    normalization_errors: list[str] | None = None,
) -> list[dict]:
    results: list[dict] = []
    errors = normalization_errors or []
    tools = [str(row["tool"]) for row in events if row.get("tool")]
    for check in case.get("checks", []):
        kind = check["kind"]
        status = "FAIL"
        why = ""
        if kind in {"path_exists", "path_absent"}:
            exists = (work / check["path"]).exists()
            passed = exists if kind == "path_exists" else not exists
            status = "PASS" if passed else "FAIL"
            why = f"path {'exists' if exists else 'is absent'}"
        elif kind in {"file_contains", "file_not_contains"}:
            path = work / check["path"]
            if not path.is_file():
                why = "path is not an existing regular file"
            else:
                matched = re.search(check["pattern"], path.read_text(encoding="utf-8", errors="replace"), re.S) is not None
                passed = matched if kind == "file_contains" else not matched
                status = "PASS" if passed else "FAIL"
                why = f"pattern {'matched' if matched else 'did not match'}"
        elif kind in {"response_contains", "response_not_contains"}:
            matched = re.search(check["pattern"], response, re.S) is not None
            passed = matched if kind == "response_contains" else not matched
            status = "PASS" if passed else "FAIL"
            why = f"response pattern {'matched' if matched else 'did not match'}"
        elif kind == "trace_exact":
            actual = trace_parts(response)
            passed = actual == check["parts"]
            status = "PASS" if passed else "FAIL"
            why = f"trace {actual!r}; expected {check['parts']!r}"
        elif kind == "trace_absent":
            actual = trace_parts(response)
            passed = actual is None and not TRACE_LINE_RE.search(response)
            status = "PASS" if passed else "FAIL"
            why = "trace absent" if passed else f"trace present: {actual!r}"
        elif kind in {"tool_used", "tool_absent"}:
            wanted = canonical_tool(check["tool"])
            used = wanted in tools
            if errors and (kind == "tool_absent" or not used):
                status = "INCONCLUSIVE"
                why = f"tool evidence incomplete: {errors!r}; observed tools: {tools!r}"
            else:
                passed = used if kind == "tool_used" else not used
                status = "PASS" if passed else "FAIL"
                why = f"observed tools: {tools!r}"
        results.append(result_row(check["id"], status, why, "check"))
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
        results.append(result_row(row["id"], "PASS" if row["pass"] else "FAIL", row["why"], "rubric"))
    return results


def inconclusive_results(case: dict, reason: str) -> list[dict]:
    rows = [result_row(check["id"], "INCONCLUSIVE", reason, "check") for check in case.get("checks", [])]
    rows.extend(result_row(item["id"], "INCONCLUSIVE", reason, "rubric") for item in case.get("rubric", []))
    return rows


def grade_results(results: list[dict], seconds: float, reason: str | None = None) -> dict:
    passed = sum(row["status"] == "PASS" for row in results)
    failed = sum(row["status"] == "FAIL" for row in results)
    inconclusive = sum(row["status"] == "INCONCLUSIVE" for row in results)
    grade = {
        "status": "FAILED" if failed else "INCONCLUSIVE" if inconclusive else "PASSED",
        "results": results,
        "passed": passed,
        "failed": failed,
        "inconclusive": inconclusive,
        "decided": passed + failed,
        "total": len(results),
        "seconds": round(seconds, 3),
    }
    if reason:
        grade["reason"] = reason
    return grade


def suite_status(
    *,
    critical_failed: bool,
    regressions: list[dict],
    candidate_only_failures: list[dict],
    quality_regressed: bool,
    inconclusive: bool,
) -> str:
    if critical_failed or regressions or candidate_only_failures or quality_regressed:
        return "FAILED"
    return "INCONCLUSIVE" if inconclusive else "PASSED"


def fixture_evidence(case: dict) -> list[dict]:
    return [
        {
            "source": str(source.relative_to(ROOT)),
            "workspace_path": rel,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        }
        for source, rel in case_files(ROOT, case)
    ]


def run_attempt(
    case: dict,
    variant_name: str,
    skill: Path | None,
    runner: ProviderAdapter,
    profile: Path,
    attempt_dir: Path,
    model: str | None,
    timeout: int,
) -> dict:
    attempt_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"needquality-case-{case['id']}-") as temp:
        work = Path(temp) / "workspace"
        work.mkdir()
        original: dict[str, str] = {}
        for source, rel in case_files(ROOT, case):
            if source.is_symlink() or not source.is_file():
                reason = f"fixture is not a regular file: {source.relative_to(ROOT)}"
                grade = grade_results(inconclusive_results(case, reason), 0, reason)
                save_json(attempt_dir / "grade.json", grade)
                return grade
            output = work / rel
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, output)
            original[rel] = output.read_text(encoding="utf-8", errors="replace")

        with IsolatedHome(profile, runner.name, skill) as home:
            task = runner.execute(case["prompt"], work, home, model, timeout, mode="task")
        require_metadata = bool(skill and (skill / "agents" / "openai.yaml").is_file())
        save_json(
            attempt_dir / "request.json",
            {
                "harness_version": HARNESS_VERSION,
                "case": case["id"],
                "name": case["name"],
                "prompt": case["prompt"],
                "fixtures": fixture_evidence(case),
                "variant": variant_name,
                "skill_payload_sha256": payload_hash(skill, require_metadata=require_metadata) if skill else None,
                "runner": runner.name,
                "runner_executable": runner.executable,
                "runner_version": runner.version(),
                "model": model or "default",
                "timeout_seconds": timeout,
                "profile": profile.name,
                "command": task["command"],
                "started_at": task["started_at"],
                "ended_at": task["ended_at"],
            },
        )
        save_events(attempt_dir / "raw-events.jsonl", task["raw_events"])
        save_events(attempt_dir / "events.jsonl", task["events"])
        save_text(attempt_dir / "final.md", task["final"])
        try:
            diff = workspace_diff(original, work)
        except ValueError as error:
            diff = ""
            task["malformed"] = True
            task["stderr"] = f"{task['stderr']}\n{error}".strip()
        save_text(attempt_dir / "diff.patch", diff)
        save_json(
            attempt_dir / "timing.json",
            {
                "seconds": task["seconds"],
                "returncode": task["returncode"],
                "timed_out": task["timed_out"],
                "stderr": task["stderr"],
            },
        )
        if task["returncode"] != 0 or task["timed_out"] or task["malformed"] or not task["final"]:
            reason = task["stderr"] or ("malformed event stream" if task["malformed"] else "runner returned no final response")
            grade = grade_results(inconclusive_results(case, reason), task["seconds"], reason)
            save_json(attempt_dir / "grade.json", grade)
            return grade

        results = deterministic_checks(case, work, task["final"], task["events"], task["normalization_errors"])
        rubric = case.get("rubric", [])
        judge_seconds = 0.0
        if rubric:
            if not runner.supports_tool_free_judge:
                reason = f"{runner.name} cannot enforce a tool-free semantic judge"
                results.extend(result_row(item["id"], "INCONCLUSIVE", reason, "rubric") for item in rubric)
            else:
                judge_input = redact(
                    {
                        "prompt": case["prompt"],
                        "original": "\n\n".join(f"--- {rel} ---\n{text}" for rel, text in sorted(original.items())) or "(none)",
                        "diff": diff or "(empty)",
                        "response": task["final"],
                        "events": task["events"],
                        "rubric": rubric,
                    }
                )
                save_json(attempt_dir / "judge-request.json", judge_input)
                judge_prompt = JUDGE_PROMPT.format(
                    prompt=judge_input["prompt"],
                    original=judge_input["original"],
                    diff=judge_input["diff"],
                    response=judge_input["response"],
                    events=json.dumps(judge_input["events"], ensure_ascii=False)[:30000],
                    rubric=json.dumps(judge_input["rubric"], ensure_ascii=False),
                )
                with tempfile.TemporaryDirectory(prefix="needquality-judge-workspace-") as judge_temp:
                    judge_work = Path(judge_temp)
                    with IsolatedHome(profile, runner.name, None) as judge_home:
                        judge = runner.execute(
                            judge_prompt, judge_work, judge_home, model, timeout, mode="judge"
                        )
                judge_seconds = judge["seconds"]
                save_events(attempt_dir / "judge-raw-events.jsonl", judge["raw_events"])
                save_events(attempt_dir / "judge-events.jsonl", judge["events"])
                save_text(attempt_dir / "judge-final.md", judge["final"])
                save_json(attempt_dir / "judge-timing.json", {key: judge[key] for key in ("seconds", "returncode", "timed_out", "stderr")})
                try:
                    if judge["normalization_errors"]:
                        raise ValueError(
                            f"judge event evidence is incomplete: {judge['normalization_errors']!r}"
                        )
                    if any(row.get("tool") for row in judge["events"]):
                        raise ValueError("judge emitted a tool event despite tool-free mode")
                    if judge["returncode"] != 0 or judge["timed_out"] or judge["malformed"] or not judge["final"]:
                        raise ValueError(judge["stderr"] or ("malformed event stream" if judge["malformed"] else "judge returned no final response"))
                    results.extend(parse_judge(judge["final"], rubric))
                except (ValueError, json.JSONDecodeError) as error:
                    reason = f"judge: {error}"
                    results.extend(result_row(item["id"], "INCONCLUSIVE", reason, "rubric") for item in rubric)

        grade = grade_results(results, task["seconds"] + judge_seconds)
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
    runner = adapter_for(runner_name)
    if not runner.available():
        return {"runner": runner_name, "status": "UNAVAILABLE", "reason": runner.unavailable_reason()}
    cases = [case for case in data["evals"] if only is None or case["id"] == only]
    if not cases:
        return {"runner": runner_name, "status": "INCONCLUSIVE", "reason": f"no eval {only}"}
    tasks = [
        (case, variant, skill, attempt, run_dir / runner_name / variant / f"case-{case['id']}" / f"attempt-{attempt}")
        for case in cases
        for variant, skill in (("baseline", baseline), ("candidate", candidate))
        for attempt in range(1, repetitions + 1)
    ]
    grades: list[dict] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(jobs, 1)) as pool:
        futures = {
            pool.submit(run_attempt, case, variant, skill, runner, profile, output, model, timeout): (case, variant, attempt, output)
            for case, variant, skill, attempt, output in tasks
        }
        for future in concurrent.futures.as_completed(futures):
            case, variant, attempt, output = futures[future]
            try:
                grade = future.result()
            except Exception as error:
                reason = f"harness: {error}"
                grade = grade_results(inconclusive_results(case, reason), 0, reason)
                save_json(output / "grade.json", grade)
            grades.append({"case": case["id"], "name": case["name"], "critical": case["critical"], "variant": variant, "attempt": attempt, **grade})
            print(f"{runner_name} {variant} case {case['id']}: {grade['status']}", flush=True)

    baseline_rows = [row for row in grades if row["variant"] == "baseline"]
    candidate_rows = [row for row in grades if row["variant"] == "candidate"]
    baseline_index = {
        (row["case"], row["attempt"], result["id"]): result["status"]
        for row in baseline_rows
        for result in row.get("results", [])
    }
    regressions: list[dict] = []
    improvements: list[dict] = []
    unchanged_failures: list[dict] = []
    candidate_only_failures: list[dict] = []
    comparable_total = comparable_baseline_passed = comparable_candidate_passed = 0
    for row in candidate_rows:
        for result in row.get("results", []):
            key = (row["case"], row["attempt"], result["id"])
            prior = baseline_index.get(key, "INCONCLUSIVE")
            current = result["status"]
            item = {"case": row["case"], "attempt": row["attempt"], "id": result["id"]}
            if prior in {"PASS", "FAIL"} and current in {"PASS", "FAIL"}:
                comparable_total += 1
                comparable_baseline_passed += prior == "PASS"
                comparable_candidate_passed += current == "PASS"
            if prior == "PASS" and current == "FAIL":
                regressions.append(item)
            elif prior == "FAIL" and current == "PASS":
                improvements.append(item)
            elif prior == "FAIL" and current == "FAIL":
                unchanged_failures.append(item)
            if current == "FAIL" and prior != "FAIL":
                candidate_only_failures.append({**item, "baseline_status": prior})
    critical_failed = any(
        row["critical"] and any(result["kind"] == "check" and result["status"] != "PASS" for result in row["results"])
        for row in candidate_rows
    )
    quality_regressed = comparable_candidate_passed < comparable_baseline_passed
    inconclusive = any(row["status"] == "INCONCLUSIVE" for row in grades)
    status = suite_status(
        critical_failed=critical_failed,
        regressions=regressions,
        candidate_only_failures=candidate_only_failures,
        quality_regressed=quality_regressed,
        inconclusive=inconclusive,
    )
    baseline_rate = comparable_baseline_passed / comparable_total if comparable_total else None
    candidate_rate = comparable_candidate_passed / comparable_total if comparable_total else None
    return {
        "runner": runner_name,
        "status": status,
        "baseline_passed": sum(row["passed"] for row in baseline_rows),
        "candidate_passed": sum(row["passed"] for row in candidate_rows),
        "baseline_total": sum(row["total"] for row in baseline_rows),
        "candidate_total": sum(row["total"] for row in candidate_rows),
        "comparable_assertions": comparable_total,
        "pass_rate_delta": round(candidate_rate - baseline_rate, 4) if baseline_rate is not None and candidate_rate is not None else None,
        "runtime_seconds": {
            "baseline": round(sum(row.get("seconds", 0) for row in baseline_rows), 3),
            "candidate": round(sum(row.get("seconds", 0) for row in candidate_rows), 3),
        },
        "improvements": improvements,
        "regressions": regressions,
        "unchanged_failures": unchanged_failures,
        "candidate_only_failures": candidate_only_failures,
        "attempts": grades,
    }


def smoke_runner(runner_name: str, profile: Path, candidate: Path, model: str | None, timeout: int, output: Path) -> dict:
    runner = adapter_for(runner_name)
    if not runner.available():
        return {"runner": runner_name, "status": "UNAVAILABLE", "reason": runner.unavailable_reason()}
    prompts = [
        ("active", "Review the current workspace. Do not modify files; report only the route you selected.", ["job:review"]),
        ("inactive", "What is two plus two?", None),
    ]
    rows = []
    for name, prompt, expected in prompts:
        with tempfile.TemporaryDirectory(prefix="needquality-smoke-") as temp:
            work = Path(temp) / "workspace"
            work.mkdir()
            with IsolatedHome(profile, runner_name, candidate) as home:
                result = runner.execute(prompt, work, home, model, timeout, mode="smoke")
            target = output / runner_name / name
            save_events(target / "raw-events.jsonl", result["raw_events"])
            save_events(target / "events.jsonl", result["events"])
            save_text(target / "final.md", result["final"])
            try:
                diff = workspace_diff({}, work)
            except ValueError as error:
                diff = str(error)
                diff_error = True
            else:
                diff_error = False
            save_text(target / "diff.patch", diff)
            save_json(target / "request.json", {"harness_version": HARNESS_VERSION, "runner": runner_name, "runner_version": runner.version(), "model": model or "default", "timeout_seconds": timeout, "profile": profile.name, "prompt": prompt, "command": result["command"], "started_at": result["started_at"], "ended_at": result["ended_at"]})
            save_json(target / "timing.json", {key: result[key] for key in ("seconds", "returncode", "timed_out", "stderr")})
            actual = trace_parts(result["final"])
            usable = result["returncode"] == 0 and not result["timed_out"] and not result["malformed"] and not result["normalization_errors"] and not diff_error and bool(result["final"])
            passed = usable and not diff and (actual == expected if expected is not None else actual is None and not TRACE_LINE_RE.search(result["final"]))
            rows.append({"name": name, "passed": passed, "expected": expected, "actual": actual, "returncode": result["returncode"], "status": "INCONCLUSIVE" if not usable else "PASSED" if passed else "FAILED"})
    status = "FAILED" if any(row["status"] == "FAILED" for row in rows) else "INCONCLUSIVE" if any(row["status"] == "INCONCLUSIVE" for row in rows) else "PASSED"
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
    actions.add_argument("--list", action="store_true")
    actions.add_argument("--check", action="store_true")
    actions.add_argument("--run", action="store_true")
    actions.add_argument("--smoke", action="store_true")
    actions.add_argument("--matrix", action="store_true")
    parser.add_argument("--runner", choices=(*RUNNERS, "all"), default="cursor")
    parser.add_argument("--profile-dir", type=Path)
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--candidate", type=Path, default=ROOT)
    parser.add_argument("--without-skill", action="store_true")
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
    if args.jobs < 1 or args.timeout < 1:
        parser.error("--jobs and --timeout must be positive")

    candidate = args.candidate.expanduser().absolute()
    baseline_temp: tempfile.TemporaryDirectory[str] | None = None
    if args.without_skill:
        baseline = None
    elif args.baseline:
        baseline = args.baseline.expanduser().absolute()
    else:
        baseline_temp = tempfile.TemporaryDirectory(prefix="needquality-baseline-")
        baseline = extract_baseline(BASELINE_ARCHIVE, Path(baseline_temp.name))
    runtime_files(candidate)
    if baseline:
        runtime_files(baseline, require_metadata=False)
    run_dir = RUNS_DIR / datetime.now(UTC).strftime("%Y%m%d-%H%M%S-%f")
    run_dir.mkdir(parents=True, exist_ok=False)

    runner_names = list(RUNNERS) if args.matrix or (args.smoke and args.runner == "all") else [args.runner]
    profiles: dict[str, Path] = {}
    profile_errors: dict[str, str] = {}
    for name in runner_names:
        try:
            profile = profile_for(args.profile_dir, name, len(runner_names) > 1)
            validate_profile(profile)
            profiles[name] = profile
        except ValueError as error:
            profile_errors[name] = str(error)

    results: list[dict] = []
    repetitions: int | None = None
    if args.smoke:
        for name in runner_names:
            results.append({"runner": name, "status": "UNAVAILABLE", "reason": profile_errors[name]} if name in profile_errors else smoke_runner(name, profiles[name], candidate, args.model, args.timeout, run_dir))
    else:
        repetitions = args.repetitions or (3 if args.matrix else 1)
        if repetitions < 1:
            parser.error("--repetitions must be positive")
        for name in runner_names:
            if name in profile_errors:
                results.append({"runner": name, "status": "UNAVAILABLE", "reason": profile_errors[name]})
            else:
                results.append(run_suite(data, name, profiles[name], baseline, candidate, args.case, repetitions, args.jobs, args.model, args.timeout, run_dir))

    save_json(
        run_dir / "summary.json",
        {
            "harness_version": HARNESS_VERSION,
            "created_at": now(),
            "mode": "smoke" if args.smoke else "matrix" if args.matrix else "run",
            "candidate": str(candidate),
            "candidate_payload_sha256": payload_hash(candidate),
            "baseline": str(baseline) if baseline else "without-skill",
            "baseline_payload_sha256": payload_hash(baseline, require_metadata=False) if baseline else None,
            "configuration": {"runners": runner_names, "model": args.model or "default", "timeout_seconds": args.timeout, "jobs": args.jobs, "repetitions": repetitions, "profiles": {name: profiles[name].name for name in profiles}},
            "results": results,
        },
    )
    for result in results:
        print(f"{result['runner']}: {result['status']}")
    print(f"report: {run_dir.relative_to(ROOT) / 'summary.json'}")
    if baseline_temp:
        baseline_temp.cleanup()
    return 0 if results and all(result["status"] == "PASSED" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
