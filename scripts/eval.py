#!/usr/bin/env python3
"""Run the needquality evals and score them. Stdlib only.

  python scripts/eval.py                  # fixtures exist
  python scripts/eval.py --list
  python scripts/eval.py --run            # run every case, score expectations
  python scripts/eval.py --run --case 3 --jobs 1

--run installs nothing. Sync the variant under test first:
  python scripts/install.py && python scripts/eval.py --run
"""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EVALS_PATH = ROOT / "evals" / "evals.json"
RUNS_DIR = ROOT / "evals" / ".runs"

JUDGE_PROMPT = """You are grading one attempt at a coding task. Judge only what the
final file contents show. Do not run tools. Do not be generous: an expectation
passes only if the code plainly satisfies it.

TASK GIVEN TO THE AGENT:
{prompt}

FINAL FILE CONTENTS:
{files}

EXPECTATIONS:
{expectations}

Reply with JSON only, no prose and no code fence:
{{"results": [{{"n": 1, "pass": true, "why": "under 15 words"}}]}}
One entry per expectation, in order."""


def load() -> dict:
    return json.loads(EVALS_PATH.read_text(encoding="utf-8"))


def validate_data(data: dict) -> list[str]:
    errors: list[str] = []
    cases = data.get("evals")
    if not isinstance(cases, list) or not cases:
        return ["evals must be a non-empty list"]

    seen: set[int] = set()
    for case in cases:
        cid = case.get("id") if isinstance(case, dict) else None
        if not isinstance(cid, int) or isinstance(cid, bool):
            errors.append(f"invalid eval id: {cid!r}")
            continue
        if cid in seen:
            errors.append(f"duplicate eval id: {cid}")
        seen.add(cid)
        if not isinstance(case.get("prompt"), str) or not case["prompt"].strip():
            errors.append(f"eval {cid}: missing prompt")
        expectations = case.get("expectations")
        if not isinstance(expectations, list) or not expectations:
            errors.append(f"eval {cid}: expectations must be a non-empty list")
        elif not all(isinstance(item, str) and item.strip() for item in expectations):
            errors.append(f"eval {cid}: expectations must be non-empty strings")
        files = case.get("files")
        if not isinstance(files, list) or not files:
            errors.append(f"eval {cid}: files must be a non-empty list")
            continue
        for rel in files:
            path = Path(rel) if isinstance(rel, str) else Path()
            if (
                not isinstance(rel, str)
                or path.is_absolute()
                or path.parts[:2] != ("evals", "files")
                or ".." in path.parts
            ):
                errors.append(f"eval {cid}: fixture is outside evals/files: {rel!r}")
    return errors


def case_files(case: dict) -> list[tuple[Path, str]]:
    """Fixture path plus its path relative to the case's own repo root."""
    out: list[tuple[Path, str]] = []
    for rel in case.get("files", []):
        src = ROOT / rel
        inside = Path(rel).relative_to("evals/files")
        out.append((src, str(Path(*inside.parts[1:]))))
    return out


def check(data: dict) -> int:
    errors = validate_data(data)
    if errors:
        print("invalid eval data:", file=sys.stderr)
        for line in errors:
            print(f"  {line}", file=sys.stderr)
        return 2
    missing: list[str] = []
    for case in data.get("evals", []):
        for src, _ in case_files(case):
            if not src.is_file():
                missing.append(f"eval {case.get('id')}: {src.relative_to(ROOT)}")
    if missing:
        print("missing fixtures:", file=sys.stderr)
        for line in missing:
            print(f"  {line}", file=sys.stderr)
        return 1
    print(f"{len(data.get('evals', []))} evals, all fixture files exist")
    return 0


def list_cases(data: dict) -> int:
    for case in data.get("evals", []):
        prompt = str(case.get("prompt", "")).split("\n", 1)[0]
        print(f"{case.get('id')}\t{prompt}")
    return 0


def agent(prompt: str, cwd: Path, model: str | None, timeout: int, ask: bool) -> str:
    cmd = ["cursor-agent", "--print", "--output-format", "text", "--trust"]
    cmd += ["--mode", "ask"] if ask else ["--force"]
    if model:
        cmd += ["--model", model]
    cmd.append(prompt)
    done = subprocess.run(
        cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False
    )
    if done.returncode != 0:
        raise RuntimeError((done.stderr or done.stdout).strip()[:400] or "agent failed")
    return done.stdout


def parse_json(text: str) -> dict:
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError(f"no JSON in judge reply: {text.strip()[:200]}")
    return json.loads(text[start : end + 1])


def judge_results(text: str, expected: int) -> list[dict]:
    payload = parse_json(text)
    if not isinstance(payload, dict):
        raise ValueError("judge reply is not an object")
    results = payload.get("results")
    if not isinstance(results, list) or len(results) != expected:
        count = len(results) if isinstance(results, list) else "no"
        raise ValueError(f"judge returned {count} results; expected {expected}")
    for n, row in enumerate(results, 1):
        if not isinstance(row, dict) or row.get("n") != n:
            raise ValueError(f"judge result {n} is missing or out of order")
        if type(row.get("pass")) is not bool:
            raise ValueError(f"judge result {n} has non-boolean pass")
        if not isinstance(row.get("why"), str):
            raise ValueError(f"judge result {n} has no why string")
    return results


def run_case(case: dict, stamp_dir: Path, model: str | None, timeout: int) -> dict:
    cid = case["id"]
    work = stamp_dir / f"case-{cid}"
    for src, rel in case_files(case):
        dest = work / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)

    started = time.monotonic()
    try:
        agent(case["prompt"], work, model, timeout, ask=False)
    except (RuntimeError, subprocess.TimeoutExpired, OSError) as err:
        return {"id": cid, "error": f"run: {err}", "passed": 0, "total": len(case["expectations"])}

    missing = [rel for _, rel in case_files(case) if not (work / rel).is_file()]
    if missing:
        return {
            "id": cid,
            "error": f"run removed fixture(s): {', '.join(missing)}",
            "passed": 0,
            "total": len(case["expectations"]),
        }

    blob = "\n\n".join(
        f"--- {rel} ---\n{(work / rel).read_text(encoding='utf-8', errors='replace')}"
        for _, rel in case_files(case)
    )
    extras = []
    present: set[str] = set()
    for rel in ("CONTEXT.md", "docs/adr", ".scratch"):
        p = work / rel
        if p.is_file():
            present.add(rel)
            extras.append(f"{rel}: present (file)")
        elif p.is_dir():
            present.add(rel)
            extras.append(f"{rel}: present (dir)")
        else:
            extras.append(f"{rel}: absent")
    expected_paths = {Path(rel) for _, rel in case_files(case)}
    unexpected = sorted(
        str(path.relative_to(work))
        for path in work.rglob("*")
        if path.is_file() and path.relative_to(work) not in expected_paths
    )
    if unexpected:
        extras.append("unexpected files: " + ", ".join(unexpected))
    blob += "\n\n--- skill-side-effects ---\n" + "\n".join(extras)
    listed = "\n".join(f"{i}. {e}" for i, e in enumerate(case["expectations"], 1))
    try:
        reply = agent(
            JUDGE_PROMPT.format(prompt=case["prompt"], files=blob, expectations=listed),
            work,
            model,
            timeout,
            ask=True,
        )
        results = judge_results(reply, len(case["expectations"]))
    except (RuntimeError, ValueError, subprocess.TimeoutExpired, OSError) as err:
        return {"id": cid, "error": f"judge: {err}", "passed": 0, "total": len(case["expectations"])}

    for i, exp in enumerate(case["expectations"], 1):
        rel = next((name for name in present if name in exp), None)
        if rel is None:
            continue
        for row in results:
            if row.get("n") == i:
                row["pass"] = False
                row["why"] = f"{rel} present"
                break
        else:
            results.append({"n": i, "pass": False, "why": f"{rel} present"})

    failed = [r for r in results if not r.get("pass")]
    return {
        "id": cid,
        "passed": len(results) - len(failed),
        "total": len(case["expectations"]),
        "failed": [{"n": r.get("n"), "why": r.get("why", "")} for r in failed],
        "seconds": round(time.monotonic() - started, 1),
    }


def skill_revision() -> str:
    done = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    rev = done.stdout.strip() or "unknown"
    dirty = subprocess.run(
        ["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True, check=False
    )
    return f"{rev}-dirty" if dirty.stdout.strip() else rev


def run(data: dict, only: int | None, model: str | None, jobs: int, timeout: int) -> int:
    cases = [c for c in data["evals"] if only is None or c["id"] == only]
    if not cases:
        print(f"no eval with id {only}", file=sys.stderr)
        return 2

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    stamp_dir = RUNS_DIR / stamp
    stamp_dir.mkdir(parents=True, exist_ok=True)

    with concurrent.futures.ThreadPoolExecutor(max_workers=jobs) as pool:
        futures = {pool.submit(run_case, c, stamp_dir, model, timeout): c for c in cases}
        results = []
        for future in concurrent.futures.as_completed(futures):
            try:
                row = future.result()
            except Exception as err:  # keep one broken case from hiding the report
                case = futures[future]
                row = {
                    "id": case["id"],
                    "error": f"harness: {err}",
                    "passed": 0,
                    "total": len(case["expectations"]),
                }
            results.append(row)
            note = row.get("error") or f"{row['passed']}/{row['total']}"
            print(f"case {row['id']}: {note}", flush=True)

    results.sort(key=lambda r: r["id"])
    passed = sum(r["passed"] for r in results)
    total = sum(r["total"] for r in results)
    report = {
        "skill_revision": skill_revision(),
        "model": model or "default",
        "passed": passed,
        "total": total,
        "cases": results,
    }
    (stamp_dir / "results.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\n{passed}/{total} expectations ({100 * passed // max(total, 1)}%) @ {report['skill_revision']}")
    print(f"report: {(stamp_dir / 'results.json').relative_to(ROOT)}")
    return 0 if passed == total else 1


def main() -> int:
    p = argparse.ArgumentParser(description="NeedQuality evals")
    p.add_argument("--list", action="store_true", help="print id and prompt")
    p.add_argument("--check", action="store_true", help="validate fixtures only")
    p.add_argument("--run", action="store_true", help="run cases and score expectations")
    p.add_argument("--case", type=int, help="run one eval id")
    p.add_argument("--model", help="model for the agent and the judge")
    p.add_argument("--jobs", type=int, default=4, help="cases in parallel")
    p.add_argument("--timeout", type=int, default=600, help="seconds per agent call")
    args = p.parse_args()

    if not EVALS_PATH.is_file():
        print(f"missing {EVALS_PATH}", file=sys.stderr)
        return 2
    data = load()
    errors = validate_data(data)
    if errors:
        print("invalid eval data:", file=sys.stderr)
        for line in errors:
            print(f"  {line}", file=sys.stderr)
        return 2
    if args.list:
        return list_cases(data)
    if args.check:
        if args.run or args.case is not None:
            print("--check cannot be combined with --run or --case", file=sys.stderr)
            return 2
        return check(data)
    if args.run:
        return run(data, args.case, args.model, max(args.jobs, 1), args.timeout)
    if args.case is not None:
        print("--case requires --run", file=sys.stderr)
        return 2
    return check(data)


if __name__ == "__main__":
    raise SystemExit(main())
