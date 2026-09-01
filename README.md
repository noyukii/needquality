<div align="center">
  <img src="assets/needquality.png" alt="NeedQuality" width="780">
</div>

<h3 align="center">Focused guidance for reliable software changes</h3>

## What it is

NeedQuality is a set of independently triggered agent skills for software
delivery. Each skill owns one kind of work (implementing, fixing, reviewing,
testing, shipping), one domain (a language, SQL, trust boundaries, web UI),
or one process (planning, architecture, docs, research, ops). A host loads a
skill only when the request matches that skill's description, so a coding
turn pays for the one or two skills it needs instead of a router that fires on
everything.

Every skill starts with the same short contract: scope the change, read the
target and its neighbours, patch the smallest slice, prove it with a fresh
command, and close with `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE` plus the
evidence. Skills hand off to each other by name in prose (for example, "use
`needquality-review` for the two-axis pass") and never link across skill
directories, so each one installs and works on its own.

## Skills

| Skill | What it does | Loads when |
|---|---|---|
| `needquality-implement` | Smallest defensible code change: ladder of what to build, patch rules, fresh proof, compact close; one dependency bump per slice | implement, add, build, create, update, change code, upgrade deps |
| `needquality-fix` | Reproduce, root-cause patch, re-run the red command; hard-bug diagnosis loop; first failing CI check; merge conflicts by intent | fix, bug, broken, diagnose, CI is red, merge conflict |
| `needquality-review` | Evidence-backed review with docs, guidelines, and a command; two-axis Standards/Spec review; live browser verification | review, look over, review since, verify in the browser |
| `needquality-cleanup` | Strip slop from a named diff, refactor, simplify, one named improvement, one measured optimization; slop-tell lookup script | clean up, deslop, refactor, simplify, optimize |
| `needquality-test` | Tests at public seams in the existing runner, red-green TDD at agreed seams, product QA pass | add tests, coverage, tdd, QA this |
| `needquality-ship` | Commit the named diff, open a PR/MR, changelog for a range, cut a release, requested rebase or squash | commit, open a PR, changelog, cut a release, rebase onto |
| `needquality-javascript` | JS/TS rules: promises and fetch, prototype pollution, DOM and Node sinks, TypeScript parsing, React, Next.js, React Native, Vue | editing .js .ts .jsx .tsx .vue .svelte |
| `needquality-python` | Python rules: parsing over `.get` chains, exceptions over silent zeros, ORM hygiene; Django and FastAPI references | editing .py |
| `needquality-go` | Go rules: wrapped errors, contexts and deadlines, bounded goroutines, client timeouts | editing .go |
| `needquality-rust` | Rust rules: the crate's error type and `?`, ownership over clones, async hygiene | editing .rs |
| `needquality-swift` | Swift/SwiftUI rules: state ownership, navigation, structured concurrency, optionals | editing .swift |
| `needquality-java` | Java rules: exceptions, nulls, streams, concurrency, JDBC/JPA; Spring Boot reference | editing .java, Maven/Gradle, Spring |
| `needquality-kotlin` | Kotlin rules: nullability, coroutines, sealed types, Gradle DSL; Android reference | editing .kt/.kts, Android, Compose |
| `needquality-csharp` | C# rules: nullable types, async and cancellation, disposal, EF Core; ASP.NET Core reference | editing .cs/.csproj/.razor |
| `needquality-ruby` | Ruby rules: Bundler, exceptions over nil, enumerables; Rails reference | editing .rb/.rake, Gemfile, Rails |
| `needquality-php` | PHP rules: Composer, strict types, PDO, escaping; Laravel reference | editing .php, composer.json, Laravel |
| `needquality-elixir` | Elixir rules: pattern matching, tagged tuples, OTP, Ecto; Phoenix reference | editing .ex/.exs, mix.exs, Phoenix |
| `needquality-cpp` | C/C++ rules: ownership and RAII, bounds and lifetimes, overflow, sanitizers | editing .c/.h/.cc/.cpp/.hpp |
| `needquality-shell` | Shell rules: strict mode, quoting, arrays, traps, portability, ShellCheck | editing .sh/.bash, shell shebangs |
| `needquality-dart` | Dart/Flutter rules: null safety, async and streams, widget state, pubspec | editing .dart, pubspec.yaml |
| `needquality-zig` | Zig rules: repo Zig version, allocators and defer, error unions, comptime | editing .zig, build.zig |
| `needquality-lua` | Lua rules: runtime version, locals, pcall, metatables, rockspecs | editing .lua/.rockspec |
| `needquality-docker` | Container rules: pinned bases, lockfile installs, layer order, non-root, health checks, secrets outside the image | Dockerfile, compose files |
| `needquality-sql` | Keyed writes, transactions, identifier allowlists, N+1 and pagination, Postgres pooling, expand-contract migrations | .sql, .prisma, schema, migrate, Postgres/Supabase/Neon |
| `needquality-trust` | Session-scoped authz, CSRF and JWT, bounded fan-out, timeouts and 2xx checks, idempotent retries, atomic reservations, uploads, webhooks, secrets | HTTP handlers, auth, money, uploads, webhooks, outbound I/O, secure, harden |
| `needquality-ui` | Web surfaces: semantics, focus, states, tokens, layout, type, color, motion, assets, landing originality, a11y audits, i18n, UI copy | web pages, components, design systems, a11y, i18n, landing page |
| `needquality-plan` | Grilling rounds, domain model and ADRs, spec, tracer-bullet tickets, wayfinder map, tracker detection, triage, prototype | grill me, write a spec, break into tickets, triage, prototype |
| `needquality-architecture` | Deep-module vocabulary, architecture scan with HTML report, dependency-cruiser entry-point rules | architecture, deepen, seams, dependency-cruiser |
| `needquality-docs` | The one requested document in its file's voice; writing for agents (skills, AGENTS.md, pointers) | document, README, AGENTS.md, write a skill |
| `needquality-research` | Bounded research: L0-L3 depth, required slots, cited primary sources, explicit stop | research this, primary sources, unfamiliar API |
| `needquality-ops` | One signal in the installed observability stack, bash wizards for manual provisioning, handoff notes | instrument, add metrics, wizard, handoff |

Descriptions for all thirty-one skills total about 2,800 tokens of
always-loaded metadata (`python3 scripts/validate.py --stats` prints the
current number; the validator caps it at 3,200).

## Install and update

Use Python 3.11 or newer. Runtime scripts use only the standard library.

```bash
python3 scripts/install.py --all
```

`--all` installs every skill into the standard roots for the shared Agent
Skills location, Claude, Cursor, and Codex, one directory per skill
(`~/.cursor/skills/needquality-fix/`, and so on). Other useful forms:

```bash
python3 scripts/install.py                              # update existing installs
python3 scripts/install.py --check                      # report drift, write nothing
python3 scripts/install.py --platform codex --platform cursor
python3 scripts/install.py --root /path/to/custom/skills
python3 scripts/install.py --skill fix --skill review   # a subset
python3 scripts/install.py --force                      # replace modified managed files
```

Each installed skill carries a hash manifest. Updates remove only unchanged
files previously managed by NeedQuality and preserve local modifications as
conflicts. Writes are staged and rolled back per destination if one fails. An
older single-directory `needquality/` install is retired automatically on the
next run when its files are unmodified; modified files stay behind as
conflicts.

Codex uses `$CODEX_HOME/skills`, falling back to `~/.codex/skills`. The other
standard roots are `~/.agents/skills`, `~/.claude/skills`, and
`~/.cursor/skills`.

The `skills/<name>/SKILL.md` layout is the one the
[`skills` CLI](https://github.com/vercel-labs/skills) expects, so
`npx skills add noyukii/needquality --skill needquality-fix` (or `--skill '*'`)
also works for hosts it supports.

## How the skills fit together

Each skill is self-contained. When a job needs another skill, the body says so
by name, and the host loads it if the request matches:

- Job skills (`implement`, `fix`, `review`, `cleanup`, `test`, `ship`) name the
  domain skill for the files they touch and `needquality-trust` for any
  boundary work.
- `needquality-test` defers seam questions to `needquality-architecture` and
  the post-green refactor to `needquality-review`.
- `needquality-review` reads the repo tracker through `needquality-plan` for
  the two-axis Spec axis.
- `needquality-plan` hands implementation to `needquality-implement` and
  research passes to `needquality-research`.

## Portability

The portable frontmatter of every skill contains only `name` and
`description`. Each skill's `agents/openai.yaml` carries Codex interface and
invocation metadata. Host extensions such as `disable-model-invocation` are
documented as extensions, never placed in the common contract.

Flows use independent agents, worktrees, trackers, browsers, and research tools
only when the host exposes and authorizes them. Parallel review and design can
run sequentially with separate findings. `implement-spec` falls back to the
ordinary `implement` flow when isolated agents or worktrees are unavailable.

## Validate

The deterministic checks are safe for local development and CI:

```bash
python3 -m unittest discover -s tests -v
python3 scripts/validate.py
python3 scripts/eval.py --check
python3 -m py_compile scripts/*.py
```

`validate.py` checks every skill: frontmatter keys, a description that states
when to load it, no trigger phrase claimed by two skills, every bundled file
linked directly from its `SKILL.md`, no links across skill directories,
cross-skill mentions that resolve to real skills, the shared contract block
copied verbatim from `shared/contract.md`, Codex metadata, portability
markers, and the total metadata token budget. CI also runs the Agent Skills
reference validator over each skill directory.

## Differential evaluation

Agent runs require a dedicated evaluation profile. Do not point the harness at
your normal home or live agent configuration. For a single runner,
`--profile-dir` may name that runner's dedicated profile. Multi-runner commands
expect `cursor/`, `codex/`, and `claude/` profiles beneath the supplied
directory. Authenticate each profile through its provider's current login
flow before running paid evaluations.

Each eval names the skills it expects to load. Deterministic checks read the
tool event stream for `skill_loaded` / `skill_not_loaded`, the workspace diff
for `diff_contains` / `diff_not_contains` / `no_new_files`, and the final
response for content checks; rubric items are graded semantically. Negative
evals (general questions, prose polishing, teaching, personal workflows) assert
that no NeedQuality skill loads at all.

Run the full candidate-versus-baseline suite on the reference runner:

```bash
python3 scripts/eval.py --run \
  --runner cursor \
  --profile-dir /path/to/eval-profiles/cursor \
  --candidate .
```

When `--baseline` is omitted, the harness uses the committed, hash-verified
snapshot in `evals/baseline-runtime.tar.gz`. That snapshot is the pre-split
single-skill router and installs as `needquality/`; the candidate installs one
directory per skill. Pass `--baseline /path/to/skill` to compare against
another checkout, or `--without-skill` for an explicit no-skill comparison.

Smoke-test native discovery on configured providers:

```bash
python3 scripts/eval.py --smoke \
  --runner all \
  --profile-dir /path/to/eval-profiles \
  --candidate .
```

Run the release matrix, which defaults to three attempts per provider:

```bash
python3 scripts/eval.py --matrix \
  --profile-dir /path/to/eval-profiles \
  --candidate .
```

The harness stores ignored, redacted evidence under `evals/.runs/`: raw and
normalized event streams, final responses, workspace diffs, exact request and
runner configuration, timings, deterministic checks, semantic grading, and
paired summaries. Result rows use `PASS`, `FAIL`, or `INCONCLUSIVE`; missing or
malformed evidence never contributes to a pass rate.

Semantic grading runs only when a provider adapter can technically disable
tools. Read-only, planning, or ask modes are not substitutes. A runner without
an enforceable tool-free judge records rubric results as `INCONCLUSIVE`. Paid
model evaluations remain manual and outside CI.

## Attribution

Flow material derived from
[mattpocock/skills](https://github.com/mattpocock/skills) remains under its MIT
license. See [`NOTICE`](NOTICE); each derived reference file carries the
attribution in its first line.
