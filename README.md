<div align="center">
  <img src="assets/needquality.png" alt="NeedQuality" width="780">
</div>

<h3 align="center">Focused guidance for reliable software changes</h3>

## What it is

NeedQuality is one routed agent skill for software delivery and agent
documentation. The root skill chooses one job or flow, loads only the relevant
language, framework, UI, research, or trust references, and requires fresh
evidence for completion claims.

Every bundled workflow is a plain reference behind the root router. Installing
NeedQuality creates one discoverable `SKILL.md`, so a host cannot accidentally
register the bundled flows as competing skills.

## Install and update

Use Python 3.11 or newer. Runtime scripts use only the standard library.

```bash
python scripts/install.py --all
```

`--all` creates or updates the standard skill roots for the shared Agent Skills
location, Claude, Cursor, and Codex. Other useful forms:

```bash
python scripts/install.py
python scripts/install.py --check
python scripts/install.py --platform codex --platform cursor
python scripts/install.py --root /path/to/custom/skills
python scripts/install.py --force
```

Without a target option, the installer updates existing NeedQuality installs.
`--check` reports missing, changed, stale, and locally modified files without
writing. Each install carries a hash manifest. Updates remove only unchanged
files previously managed by NeedQuality and preserve local modifications as
conflicts. Use `--force` only when those exact managed modifications should be
replaced.

Codex uses `$CODEX_HOME/skills`, falling back to `~/.codex/skills`. The other
standard roots are `~/.agents/skills`, `~/.claude/skills`, and
`~/.cursor/skills`.

## Routing

Routing follows four rules:

1. An explicitly named flow outranks an inferred generic job.
2. The longest matching phrase wins.
3. One primary job or flow is selected.
4. Applicable language, framework, UI, research, and trust references are
   added in table order.

Multiple jobs or flows are composed only when the request clearly asks for
distinct operations. Active runs emit the canonical route trace documented in
`SKILL.md`; unrelated question-only requests do not.

Use the inventory command instead of relying on copied counts:

```bash
python scripts/validate.py --stats
```

## Portability

The portable frontmatter contains only `name` and `description`.
`agents/openai.yaml` carries Codex interface and invocation metadata. Host
extensions such as `disable-model-invocation` are documented as extensions,
not placed in the common contract.

Flows use independent agents, worktrees, trackers, browsers, and research tools
only when the host exposes and authorizes them. Parallel review and design can
run sequentially with separate findings. `implement-spec` falls back to the
ordinary `implement` flow when isolated agents or worktrees are unavailable.

## Validate

The deterministic checks are safe for local development and CI:

```bash
python -m unittest discover -s tests -v
python scripts/validate.py
python scripts/eval.py --check
python -m py_compile scripts/*.py
```

Validation enforces a single discoverable skill, complete and unambiguous
routes, a fully reachable reference graph, valid links and metadata, and the
evaluation schema.

## Differential evaluation

Agent runs require a dedicated evaluation profile. Do not point the harness at
your normal home or live agent configuration. For a single runner,
`--profile-dir` may name that runner's dedicated profile. Multi-runner commands
expect `cursor/`, `codex/`, and `claude/` profiles beneath the supplied
directory. Authenticate each profile through its provider's current login
flow before running paid evaluations.

Run the full candidate-versus-baseline suite on the reference runner:

```bash
python scripts/eval.py --run \
  --runner cursor \
  --profile-dir /path/to/eval-profiles/cursor \
  --candidate .
```

When `--baseline` is omitted, the harness uses the committed, hash-verified
implementation-start snapshot in `evals/baseline-runtime.tar.gz`. Pass
`--baseline /path/to/skill` to compare against another skill, or
`--without-skill` for an explicit no-skill comparison.

Smoke-test native discovery on configured providers:

```bash
python scripts/eval.py --smoke \
  --runner all \
  --profile-dir /path/to/eval-profiles \
  --candidate .
```

Run the release matrix, which defaults to three attempts per provider:

```bash
python scripts/eval.py --matrix \
  --profile-dir /path/to/eval-profiles \
  --candidate .
```

The harness stores ignored, redacted evidence under `evals/.runs/`: normalized
tool events, final responses, workspace diffs, timings, deterministic checks,
semantic grading, and paired summaries. A missing runner, malformed event
stream, absent final response, or failed judge is `INCONCLUSIVE`, never a pass.
Paid model evaluations are manual and are not part of CI.

## Attribution

Bundled flow material derived from
[mattpocock/skills](https://github.com/mattpocock/skills) remains under its MIT
license. See `references/flows/NOTICE`.
