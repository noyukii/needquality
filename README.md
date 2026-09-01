<div align="center">
  <img src="assets/needquality.png" alt="NeedQuality" width="780">
</div>

<h3 align="center">Focused guidance for reliable software changes</h3>

## What it is

NeedQuality is one routed agent skill for software delivery. The root skill
chooses one job or flow, loads only the relevant references, and requires fresh
evidence for completion claims. Installing it registers a single discoverable
`SKILL.md`, so bundled flows cannot become competing skills.

## Install

Use Python 3.11 or newer. Runtime scripts use only the standard library.

```bash
python3 scripts/install.py --all
```

`--all` installs to the standard skill roots for Agent Skills, Claude, Cursor,
and Codex. Other useful forms:

```bash
python3 scripts/install.py --check
python3 scripts/install.py --platform codex --platform cursor
python3 scripts/install.py --root /path/to/custom/skills
```

Without a target option, the installer updates existing NeedQuality installs.
Standard roots are `~/.agents/skills`, `~/.claude/skills`, `~/.cursor/skills`,
and Codex's `$CODEX_HOME/skills` (fallback `~/.codex/skills`).

## Development

### Routing

Routing follows four rules:

1. An explicitly named flow outranks an inferred generic job.
2. The longest matching phrase wins.
3. One primary job or flow is selected.
4. Applicable language, framework, UI, research, and trust references are added
   in table order.

Multiple jobs or flows are composed only when the request clearly asks for
distinct operations. Active runs emit the canonical route trace documented in
`SKILL.md`; unrelated question-only requests do not.

```bash
python3 scripts/validate.py --stats
```

Use the inventory command instead of relying on copied counts.

### Validate

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/eval.py --check
python3 -m py_compile scripts/*.py
```

Validation enforces a single discoverable skill, complete routes, a fully
reachable reference graph, valid links and metadata, and the evaluation schema.

### Differential evaluation

Agent runs require a dedicated evaluation profile. Do not point the harness at
your normal home or live agent configuration. For a single runner,
`--profile-dir` may name that runner's dedicated profile; multi-runner commands
expect `cursor/`, `codex/`, and `claude/` profiles beneath the directory.
Authenticate each profile before running paid evaluations.

```bash
python3 scripts/eval.py --run \
  --runner cursor \
  --profile-dir /path/to/eval-profiles/cursor \
  --candidate .
```

When `--baseline` is omitted, the harness uses the committed snapshot in
`evals/baseline-runtime.tar.gz`. Pass `--baseline /path/to/skill` or
`--without-skill` for other comparisons.

```bash
python3 scripts/eval.py --smoke \
  --runner all \
  --profile-dir /path/to/eval-profiles \
  --candidate .
```

```bash
python3 scripts/eval.py --matrix \
  --profile-dir /path/to/eval-profiles \
  --candidate .
```

The release matrix defaults to three attempts per provider.

The harness stores ignored, redacted evidence under `evals/.runs/` (event
streams, responses, diffs, config, timings, checks, grading, summaries).
Results use `PASS`, `FAIL`, or `INCONCLUSIVE`; missing or malformed evidence
never contributes to a pass rate. Semantic grading runs only when a provider
adapter can technically disable tools; runners without an enforceable tool-free
judge record rubric results as `INCONCLUSIVE`. Paid model evaluations remain
manual and outside CI.

### Portability

Portable frontmatter contains only `name` and `description`; `agents/openai.yaml`
carries Codex interface metadata. Host extensions are documented as extensions,
not in the common contract. Flows degrade gracefully when hosts lack agents,
worktrees, trackers, browsers, or research tools: parallel review and design can
run sequentially, and `implement-spec` falls back to ordinary `implement`
without isolated agents or worktrees.

### Attribution

Bundled flow material derived from
[mattpocock/skills](https://github.com/mattpocock/skills) remains under its MIT
license. See `references/flows/NOTICE`.

### Installer details

Each install carries a hash manifest. Updates remove only unchanged managed
files and preserve local modifications as conflicts. Updates are staged and
rolled back per destination if a write fails. `--force` replaces only a modified
managed file that still exists in the current payload; modified stale or legacy
files and conflicting directories remain conflicts even with `--force`. The
install name comes from root skill metadata. Source payload symlinks and nested
destination symlinks are rejected rather than followed.
