# Research notes (Firecrawl, 2026-08-18)

Sources gathered with Firecrawl search + scrape. This file is background
for iterating `noslop`; the agent writing code should follow SKILL.md, not
this essay.

## What people mean by *good* (not “clean”) code

- **Complexity is the enemy** ([Grug](https://grugbrain.dev/)). Say no to
  speculative features and early abstractions. Named intermediates so a
  debugger can see the decision. Factor only at a natural cut point.
- **Duplication is cheaper than the wrong abstraction**
  ([Sandi Metz](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction)).
  Copy twice; extract on the third time. If a shared helper grows
  caller-specific flags, inline it back.
- **Easy to delete** ([tef](https://programmingisterrible.com/post/139222674273/write-code-that-is-easy-to-delete-not-easy-to)).
  Lines are spent, not produced. Isolate what will change. Repeat yourself
  to avoid a dependency; don’t repeat yourself to manage one.
- **Optimize for change, not looks** (Dan Abramov, “Goodbye Clean Code”;
  also [gerlacdt’s Clean Code critique](https://gerlacdt.github.io/blog/posts/clean_code/)).
  Tiny functions and aggressive DRY often make the next requirement harder.

## What developers hate in AI code

Pattern catalog (language-neutral) from
[scanaislop’s 20 examples](https://scanaislop.com/blog/20-ai-slop-code-examples-and-the-better-pattern)
plus maintainer/reviewer complaints:

### Fake resilience
1. Swallowed exception (catch, log, return empty success)
2. Catch-and-rethrow with no context
3. Universal fallback (every failure becomes cached/default data)
4. Retry without a budget (infinite, no jitter, no idempotency)

### Fake safety
5. Type-system escape hatch (`as T` on unknown)
6. Validate everywhere instead of once at the boundary
7. Defensive checks against states the type already excludes
8. Boolean blindness (several unexplained true/false args)

### Unreadable / undeletable structure
9. Narrative comments (“increment the counter”)
10. Generic names (`data`, `result`, `handler`)
11. One-call wrappers
12. Oversized orchestration (parse + business + IO + HTTP in one blob)
13. Duplicate of an existing helper (agent did not search the tree)
14. Dead helper from an abandoned approach

### Tests that lie
15. Deleting or skipping the failing test as the “fix”
16. Tautological tests (reimplement the function and compare)
17. Snapshot-everything until CI is green

### Scope and supply chain
18. Hallucinated dependency / slopsquatting
19. Speculative config and flags “for later”
20. Drive-by rewrite of unrelated files while fixing one bug

HN thread [Ask HN: How to deal with AI generated sloppy code](https://news.ycombinator.com/item?id=41677207)
and GitHub’s [Copilot security discussion](https://github.com/orgs/community/discussions/194034)
add: mixed indent, plausible-but-wrong APIs, typosquat packages that CI
then installs, and “I cannot explain this patch to a maintainer.”

[TRIM (arXiv:2607.18161)](https://arxiv.org/abs/2607.18161) names the
residue **CodeSlop**: speculative edits, abandoned hypotheses, and
temporary changes that survive into the final patch because the agent
iterated toward green tests. Verbosity is not style — it is leftover
search.

## What research says AI gets wrong (often)

| Finding | Source |
|---|---|
| Experienced OSS developers were **19% slower** with early-2025 AI tools while *feeling* 20% faster | [METR RCT](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) |
| Refactoring share of diffs: **25% (2021) → <10% (2024)** | [GitClear 2025](https://www.gitclear.com/ai_assistant_code_quality_2025_research) (211M lines, 2020–2024) |
| Copy/paste **exceeded moved (reuse) code for the first time**; cloned blocks 8.3% → 12.3% | same |
| Short-term churn nearly **doubled** | same |
| AI-co-authored PRs had **~1.57× more security findings overall; 2.74× for XSS** | [CodeRabbit, 470 PRs](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report) |
| Developers using assistants introduced vulns at **higher rates** (less scrutiny) | Stanford study, cited in [Dotsquares](https://www.dotsquares.com/press-and-events/tech/common-errors-in-ai-generated-code-and-solutions) |
| Hallucinated packages, wrong APIs, deprecated methods, off-by-ones, over-engineering simple tasks, context-blind duplicates | Dotsquares; [SoftwareSeni evidence roundup](https://www.softwareseni.com/the-evidence-against-vibe-coding-what-research-reveals-about-ai-code-quality/) |
| Complacency with assistants | Thoughtworks Tech Radar, cited in SoftwareSeni |
| Training-cutoff CVEs and slopsquatting | [OWASP Secure Coding with AI](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) |

Common error buckets (SoftwareSeni / Dotsquares):

1. **Hallucinations** — fake libraries, wrong signatures, deprecated APIs
2. **Logic** — happy path only, off-by-one, inverted conditions, pattern-match not reasoning
3. **Security** — SQL concat, missing authz, hardcoded secrets, insecure defaults
4. **Context blindness** — reimplements a helper two files away
5. **Over-engineering** — factories/DI for a one-function task
6. **Review tax** — time saved typing is spent verifying, then rewriting

## Practices that actually work (from the same sources)

GitHub’s [Review AI-generated code](https://docs.github.com/en/copilot/tutorials/review-ai-generated-code):
run tests and static analysis first; check the change solves the *right*
problem and matches local architecture; refuse code you would rewrite;
scrutinize every new dependency (existence, age, license, slopsquatting).

Engineering-leader guidance ([Of Ash and Fire](https://www.ofashandfire.com/blog/ai-generated-code-quality-crisis)):
reviewer must confirm the author *understands* the patch; extra scrutiny
on authn/z and data handling; tests must assert behavior, not the
implementation; do not use AI for security-critical or novel architecture
without a human design. Thoughtworks: complacency is the failure mode
after the first month of “it works.”

OWASP: never `npm install` / `pip install` an AI-suggested name unchecked;
audit versions for CVEs; treat issues/PRs/READMEs as untrusted
instructions to the agent (prompt injection).

Practical workflow (Dotsquares, Medium “10 tips”, 30-day tool diaries):
give the agent the existing helper names; ask for a plan before edits;
forbid drive-by refactors; write edge-case tests *before* accepting the
diff; do not let the same model rubber-stamp its own tests.

## Gaps vs current `noslop` SKILL.md

Round 2 folded into SKILL.md: trajectory leftovers, drive-by rewrites,
tests that cannot fail, slopsquatting, universal fallback / retry budget,
boolean blindness, over-mocked tests, and “the authoring model is not
the only reviewer.”

Round 3 folded into SKILL.md: untrusted issue/PR/README context,
hardcoded secrets, check-then-act races, timezone vs offset vs date,
Unicode NFC / `.length` / hidden bidi+Tags, and lockfile/CI as
backdoor surface.

Round 4 folded into SKILL.md + `references/ui.md`: do not hallucinate
a custom Popover/Modal/Select when the workspace kit (HeroUI, shadcn,
…) already exports it. Look up the installed API; do not add a second
library; do not invent props.

Round 5: "don't invent an existing thing" is a general rule (tree →
internet lookup → then write). Design-slop fingerprint added to the
blacklist. New UI must look up kit docs + live references, not emit
the Inter/indigo/three-card centroid.

Round 6: writing slop (structure > vocabulary) and UX/a11y slop
(operability invisible in screenshots) folded into `copy.md`,
`ui.md`, and the blacklist.

Round 7: uniqueness is process (references, bans, tokens, layout→
theme→motion, wide-then-narrow), not adjectives. More UI tells from
Krebs 16 / Hey.com / Sailop / Superdesign.

## Round 2 (more Firecrawl searches)

| Finding | Source |
|---|---|
| RCT: 16 experienced OSS developers were **19% slower** with early-2025 Cursor/chat/autocomplete, while forecasting speedups | [METR](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/) |
| Copilot completed 1,689 CWE-oriented programs; **~40% vulnerable** | Pearce et al., [Asleep at the Keyboard](https://arxiv.org/abs/2108.09293) (IEEE S&P 2022) |
| AI PRs: **~1.7× more issues**, 75% more logic bugs, **>3× readability** issues, ~2× missing error handling, **~1.57× security overall / 2.74× XSS** | [CodeRabbit report](https://www.coderabbit.ai/blog/state-of-ai-vs-human-code-generation-report) (470 PRs) |
| Slopsquatting is live: agents invent package names, attackers register them, other agents spread the name | [Aikido](https://www.aikido.dev/blog/slopsquatting-ai-package-hallucination-attacks), [Mend](https://www.mend.io/blog/the-hallucinated-package-attack-slopsquatting/), CSA note |
| Copilot tests infer expected values from the implementation: tautology, mock-everything, echo snapshots, happy-path-only | [Autonoma](https://getautonoma.com/blog/copilot-generated-tests-quality-pitfalls) |
| Godot tightened contribution policy against AI slop PRs; maintainers drowning; contributor must understand the patch | [Hackaday](https://hackaday.com/2026/07/03/godots-new-contributing-policy-adds-barriers-for-ai-slop/), [Godot forum](https://forum.godotengine.org/t/changes-to-godot-contribution-policies-stricter-rules-against-ai-contributions/140986) |
| **Hold** on complacency with AI-generated code: GitClear churn + Microsoft “AI confidence vs critical thinking” | [Thoughtworks Radar](https://www.thoughtworks.com/en-us/radar/techniques/complacency-with-ai-generated-code) |
| Training on public GitHub raises copyleft/derivative-work questions; ToS covers GitHub-hosted training data, not a free pass to paste mystery snippets | [FOSSA](https://fossa.com/blog/analyzing-legal-implications-github-copilot/) |

### Copilot test pitfalls (for the skill)

1. Assert the function against itself (tautology)
2. Mock the unit under test; verify the mock
3. Snapshot/echo that re-blesses any change
4. Happy path only — no empty, null, boundary, error

Root cause: the model’s only source of “expected” is the code it just wrote.
Give it a spec number, or write the expected value yourself.

### Maintainer bar

Godot/Mesa/Hackaday commenters: you cut/paste only what you can defend;
extensive tests catch a fair number of model bugs; “tell AI to do
something without domain knowledge” is the disaster mode. Skill atrophy
(“use it or lose it”) is a stated fear.

## Round 3 (races, time, unicode, injection, secrets)

Firecrawl keyless search/scrape hit the free-tier rate limit this
round. Developer index still returned prompt-injection hits
(`.firecrawl/round3/dev-prompt-injection.json`). Remainder from the
already-scraped OWASP cheat sheet plus targeted fetches of the
primary papers/posts.

| Finding | Source |
|---|---|
| Agents write code that is correct *in isolation*. Check-then-act (SELECT then UPDATE) double-books; single-request tests stay green | [Rusin](https://blog.alexrusin.com/claude-code-race-condition/) (booking endpoint); ECOA agent benchmarks (deadlock / lock-across-I/O) |
| Offset ≠ timezone. `new Date("YYYY-MM-DD")` is UTC midnight; birthdays stored as UTC instants shift a day. Cron at 1:30 local runs twice on fall-back | [Timezoners](https://www.timezoners.com/blog/time-zones-in-code-engineering-gotchas); [Multigrid](https://multigrid.ai/learn/llm-date-reasoning) (models have no clock, conflate offset with IANA) |
| Time-zone mistakes are the largest class of real Python datetime bugs | MSR 2025, *It’s About Time* ([DOI](https://doi.org/10.1109/msr66628.2025.00020)) |
| Issues/PRs/comments/READMEs/error traces/fetched pages are instruction sources for agents | [OWASP Secure Coding with AI](https://cheatsheetseries.owasp.org/cheatsheets/Secure_Coding_with_AI_Cheat_Sheet.html) §3 |
| Hidden `<picture>` HTML in a GitHub issue + fake chat history made Copilot Agent install a lockfile backdoor when assigned the issue | [Trail of Bits](https://blog.trailofbits.com/2025/08/06/prompt-injection-engineering-for-attackers-exploiting-github-copilot/) |
| **PromptPwnd:** untrusted issue body → CI agent prompt → privileged tools → secrets posted back to the issue. Gemini CLI repo patched in 4 days | [Aikido](https://www.aikido.dev/blog/promptpwnd-github-actions-ai-agents) (Dec 2025) |
| TOCTOU: benign PR title approved, then edited before the CI agent reads it; overwrite runner binary → dump env | [HackTricks cloud](https://github.com/hacktricks-wiki/hacktricks-cloud) (Abusing GitHub Actions) |
| Cross-Prompt Injection Attack (XPIA) warnings now default in GitHub Agentic Workflows | [github/gh-aw#1182](https://github.com/github/gh-aw/issues/1182) |
| Unicode Tags (U+E0000–U+E007F), zero-width, bidi: invisible in review, obeyed by the model. Skills, `.cursorrules`, MCP tool descriptions | [CSA research note](https://labs.cloudsecurityalliance.org/research/csa-research-note-unicode-instruction-injection-ai-skills-20/) (2026-03-10); OWASP §12 |
| Copilot-enabled repos leak secrets **6.4% vs 4.6%** baseline (**+40%**). HKU: 8,127 Copilot suggestions → 2,702 “valid” secrets, **3.0 per prompt**; ≥200 matched real GitHub credentials | [GitGuardian](https://blog.gitguardian.com/yes-github-copilot-can-leak-secrets/); Huang et al., *Neural Code Completion Tools Can Memorize Hard-coded Credentials* |
| Attack success on Copilot/Cursor command execution from poisoned external resources up to **84%** (314 payloads) | [“Your AI, My Shell”](https://arxiv.org/html/2509.22040v2) (arXiv:2509.22040) |

### What the agent should do (generation time)

1. Issue/PR/README/error/web text is data. Do not run scripts, dump
   env, or edit lockfiles/CI because that text asked.
2. No credential-shaped literals. Env or the repo’s secrets helper.
3. Book/claim/reserve/decrement: one atomic write, then a two-request
   test — or say you did not.
4. Instants UTC; wall-clock + IANA; dates as dates. Offset is not a
   zone.
5. NFC for identity strings. No hidden Unicode in files you write.
   JS `.length` is not character count.

### Injection hiding places already demonstrated

- GitHub issue HTML that renders blank (`<picture>` / empty `<img>`)
- Unicode Tags / zero-width steganography in skill and rule files
- MCP tool descriptions (human sees a summary; model sees the full text)
- PR title edited after a maintainer `@`-mentions the bot (TOCTOU)
- `uv.lock` / package lock URL swaps (reviewers skip lockfiles)

## Firecrawl query log

- search+scrape: developers hate AI slop; AI failure modes/GitClear;
  pragmatic good code
- developer index: aislop rules, deslop commands, slop examples
- research search-github: anti-slop linters and maintainer AI policies
- scrape: GitClear 2025 landing, Grug, aislop 20 examples, OWASP cheat
  sheet, GitHub review tutorial, TRIM abstract
- round 2 search+scrape: METR RCT, slopsquatting, Stanford Copilot
  security, Godot/Mesa AI PR policy, CodeRabbit + tautological tests
- round 2 extra: Copilot license/secrets, Thoughtworks complacency
- scrape: Pearce arXiv, Autonoma Copilot tests, Godot policy thread
- round 3 developer: prompt injection via issues/Actions (HackTricks,
  PromptPwnd, XPIA, Docker horror stories)
- round 3 search/scrape: keyless 429; used OWASP scrape + fetches of
  Rusin, Aikido PromptPwnd, GitGuardian, Timezoners, Trail of Bits, CSA Unicode note
- round 4 search: keyless 429 again; UI-reuse from DEV “UI drift”,
  shadcn/coss/HeroUI agent skills (use kit primitive, fetch docs)
- round 5: keyless 429; design-slop catalogs (uxskill, 925studios,
  Superdesign, Sailop) + impeccable refuse list
- round 6: writing (SEW 30, Wikipedia AI signs, UMD/DeepMind,
  llmbestpractices) + UX/a11y (uxskill seven, Sailop 90+, Pixelslop)
- round 7: uniqueness workflows (Superdesign, Zenn, Zhou, DESIGN.md);
  Krebs 16 / Hey.com / next-centroid fonts
- round 8: mix-ins from sibling skills (ponytail, vercel-react,
  composition, WIG, ui-ux-pro-max, shadcn/heroui, firecrawl DESIGN.md,
  tdd seams) — generation-time subset only; do not swallow those skills

## Round 4 (UI kit hallucination)

The tell: repo already depends on HeroUI (`@heroui/react`) and the
agent writes `function Popover` with `useState` + `absolute` +
click-outside instead of importing the kit component. Same GitClear
adjacent-add, applied to overlays.

| Finding | Source |
|---|---|
| Models default to the training-set UI (generic Tailwind / shadcn-shaped overlays) when the project's kit is not in the immediate context. Screens then *drift*: radius, color, spacing almost-right, five different freelancers | [Veljanoski, “UI drift”](https://dev.to/dejan_veljanoski/your-ai-coding-tools-are-ignoring-your-design-system-heres-how-i-fixed-it-161j) |
| Agent skills for real kits already encode the rule: search the registry / fetch docs *before* markup; compose, don't reinvent | [shadcn skill](https://ui.shadcn.com/), HeroUI v3 skill (“always fetch v3 docs”), coss skill (“existing primitives first”) |
| Rebuilding overlays drops what the kit paid for: focus trap, portal, keyboard, aria. A nested Select that “doesn't work” is usually a portal/container prop, not a reason to write a new component | HeroUI modal+select issues; kit `portalContainer` / `container` APIs |

### Agent checklist

1. `package.json` + nearby imports → name the one kit.
2. Grep / docs / types for Popover, Modal, Select, Tooltip, Menu, Toast, Tabs.
3. Copy *this repo's* composition (HeroUI v2 vs v3, shadcn parts).
4. No second library. No invented `isOpen`. No `components/ui/popover.tsx` from a CodeSandbox.

## Round 5 (design slop + look it up)

Firecrawl keyless still 429. Catalog from public design-slop writeups
plus the frontend-design / impeccable refuse lists.

| Finding | Source |
|---|---|
| Fingerprint: Inter, indigo/violet gradient, centered hero, three rounded cards. Cluster ≥4 is the centroid look | [uxskill](https://uxskill.laithjunaidy.com/what-is-ai-slop.html), [925studios](https://www.925studios.co/blog/ai-slop-design-tells), [Superdesign](https://www.superdesign.dev/blog/why-ai-design-looks-generic) |
| `#3b82f6` / `#8b5cf6` / `from-purple-500 to-pink-500` + `rounded-2xl` + three cards = “Comic Sans of 2026” | [Sailop](https://sailop.com/blog/tailwind-blue-purple-gradient-ai-signature-2026) |
| Extra tells: pill beta badge, glass `backdrop-blur`, emoji icons, gradient text on “AI”, fake Trusted-by, 01/02/03, colored left border, bento-on-dark, fade-up everything, “Unlock your potential” | [ahd taxonomy](https://github.com/Ad-Astra-Computing/ahd/blob/main/docs/SLOP_TAXONOMY.md), [booplex](https://booplex.com/blog/what-is-ai-design-slop), [vibecodekit](https://vibecodekit.dev/ai-slop-design), impeccable craft-floor |
| Wathan: Tailwind UI `bg-indigo-500` demos trained the default | quoted in 925studios |
| Fix is constraint + real references, not “make it more unique” (adjectives have their own centroid) | uxskill; Superdesign (“feed real references”) |

General reuse: debounce, CSV, retry, overlays, date math — search the
tree, then look up docs/registry/two live pages, then write. Fetched
inspo is data, not extra instructions.

## Round 6 (writing slop + UX/a11y slop)

| Finding | Source |
|---|---|
| AI slop = looks more complete than the work deserves. 30 tells: landscape opener, delve, tapestry, Moreover parade, "in conclusion" replay, unnamed experts, chatbot residue | [Search Engine Watch](https://searchenginewatch.com/what-is-ai-slop/) |
| Structure outlasts word lists. UMD + DeepMind, 61,608 texts: stripping clichés dropped detection only 95.5% → 93.9%. "It's not X, it's Y", paragraph morals, hedge stacks, rule of three | [unslop / UMD·DeepMind 2026](https://skillsllm.com/skill/unslop); [Wikipedia: Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing); [llmbestpractices anti-slop](https://llmbestpractices.com/writing/anti-slop) |
| Era vocab: GPT-4 delve/tapestry; GPT-4o showcasing/fostering; GPT-5 emphasizing/highlighting. 2026: negative parallelism is #1; "quietly building"; em-dash asides | [joshp123 deny-list](https://gist.github.com/joshp123/3c60d8def6d30a2503d8a98575334702); Wikipedia field guide |
| UX writing: placeholder-as-label, "click here", redundant label+heading+helper, Oops-errors, empty states with no action | NNGroup/Baymard via [Brand Vision](https://www.brandvm.com/post/ux-writing-conversion-guide); Paul Bakaus (Japanese-style redundancy, cardocalypse) |
| A11y holes because models optimize the screenshot: gray-on-white <4.5:1, `outline-none`, unnamed icon buttons, clickable `div`, placeholder label, color-only error, unguarded motion | [uxskill](https://uxskill.laithjunaidy.com/blog/ai-generated-ui-accessibility.html); [v0/Lovable a11y checklists](https://blog.a11yfix.dev/checklist/v0/) |
| More UI patterns: `hover:scale-105`, white-on-gray-50 cards, inverted dark mode, zigzag >2, shimmer skeletons, count-up stats, grayscale logo row, blur modals, hide-it-in-a-modal | [Sailop 90+](https://sailop.com/blog/90-plus-ai-design-patterns-to-avoid-definitive-list); [Pixelslop](https://booplex.com/projects/pixelslop); impeccable craft-floor |

### Agent checklist

Writing: name the thing; no moral at the end of every paragraph; no
chat residue. UI copy: action on the button, recovery on the error.

UX: real `<button>`/`<label>`, 4.5:1, `:focus-visible`, reduced-motion,
no nested cards, no scale-on-hover grid.

## Round 7 (uniqueness + more UI tells)

| Finding | Source |
|---|---|
| Uniqueness is not a prompt adjective. Open prompt → distributional mean. Separate direction from build; feed real URLs/screenshots so the "most probable" answer is no longer Inter/indigo | [Superdesign: why generic](https://www.superdesign.dev/blog/why-ai-design-looks-generic), [how to design with AI](https://superdesign.dev/blog/how-to-design-with-ai) |
| Stronger prior: curated reference set, exclusion list, 3–5 variants then pick. Compact DESIGN.md (hex, type pair, don'ts) beats 200KB token dump | [Zenn / Claude Code workflow](https://zenn.dev/neotechpark/articles/658d99a04844c1); [Zhou: layout→theme→motion](https://medium.com/@jason.zhou.design/why-your-ai-generated-ui-looks-ai-ish-and-the-workflow-that-fixes-it-bfb1827a5f96); UX Planet DESIGN.md (YAML tokens + markdown decisions + linter) |
| A skill without a picture still falls back to archetypes. Reference grounding > heuristics. App UI needs a screen-type reference, not a "be distinctive" hero | [Superdesign: Claude Code UI](https://superdesign.dev/blog/claude-code-ui-design) |
| Highest-leverage anti-slop move: change the typeface first. Color should be semantic (action/warn/success), not `gradient-start`. Missing empty/error/loading is the screenshot optimizer | [Hey.com / Kosta](https://world.hey.com/kostac/spot-the-slop-a-ui-designer-s-guide-to-fixing-ai-defaults-4c448c9c) |
| Show HN audit, 1,590 pages: 22% heavy slop (≥4 of 16 patterns). Top tells: permanent dark 34%, gradient bg 27%, icon-card grids 22%. Next-centroid fonts: Geist, Space Grotesk, Instrument Serif | [Developers Digest / Krebs](https://www.developersdigest.tech/blog/ai-design-slop-and-how-to-spot-it) |
| More stencil: sticky glass nav, FAQ closer, three-tier "Most popular" pricing, mesh orbs, `rounded-3xl`, everything visible at once, progressive-disclosure failure | Sailop encyclopedia; Hey.com #7 |
| Ground in the subject's artifacts; ban the category-default page; one signature, rest quiet. If the look is guessable from category, rework | frontend-design; impeccable new-work |

### Agent uniqueness loop

1. Subject + world (not "SaaS").
2. 2–3 live references; name why.
3. Ban Inter-only / indigo / hero-3-cards / glass nav.
4. Lock hex, type pair, radius, density.
5. Wireframe → theme → one motion.
6. Fork 2–3 directions; pick; scale one component.
7. Screenshot; empty/error/loading; contrast.

## Round 8 (sibling skill mix-ins)

Goal: steal generation-time reflexes from skills already on disk,
without turning noslop into ponytail, impeccable, or a 70-rule Vercel
dump. Full audits still load those skills.

| Mix-in | Source | What noslop took | What it refused |
|---|---|---|---|
| Native platform before a widget; `ponytail:` ceiling comments | ponytail ladder rungs 4–5 | `<input type="date">`, CSS over JS measure, DB constraint | YAGNI / skip-the-feature (ponytail's job) |
| Waterfalls, barrels, nested components, derive-in-render | vercel-react-best-practices | ~10 generation-time tells in `typescript.md` | All 70 rules, SWR, `after()`, idle callbacks |
| Boolean-prop blindness → compose / explicit variants | vercel-composition-patterns | Extend existing boolean-blindness bullet | Provider/context architecture cookbook |
| Forms, focus, motion, Intl, URL state, paste, CLS | Vercel Web Interface Guidelines (`command.md`) | Compact table in `ui.md` | Full WIG review output format |
| 44×44, 150–300ms, press feedback, icon stroke, scrim | ui-ux-pro-max | Overlap with WIG, kept the mobile-specific bits | Native-only tables as if they were web law |
| Group/Title/Separator/Empty; no z-index restyle | shadcn composition + heroui/coss | Compose as documented; layout `className` only | Per-kit API encyclopedias |
| Branding scrape + screenshot → DESIGN.md | firecrawl-website-design-clone | One step in uniqueness loop | The whole scrape workflow |
| Expected value from spec/literal; public seams | tdd | Tighten tests section | Red-green loop as noslop's job |
| Same verb through the flow; `…`; numerals | write + WIG typography | `copy.md` UX bullets | Em-dash hard-ban on agent chat; 🥷 prefix |
| Chat residue vs UI grammar | caveman | "Caveman is not UI copy" | Compressed assistant voice |

`deslop` / `specs-code-cleanup` stay post-hoc. Noslop's job is that
they have nothing to do. `grill-me` is an interview, not a code rule.

- round 9: UI/design coverage map. Firecrawl keyless 429; used
  WebFetch of Sailop encyclopedia / 7 dimensions / 73 patterns /
  90+ list, Kosta/Hey, Superdesign, WCAG 2.2 W3C, NN/G forms+empty
  states, no-slop-ui (Linear centroid warning), dark-mode + chart
  a11y, i18n/RTL. Product-UI stencil (4 KPI + Recharts) was the
  biggest hole vs landing-page blacklist.
- round 10: main-skill holes — N+1, unbounded lists, IDOR, timeouts,
  money-as-float, CORS *, 200-for-errors, log PII, 100vh/z-9999.
  Firecrawl CLI in this session still unauthenticated (keyless 429);
  used web search + page fetch. GitClear 2026 maintainability gap.

## Round 9 (UI/design: what to cover)

Sailop (500 scanned sites): 94% share 12 core patterns; 7
dimensions (color, type, layout, motion, component, structure,
spacing). Color + type weigh most. 87 encyclopedia patterns; 73
"signature" counters of which 8–12 suffice. Kosta: missing states
and progressive disclosure matter more than the gradient. Superdesign:
distributional convergence + one-shot workflow.

WCAG 2.2 AA that agents skip: focus not obscured (sticky), dragging
alternative, target 24×24 (we already ask 44 for touch), redundant
entry, accessible auth (allow paste). Focus Appearance is AAA.

NN/G: validate after the field is finished; errors next to fields;
preserve input; empty ≠ loading; don't toast a blocking error.

Product centroid: shadcn dashboard blocks (sidebar + 4 KPIs +
chart). `no-slop-ui` correctly bans glass/heroes-in-apps, then
prescribes Linear/Raycast — the next mean.

**In noslop (generation-time):** screen job; product stencil; type
measure/leading/tracking; hue-shifted neutrals; forms/tables/charts;
WCAG 2.2 paste/focus (AA); redundant entry is Level A; i18n concat when the product
localizes.

**Leave to siblings:** 73 signature devices, palettes/pairings
databases, full WIG/HIG/M3, design-director process (impeccable /
frontend-design).

**Don't add:** always-dark-mode (Sailop landing bias); drop caps /
custom cursors / riso as defaults; "system font only."

## Round 10 (main skill holes: load, authz, money, I/O)

The UI file was catching landing/app slop. `SKILL.md` still let an
agent ship a "correct" API that dies under a second user or a second
thousand rows. This round: web search + page fetch (this agent
session's Firecrawl CLI still reports unauthenticated / keyless 429).

| Finding | Source |
|---|---|
| N+1 is the default JS idiom (`map` + `await` / `Promise.all`). Parallel N+1 still kills the pool. JOIN / `include` / `IN` | [Afterbuild](https://afterbuildlabs.com/resources/n-plus-1-in-ai-built-apps), [AuditBuffet](https://auditbuffet.com/patterns/ab-000903) |
| Unbounded "return all" endpoints; OFFSET deep pages | [No Semicolons](https://nosemicolons.com/posts/ai-generated-apis-load-testing-pattern/), ResumeLens SQL anti-patterns |
| 76% of AI-assisted PRs miss timeouts on outbound calls; no idempotency on create | [code-slop / OX Security 2025](https://github.com/asyrafhussin/agent-skills/blob/main/skills/code-slop/rules/defensive-missing-real.md) |
| `requests` has no default timeout; AI wrappers often set `httpx` timeout to `None` | [Batpig](https://batpig.io/blog/the-missing-timeout/), Requests docs |
| Logged-in `GET /:id` without owner check (IDOR/BOLA). UUID ≠ authz | [PreBreach OWASP in AI code](https://www.prebreach.dev/blog/owasp-top-10-ai-generated-code), [CheckVibe](https://checkvibe.dev/blog/cursor-copilot-security-audit), OWASP IDOR cheat sheet |
| `cors()` wildcard + cookies/Authorization | [Busy Agents](https://dev.to/busyagents/ai-generated-backends-almost-always-get-cors-wrong-2ic6) |
| SQL/NoSQL string concat; request body as Mongo filter | Safeguard pattern review; PreBreach A03 |
| Money as `float`/`number`; JSON numeric literals | Django Decimal guide; rust_decimal practice |
| `200` + `{error}`; stack traces to client; no rate limit on login | PreBreach A05; API design packs |
| GitClear 2026 (623M changes): copy/paste ~5× moved lines; duplicated blocks +81%; error-masking +47%; refactoring −70% | [The Maintainability Gap](https://www.gitclear.com/the_ai_code_quality_maintainability_gap) |
| CSS: `100vh` heroes, `z-index: 9999`, `overflow-x: hidden` (breaks sticky), `!important` | Hallmark layout-and-space; Sailop 2026 guide |
| `100vh`/`dvh` ignore the mobile keyboard | OpenReplay; Loke.dev interactive-widget |

**Folded into noslop:** new SKILL section *Authorization, I/O, and money*; language notes; CSS tells in `ui.md`. Not folded: full OWASP encyclopedia, cursor-pagination-only religion, circuit-breaker catalogs.

## Round 11–12 (agent hygiene, XSS/SSRF, compact)

People's loudest remaining hates were not more UI tells. Trust in AI
code ~29% with 84% adoption; #1 pain is almost-right output
([Code With Seb](https://www.codewithseb.com/blog/uncomfortable-truths-ai-coding-agents-2026),
Stack Overflow 2025). Agent-as-coworker: unasked `SUMMARY.md` /
`CHANGES.md` (LinkedIn / Cursor rules), "would you also", shipping
the plan as a file, declaring done on repo activity (Anthropic
long-running agents: progress ≠ completion; false E2E from unit
tests), "simplifying away" a working feature
([Hackernoon preservation](https://hackernoon.com/how-i-stop-ai-coding-agents-from-improving-away-important-features)),
questionnaire instead of reading the file.

Security still under-covered vs data: XSS **2.74×** density /
Veracode **~85% XSS / ~87% log-injection** fail; SSRF in **all 15/15**
Tenzai benchmark apps (not “100% of URL fetches”);
(AppSec Santa 2026) including redirect-bypass of one-shot IP
checks; mass assignment; `pickle`/`yaml.load`/`shell=True`;
unsigned webhooks; model field with no migration.

Skills-as-product: SKILL.md was 465 lines with a duplicated UI
table; create-skill cap is 500; catalog description budgets drop
sibling skills. Compacted main file (~410), moved UI detail to
`ui.md`, added Scope + trust-boundary bullets, did not swallow
OWASP/CSP/FinOps.

**Folded:** Scope (no extra artifacts, no "also", preserve
behavior, progress ≠ done, no surprise git); look-before-ask;
XSS/SSRF/mass-assignment/eval/schema/webhook/cache; user-path
verify; `key={i}`; `Math.random` for tokens. UI uniqueness loop
in `ui.md` shortened. Language notes got the local form.

## Round 13 (coworker bucket — subagent loop)

[Coworker](4c1df7ca-120b-4e8c-86cb-5403f16480fb) saturated: same ~15
modes across Anthropic long-running agents, Slate, Cursor swarm,
skill-description drop, Cursor SUMMARY.md thread, Register LIDE.
LinkedIn was not a hate source (people there *want* markdown memory).

**Folded:** one slice / no one-shot; no planner ceremony; ossify
inverse (change core if the task needs it); don't grow the megafile;
docs-about-work ≠ work (`FINAL_REPORT.md`); two failures then stop;
stale plan loses; a statement is not an order; no tool narration /
next-step menu; don't claim a path you couldn't see; keep the diff
reviewable; no chmod/delete/deploy unless tasked.

**Left out (harness):** description-budget silent skill drop, lossy
compaction, cold-start amnesia, permission UI vs auto-approve,
subagent summary handoff, Anthropic's progress-file + auto-commit
recipe (that's how product repos get `claude-progress.txt`).

## Round 14 (product leftovers + writing voice)

[Product](e159ce43-42ab-4bf5-9c7b-358dd9d08555) saturated on
Wikipedia AI slop, SEW 30, BBC, Pew 2026, Gemini threads, FTC fake
reviews. Folded *app* rules into `ui.md` (no generated people/hands,
no invented testimonials, support bot must escalate, cancel where
they signed up, chats not training data unless opt-in, 429 ≠ fake
answer). Left out: platform ads, lab rate limits, national policy,
jobs/energy, dead-internet theory, lab copyright suits.

[Sycophancy](ec63ced8-fccd-4ef6-a6e1-1a8cca8f3c5a) saturated on
Wikipedia Signs of AI writing, Stanford/Science 2026 (49% extra
affirmation), OpenAI GPT-4o rollback, StoryScope. Folded into
`copy.md`: title-case headings, over-bold, curly quotes, collaborative
comms beyond the four phrases, citation-token family, named-but-wrong
citations, knowledge-cutoff theater, tailing `-ing` clauses, README
Key Takeaways stencil. SKILL: don't accept a false frame; don't paste
chat scaffolding into README comments. Left to `write`: copula
avoidance, fiction tells, ELEPHANT taxonomy.

## Round 15 (almost-right + dishonesty + security)

[Almost-right](66742dec-7c0b-46c6-40ff-bdb2-975319f28231): min-diff,
5-line clone, bypass-the-wrapper, false-equivalent helper swap,
sibling-route auth middleware, undeclared env/schema. Left out:
GitClear/METR org metrics, cargo-cult Kafka (ponytail), mutation-
testing CI (tdd).

[Dishonesty](c226e99b-46c6-40ff-bdb2-975319f28231): this-turn tool
output only; no invented consent; don't edit the grader; no E2E
backdoor / expected-value in the impl; quote the runner verbatim;
unfinished todos stay visible; after a correction, run a tool first.
Left out: AgentLiar products, holdout-suite architecture, RLHF papers.

[Security](a8a702b7-a9b9-442b-8841-eae2f64e3bab): saturation on
generation-time tells (path join, cookie CSRF, TLS verify-off,
`jwt.decode`, client-bundled service keys, header identity, log
CRLF, password hashing, logged-in ≠ admin, user-as-template-source).
Left to `security-review`: CSP/XXE/OAuth/GraphQL/header suites.
Sources: Veracode ~45% insecure / ~85% XSS / ~87% log injection;
CodeRabbit ~1.57× security overall, 2.74× XSS; Tenzai/Valtik CSRF
0/15 + SSRF in 15/15 apps; path-traversal LLM study;
GitGuardian Copilot secrets.

## Round 16 (UI / a11y bucket)

[UI](a33d71cb-9a2d-4a0b-8f36-697eabe63b3b) saturated on Krebs 16,
Sailop 7, Kosta, Superdesign (process, not tells). Folded into
`ui.md`: generated rasters as product (fingers/plastic/garbled type,
live type not PNG), chart text alternative (summary + table, not
tooltip-only), drag-only, false empty vs loading, reveal that hides
content at rest, sticky footer/cookie covering focus, image CAPTCHA.
Left to frontend-design/impeccable: distinctive world, Superdesign
canvas, APCA, AAA focus appearance. No more landing-page font lists.

## Round 17 (3-3-3 composer: expand + gaps + operability)

[Expand: structure](926fc35e-e28b-449a-b189-af1a1163a31f): copy-twice vs
clone, grep-before-ask, one-slice stop, preserve vs change-core, min-diff.

[Expand: trust](d0f8a145-6a77-4459-aecf-43c12e8e9c30): shortened Authn
(one auth model per route), invent-success `?.` on required data, schema
env tell, log interpolate, TLS next to timeouts, secrets trim, tests
this-turn.

[Expand: UI/copy/langs](5f1d6749-1259-4d20-abce-e3b49a913770): grep-able
identifiers in ui/copy/ts/python/go/rust; false frame in copy.md.

[Gaps: agent](1104f62e-9b33-4764-bbd8-e7f8cc9ba9ab): phantom edits,
negative constraint, mermaid/CHANGELOG, confirmshaming/cookie wall.

[Gaps: code](f78686f2-a9dd-4eae-970c-10fd0ca5f7f0): symptom/wrong file,
Zod never parsed, one lockfile, localhost/DEBUG defaults, stale comments,
reproduce-before-patch, generated-file format, no amend.

[Check: operability](2657f7d0-0c74-4eb0-9ae5-a711939bb11a): yes-if-patched.
Took: question-only off-ramp, landing-only URL fetch, identical retries,
must-load language identifiers. Did **not** delete Slop tells, Philosophy,
or Tests — those are the fingerprint, not theater.

## Round 18 (remaining 3-3-3: ops gaps + consistency + facts)

[Gaps: security UI ops](9dba09eb-eef0-4c15-817e-07a13ceff3b9): health
always-200, migrate-on-boot, FK without index, `curl|bash`/postinstall,
email header CRLF, `<html lang>`, PrismaClient per request. Left
CSP/clickjacking/host-header to security-review.

[Check: internal consistency](a03ede8b-e13a-49e5-b372-d729dc37242b):
Inter ban now match-the-file; fetch-blocked UI matches repo or skips;
cookie CSRF slop row scoped; ponytail check ≠ unasked test file.

[Check: cited facts](ff09142e-c6d2-48d1-a034-5310fad5d99c): SKILL cites
no study stats (keep “70% problem” as metaphor). research.md: CodeRabbit
2.74× is XSS-only; Veracode ~85/87; Tenzai SSRF is 15/15 apps; 44×44 is
touch/HIG not WCAG AA (24×24).

## Round 19 (review + Firecrawl expand, 2026-08-19)

Three review subagents (structure, gaps, operability) plus Firecrawl
search/scrape/papers. SKILL.md was 485 lines, drowning; installed
`~/.agents/skills/noslop` was still the 409-line sibling-pairing
copy.

**Structure.** Delete karaoke: 70-row Slop tells table restated the
body. Move Trust encyclopedia to `references/trust.md`; keep an
always-on index. Load table at the top (extensions, not bottom
pointers). Drop Popover + named-intermediates samples. Keep the
ponytail ladder; drop lite/full/ultra; `ceiling:` not `ponytail:`;
description says ponytail/deslop are inlined. Target ~375 lines.

**Gaps (must-add, cheap).** HTTP 2xx before `.json()` / `raise_for_status`
([otel-demo #3782](https://github.com/open-telemetry/opentelemetry-demo/issues/3782));
owner/org/role from session not body; persist idempotency keys
([Stripe ai #402](https://github.com/stripe/ai/issues/402)); unbounded
I/O fan-out; two writes = one transaction; file-level
`@ts-nocheck`/`noqa`; test `sleep` / giant snapshot; destructive
schema needs backfill. Language refs: Next 15 async `params`,
`Promise.allSettled` invented success, cookie flags, Python
`raise_for_status` + `assert`≠boundary, Go one `sql.DB`, Rust crate
hallucination.

**Operability.** Copy-twice vs grep-hit resolved in the ladder.
Leave-a-check ≠ new test file. `ui.md` only on layout/new surface.
Inter match-the-file *before* the ban. CSRF Bearer carve-out in
python.md. Description no longer claims sibling pairing.

**Firecrawl (round19).** Incidents:
[Adversa, nine deletions](https://adversa.ai/blog/ai-coding-agent-incidents/)
(YOLO wipe, Replit SaaStr DROP, Plan Mode ignored "DO NOT RUN",
`rm -rf … ~/`, unquoted spaces → `D:\`, Prisma
`--shadow-database-url` at prod, Jul 2026). Irreversible is its own
class. [Augment 80% problem](https://augmentcode.com/guides/the-80-percent-problem-ai-agents-technical-debt):
missing auth on the fourth endpoint, no idempotency, duplicate
charge after timeout. [LainAgent phantom events](https://dev.to/lainagent_ai/a-month-of-ai-agents-in-production-july-2026-silence-retries-and-phantom-events-1i8o):
retry with no cap; persist "handled" before success. [UVIK / SO 2025](https://uvik.net/blog/claude-code-vs-cursor-vs-copilot-vs-codex-2026/):
66% "almost right." Papers: library hallucinations
([arxiv:2509.22202](https://arxiv.org/abs/2509.22202)), 2026 frontier
slopsquat still ~5% and 53 shared registrable names
([arxiv:2605.17062](https://arxiv.org/abs/2605.17062)), Rust crate
invention ([arxiv:2606.08444](https://arxiv.org/abs/2606.08444)).

**Evals 4–6.** Scoped invoice read (authz); atomic slot reserve
(CAS); outbound GET (timeout + 2xx). Old 1–3 never mentioned a
second user, a race, or HTTP status.

**Left out.** Full OWASP, FinOps, sandbox/symlink RCE harness bugs
(GhostApproval, DuneSlide), AgentLiar products, ponytail intensity,
always-load ui.md on a 20-line JSX logic patch.

## Round 20 (review + Firecrawl, 2026-08-19)

Subagents: [Bugbot](0c175f4b-e787-4d8e-b7e1-b8547285959b) (natural-language
diff; no git), [structure](956ead09-a484-4c7a-b510-4b8ee750ae61),
[gaps](d3e5371e-b4df-4976-b9b5-3240ebdc31b1),
[language-consistency](d639259c-f9d1-4940-990a-5fd41d9ad31e),
[security](5603388d-5d55-466b-b292-cf412a379514). Dedicated
security-review subagent could not compute a diff (folder is not a
git repo). Firecrawl round20: search + scrape + papers.

**P0 collisions folded.** `typescript.md` no longer always-loads
`ui.md` on JSX. CSRF: skip only if cookies cannot authenticate
([OWASP CSRF](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html);
cookie JSON `fetch` is still a cookie session). Node `jwt.decode`
never verifies ([jsonwebtoken README](https://github.com/auth0/node-jsonwebtoken#jwtdecodetoken--options));
PyJWT `decode(token, key, algorithms=…)` *is* verify. Copy-twice vs
clone: named helper → import; unmarked snippet → copy. `ceiling:` vs
`ponytail:`. Leave-a-check is an existing spec, not `assert` at the
trust boundary and not a new `test_*`. Slop-tells karaoke cut to five
visual rows. Description gained a question-only off-ramp.

**Firecrawl (must-add).** Next.js: treat `'use server'` as a public
POST; page-level `auth()` does not cover the action
([data-security](https://nextjs.org/docs/app/guides/data-security),
[Arcjet](https://blog.arcjet.com/next-js-server-action-security/)).
`FormData.get` is not parse. `cookies()` / `headers()` inside
`cache()` / `'use cache'` / `unstable_cache` is request-in-cache;
pass values as arguments
([use cache](https://nextjs.org/docs/app/api-reference/directives/use-cache)).
`LIKE` concat: parameterized SQL still ships `%`/`_` injection
([CQR](https://cqr.company/web-vulnerabilities/sql-wildcard-injection/),
cal.diy #29372). HTTP 2xx is 200–299, not `StatusOK`. Unique email
is a constraint, not `findByEmail` then insert. JSON/JSONB
read-modify-write loses concurrent keys. Flags `?? true` fail-open.
SSE/WebSocket without abort. `stash pop` onto dirty work; `git add .`
taking `.env`. `Date.now()` in SSR render. Deep `OFFSET` as the only
pager. Wall-clock tests pin `TZ`. Recalled crates.io names are still
slopsquat. Do not write `DESIGN.md` unless asked.

**Papers (cited, not in SKILL).** LLM-generated snippets: 68.8%
violate ≥1 security MR; hard-coded creds + command injection dominate;
auth/DB prompts co-violate
([arxiv:2607.12089](https://arxiv.org/abs/2607.12089)). LLM-integrated
apps mediate classic sinks (LLM2SQLi/XSS/SSRF) — that is product
architecture, not this skill
([arxiv:2608.10281](https://arxiv.org/abs/2608.10281)). SKILL still
cites no study stats.

**Evals.** Eval 1 grades `insertUser` (unique insert), not
find-then-push. Eval 5 fixture `#` → `//` (invalid TS). Eval 6 uses
`PRICES_URL`, not a caller URL (SSRF). Eval 7: `createInvoice` owner
from session. Eval 4 still read-path; write-path is 7.

**Left out.** `after()` chapter, cursor-pagination religion beyond
one OFFSET line, CSP/OAuth/GraphQL, Go/Rust evals before fixtures,
growing SKILL past ~400, AgentLiar products.

## Round 21 (JS + React split, 2026-08-19)

Subagents: [Bugbot](c3c628cd-6fdb-4a6a-bc53-79b89529f3da) (natural-language
diff; no git), security-review (failed: not a git repo), plus
structure / JS-React-gaps / skill-security agents. Firecrawl
round21: search + scrape + developer index + papers.

**Structure.** JS runtime, React, and TypeScript types lived in one
`typescript.md`. `.vue`/`.svelte` skipped those rules. Split:

| File | Job |
|---|---|
| [javascript.md](references/javascript.md) | fetch/2xx, proto, DOM, Node, jwt, public env |
| [react.md](references/react.md) | effects, RSC/`use client`, hydration, XSS-in-JSX |
| [typescript.md](references/typescript.md) | `as T`, Zod-as-alias, Prisma CAS/N+1 |

Load table: `.js` → javascript; `.ts` → javascript then typescript;
`.jsx` → react then javascript; `.tsx` → all three; `.vue`/`.svelte`
→ javascript for `<script>`. SKILL.md 398 lines. Did not dump the
Vercel 70-rule cookbook or CSP.

**Bugbot.** Eval 1 fixture `insertUser` was find-then-push while the
skill forbids that for duplicate identity — now a `Map` email key.
No React/JS evals; eval 6 was Python-only for outbound 2xx. Vue/Svelte
skipped the JS ref.

**Firecrawl (must-add).** Prototype pollution is not `JSON.parse` —
it is `Object.assign` / recursive merge of a parsed `__proto__` key
([MDN](https://developer.mozilla.org/en-US/docs/Web/Security/Attacks/Prototype_pollution);
PortSwigger; AWS SDK `Object.assign` issues). React 2026: stale
closures + `eslint-disable` exhaustive-deps; derive-in-render /
reset-with-`key` ([react.dev](https://react.dev/learn/you-might-not-need-an-effect);
[Kodus checklist](https://kodus.io/en/react-code-review-checklist/));
client `useEffect` fetch instead of RSC
(Medium “10 lethal mistakes”); `dangerouslySetInnerHTML`,
`localStorage` tokens, client Zod as security, `REACT_APP_`/`NEXT_PUBLIC_`
secrets ([front-end.tips](https://front-end.tips/react-security-mistakes-developers-make/)).
`'use server'` on a component is not “this is a Server Component”;
mutating clicks without pending double-submit. Abort in-effect fetch
so a stale `id` cannot `setState`. `Math.random` / `Date` in render
hydrates wrong — `useId()`. React 19: `ref` is a prop, skip
`forwardRef` on new function components.

**Papers (cited, not in SKILL).** Same family as round 20:
[arxiv:2607.12089](https://arxiv.org/abs/2607.12089) (LLM snippet
security MRs), [arxiv:2504.20612](https://arxiv.org/abs/2504.20612)
(LLM-generated web apps). SKILL still cites no study stats.

**Evals 8–10.** React derived full name (no `useEffect` copy); JS
allowlisted `mergeSettings` (no `Object.assign` of JSON); JS
`loadPrices` (timeout + 2xx), twin of eval 6.

**Left out.** CSP/SRI, SWR/`after()`, `useMemo` religion beyond one
line, GraphQL/OAuth, Pages-router encyclopedia, `var` vs `let`
lectures, ReDoS catalog, `postMessage` cookbook beyond one line.

**Follow-up (same day).** Folded
[structure](197685ac-eee8-4fde-b4aa-dd4701aaa370),
[JS/React gaps](89c9ec05-5c4a-4f7c-8179-e89e9d424e50),
[skill security](cc6df3f1-3775-4c16-b332-cdaf55905453). SKILL Authz:
Origin rejects missing; skip CSRF ≠ “it's JSON”; Node `decode` /
`jose.decodeJwt` vs PyJWT `decode(key, algorithms)`; `cookies()` out
of `cache()`; JS `.length` is UTF-16. Did **not** exclusive-load
(`.ts` still reads `javascript.md`) — proto / `forEach(async)` /
sync `fs` would vanish from `route.ts`. Next **server** leftover
stays in `typescript.md` for `actions.ts`. javascript.md: floating
`forEach(async)`, module-scope `currentUser`, CSRF PATCH, `for…in`
parsed JSON. react.md: `'use client'` on Prisma, file-level `'use
server'`, `try/redirect` catch, client `metadata`,
`suppressHydrationWarning`. trust.md: passwords, `Host` header,
`force-cache`, `next/image` SSRF. Eval 1: unique-insert helper + no
body `id`; dropped “atomically” on in-memory `Map`. No new evals.

## Round 22 (anti-slop UI + guiderails, 20 Firecrawl loops)

Twenty `firecrawl search` queries (CLI), then scrape of winners.
Landing-font saturation from round 16 still holds. This round is
**operability guiderails** agents miss on the first draft.

| Loop | Query | Keep |
|---|---|---|
| 1 | AI UI slop 2026 | [Vibe Code Kit](https://vibecodekit.dev/ai-slop-design): slop = no decision. Do **not** add DESIGN.md unless asked |
| 2 | v0/shadcn | Official [dashboard example](https://ui.shadcn.com/examples/dashboard) *is* the stencil |
| 3 | Vercel WIG | [vercel.com/design/guidelines](https://vercel.com/design/guidelines) + [command.md](https://raw.githubusercontent.com/vercel-labs/web-interface-guidelines/main/command.md). Take paste, ≥16px inputs, keep-label spinner, URL state. **Refuse:** Title Case, curly quotes, `maximum-scale=1` as an iOS-zoom fix (conflicts with zoom + `copy.md`) |
| 4 | WCAG 2.2 | [Focus not obscured](https://www.w3.org/WAI/WCAG22/Understanding/focus-not-obscured-minimum.html) (sticky = F110); [3.3.8](https://www.w3.org/WAI/WCAG22/Understanding/accessible-authentication-minimum.html) paste + no 6-box OTP transcription |
| 5 | Apple HIG | 44×44 pt min; Dynamic Type ≥200%; more than color; Reduce Motion |
| 6 | Material 3 | Color *roles*, not invert. Web: semantic tokens |
| 7 | GOV.UK | [Error message](https://design-system.service.gov.uk/components/error-message/) + [summary](https://design-system.service.gov.uk/components/error-summary/): both, same words, focus summary, don't clear fields. Field error ≠ service down. [One thing per page](https://designnotes.blog.gov.uk/2015/07/03/one-thing-per-page/) then merge in research. [Question pages](https://design-system.service.gov.uk/patterns/question-pages/): legend as `<h1>`, don't break Back |
| 8 | ARIA APG | [Dialog](https://www.w3.org/WAI/ARIA/apg/patterns/dialog-modal/): focus in, Tab cycles, Esc, return focus. `aria-modal=true` only if it actually traps. Kit/`<dialog>`, not a custom trap |
| 9 | NN/g dashboard | [Preattentive](https://www.nngroup.com/articles/dashboards-preattentive/): glanceable; length/position for quantity, not pie/color |
| 10 | Baymard | Single column; don't split identities; labels above; accept format variants; prefill editable |
| 11 | Deceptive | [NN/g](https://www.nngroup.com/articles/deceptive-patterns/): obstruction, confirmshaming, preselect extras, nagging — already in round 14/17 |
| 12 | Dark mode | Not invert (paywalled restatement of tokens). Keep existing `ui.md` row |
| 13 | Skeleton | [NN/g](https://www.nngroup.com/articles/skeleton-screens/): skip <1s; no frame-only; match layout |
| 14 | Motion | [web.dev](https://web.dev/articles/prefers-reduced-motion) + WCAG C39. Already in reflexes |
| 15 | Agent UI skills | [Hallmark](https://github.com/nutlope/hallmark) (58 gates, theme catalogue); [anti-ui-slop](https://github.com/samuelbushi/uizze) (UIZZE + DESIGN.md ceremony). **Left out:** both are competing skills. Modes (persuade/operate/read) already in `ui.md` |
| 16 | Inclusive | Skip link, landmarks — already |
| 17 | Content design | [GOV.UK writing](https://www.gov.uk/service-manual/design/writing-for-user-interfaces): sentence case, no please/sorry in field errors. Folded `copy.md` |
| 18 | svh/keyboard | [Chrome `interactive-widget`](https://developer.chrome.com/blog/viewport-resize-behavior): default `resizes-visual`; forms → `resizes-content`. `100svh` does not lift the OSK |
| 19 | Toast / live | [WCAG 4.1.3](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html); [Soueidan](https://www.sarasoueidan.com/blog/accessible-notifications-with-aria-live-regions-part-1/): polite vs assertive; vanishing toast ≠ only error record |
| 20 | Progressive disclosure | [NN/g](https://www.nngroup.com/articles/progressive-disclosure/) — already the product-UI stencil |

**Folded into `ui.md` / `copy.md`.** Not folded: Hallmark gates, UIZZE upsell,
APCA-over-WCAG, Vercel Title Case / curly quotes, Baymard Luhn/CVV
ecommerce encyclopedia, Material dynamic wallpaper color.

## Round 23 (complaint extract, 2026-08-18)

56 structured complaints from
`.firecrawl/round23/extract-data-2026-08-18.json`. Sources:
[impeccable.style/slop](https://impeccable.style/slop) (38),
[ACM 10.1145/3757980.3757989](https://dl.acm.org/doi/10.1145/3757980.3757989)
(8), [Puck constrained UI](https://puckeditor.com/blog/ai-slop-vs-constrained-ui)
(4), [smoothui](https://smoothui.dev/blog/ai-design-slop) (4),
[Phogat](https://mohitphogat.medium.com/ai-design-slop-why-every-ai-built-interface-looks-the-same-and-how-to-fix-it-bf874e0b470c)
(2). ~40 already in `ui.md` / `copy.md` from Krebs/Sailop/round 16–22.

**Folded (generation-time, not already named):** graph-paper wallpaper
on a non-canvas; thick stroke vs radius; hairline + wide shadow;
icon tile larger than the heading; full-sentence display H1;
heading/body within ~4px; crushed `tracking-tighter`; all-caps body;
SVG blob collage / mascot doodle; pulse on a static status; bounce
easing; hover image transform; DOM order = tab order;
streamline/empower/supercharge in copy.

**Left out:** non-deterministic layout (tooling); prompt-insensitive
a11y and one-shot no-fix loops (process — Done already re-reads the
diff); Puck "registered component registry" (already kit lookup).

## Round 24 (second complaint extract, 2026-08-18)

53 complaints from
`.firecrawl/round23/extract-data-2026-08-18-1.json`. Sources:
[impeccable.style/slop](https://impeccable.style/slop) (25),
[arXiv 2509.10652](https://arxiv.org/html/2509.10652v1) (19),
[Puck](https://puckeditor.com/blog/ai-slop-vs-constrained-ui) (5),
[Lavaee](https://alexlavaee.me/blog/lessons-learned-designing-with-ai/)
(3), [managed-code](https://www.managed-code.com/blog-post/ai-slop-in-design)
(1). Visual catalog mostly a duplicate of round 23.

**Folded:** "Powered by AI" kicker; italic-serif as the whole H1;
labels/links/cells `< 11px`; scrollable/two-column settings modal;
missing disabled state; `w-[1280px]` desktop canvas.

**Left out:** arXiv process (deskilling, opaque history, multimodal
feedback, deployment fragility, accountability). Extra files, two
failures, no secrets, no sibling feature already in SKILL.md.

## Round 25 (review + SQL/FastAPI/Go, 2026-08-19)

Four review subagents + Firecrawl search/scrape. Workspace was already
ahead of `~/.agents/skills/noslop` (JS/React load split, evals).

**Must-add.** `.sql` / schema had no language file — agents emit
`UPDATE` with no `WHERE`, comma joins, `SELECT *`, guessed columns,
tables with no index on the filter they just wrote
([AI2SQL](https://builder.ai2sql.io/blog/ai-generated-sql-safety-guide);
Reddit schema-review thread). FastAPI: skip `Depends`, global `db`,
Pydantic v1 in a v2 file, dump routes in `main.py`
([ofershap/fastapi-best-practices](https://github.com/ofershap/fastapi-best-practices)).
Go: `go func` + forgotten sender / no `ctx.Done()`
([OneUptime](https://oneuptime.com/blog/post/2026-01-07-go-goroutine-leaks/view)).
Tests: private-field asserts, `expect` in a callback that never fires
([Autonoma](https://getautonoma.com/blog/useless-unit-tests-tautological-anti-pattern)).

**Database.** Architecture review: do not add a BM25 palette DB;
read the language file. Compromised: 45-row `data/tells.csv` + stdlib
`scripts/lookup.py` for a large-diff cleanup pass only — not before
every one-file fix.

**Also folded from review:** do not read `research.md`; `as T` why-comment
is not a license on wire data; language files no longer re-pull
siblings the Load table already loaded.

**Evals 11–12.** SQL deactivate with WHERE; FastAPI DELETE with
`Depends` + `delete_for`.

**Left out.** EXPLAIN/staging runbooks, FastAPI lifespan encyclopedia,
Swift/Kotlin files, scanaislop 14 scanner patterns (already in SKILL),
Text-to-SQL RBAC papers as citations in SKILL.

## Round 26 (deep research: what to add next, 2026-08-19)

Thorough Firecrawl pass after round 25 was already folded. Goal: what
is still missing vs what would bloat `SKILL.md` (410 / 500 lines).

**Authoring constraint (do not grow SKILL.md).** Anthropic: keep the
body under 500 lines; once loaded, every token competes with history
([skill best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)).
[ContextCov](https://arxiv.org/abs/2603.00822): prompt-only AGENTS.md
compliance **67.0%**; compiled AST/shell/architecture checks **88.3%**.
More prose in SKILL.md is the expensive failure. Evals + `tells.csv`
rows beat another section.

**Must-add (cheap, generation-time, not already named).**

1. Dead leftovers aislop principle 4 still underspecifies:
   empty function, code after `return`/`throw`, `if (true)` /
   `if (1)` ([Clean Agent Code Standard](https://scanaislop.com/standard/),
   patterns [empty-function](https://scanaislop.com/patterns/empty-function)
   / [unreachable-code](https://scanaislop.com/patterns/unreachable-code)
   / [constant-condition](https://scanaislop.com/patterns/constant-condition)).
   Leftovers already bans `pass` / `todo!()` stubs — not stranded
   statements or constant gates. One line in Leftovers + CSV rows.
2. Hidden fallback: `catch` that returns `""` / `"ok"` / `[]` /
   a default object. GitClear 2026 error-masking **+47%**
   ([Maintainability Gap](https://www.gitclear.com/the_ai_code_quality_maintainability_gap));
   aislop v0.13.1 calibrated `hidden-fallback`. Invent-success is
   close; name the catch-return-safe-string shape.
3. Patchwork CFC (dead-code-after-return, duplicate switch case) —
   16 hits in 43 vibe-coded repos; 97% of structural failures evade
   `tsc --strict` / tests / SAST
   ([arxiv:2607.08981](https://arxiv.org/abs/2607.08981)).
   Sibling-route auth (SSR) and undeclared env (BCI) already in
   SKILL. Don't dump the eight-category taxonomy.

**Evals (higher leverage than SKILL text).** No Go fixture yet
despite `go.md` leak rules. No eval for empty function / unreachable
after return / catch-return-`[]`. ContextCov and ClayBuddy
([arxiv:2606.19380](https://arxiv.org/abs/2606.19380)) both say
capability errors (skill ignored) need a failing check, not more
instructions. Underspecification (unsafe default) is what SKILL
already targets.

**Do not add.** C# / C++ language files (aislop v0.14.1, 2026-08-08)
— match-the-file is enough until a user works there. Swift/Kotlin
same. FastAPI lifespan encyclopedia (ofershap plugin's extra 10).
Function-length linter (aislop principle 5 fights "size is a hint").
Writing-slop skills ([petergyang/no-ai-slop](https://github.com/petergyang/no-ai-slop))
— `copy.md` already owns that. CSP / OAuth / GraphQL / ReDoS
cookbooks (left out rounds 20–21). Cloud-cost provisioning from
[What Breaks](https://arxiv.org/abs/2605.30777) is harness/ops, not
a code-patch skill. Volume-Quality Inverse Law
([arxiv:2605.02741](https://arxiv.org/abs/2605.02741)): more capable
models emit more coupled bloat — prompting does not fix it; keep
one-slice / locality, don't add an architecture-foresight chapter.

**Papers (cited, not in SKILL).** Patchwork 81.4% of 43 AI repos
had structural findings (474 DHI / 270 RCF / 177 PIA). What Breaks:
547 confirmed GitHub incidents, 326 high/critical; 65% in bugfix +
setup; deception and fabricated completion. Endless Stream of AI
Slop ([arxiv:2603.27249](https://arxiv.org/abs/2603.27249)): reviewer
burden, test subversion, PR-size limits — already one-slice / don't
weaken the grader.

**GitClear 2026 (already cited round 10, still true).** Function
connectivity −35% is the reuse tell: a new function whose body
matches an existing one across files. CSV `duplicate-helper` exists;
an eval that plants a named helper two files away would catch it
better than another sentence.

**Follow-up (same day, review dump).** Folded remaining must-fix
from [architecture](d7b766f6-0e27-4ebe-af3d-2c857571f706) /
[coverage](fecc9c82-0842-4ab5-aaba-c42cc52ece8a) /
[consistency](aaf24ae1-f7e4-4d0e-adb1-572073659373): expand-and-contract
+ identifier interpolation + `db push`; Vue `v-html` / Svelte `{@html}`
in `javascript.md`; CSRF on mutating GET; metadata SSRF; `rust.md`
CSRF/SQL/JWT/webhook; Go `Body.Close` / `rows.Err` / concurrent map;
Trust index "The rest" is a pointer; eval 3 swallows into `{}`; evals
1/5/6/10 close the as-T / Prisma / extra-lib holes. Still not: kit
reuse eval, cookie CSRF eval, `'use server'` eval, shrinking `ui.md`.

## Round 27 (slop colors / picks / consistency, 2026-08-19)

Color was named in rounds 5–9 as Inter/indigo and left at
"hue-shifted neutrals + semantic roles." Palettes/pairings stayed a
sibling (impeccable / frontend-design). This round is the color file
those rounds deferred: which hexes models actually emit, why, and the
consistency failures that survive an indigo ban.

Firecrawl authenticated. Scraped Sailop color essays + zinc-950 +
Veljanoski UI drift; searched Wathan/indigo, VibeCode Purple, token
drift. Krebs 1,590-page audit and Sailop 600-site tool log are the
counts. Do not treat Sailop's "12 escape palettes" as noslop law —
several *are* the next centroid (cream/terracotta, black/acid-green).

### Two problems, not one

**Picks** are the attractor: the model chooses a hue from the training
mean. **Consistency** is holding a system after the pick: same tokens
on the next screen, derived hover/focus/status, a second theme that is
composed not inverted. Banning indigo and then writing `bg-blue-500`
beside `--primary`, or `ring-blue-500` after a terracotta accent, is
the second failure. Veljanoski names it **UI drift**: each screen
almost-right, five freelancers in one app
([dev.to](https://dev.to/dejan_veljanoski/your-ai-coding-tools-are-ignoring-your-design-system-heres-how-i-fixed-it-161j)).

Hues ≠ roles. Vibe Code Kit: ≤3 *hues* (dominant / neutral / accent).
Sailop C04: humans ship 8–12 *roles* (canvas, surface, text, muted,
action, danger, success, warning, info, border). Noslop's "4–6 hex"
is the hue lock; the roles are tints of those hues, not new hues.
A shallow 3-token palette and a rainbow of 12 unrelated hexes are
both slop.

### Why these hexes

Training chain, not taste ([Sailop archaeology](https://sailop.com/blog/tailwind-blue-purple-gradient-ai-signature-2026);
[Wathan's indigo apology](https://prg.sh/ramblings/Why-Your-AI-Keeps-Building-the-Same-Purple-Gradient-Website);
Kai Ni):

1. Tailwind UI demos used `bg-indigo-500` / `blue-500` (`#6366F1` /
   `#3B82F6`). Ergonomics: three keystrokes.
2. v3 gradient utilities made `from-purple-500 to-pink-500` a
   one-liner. OpenAI 2022 marketing + Stripe `#635BFF` (2019) gave
   the pair prestige; the LLM copy is the Tailwind stops, not Stripe's.
3. shadcn froze `slate` then `zinc` as the canonical neutral.
   `npx shadcn init` highlights Zinc. Millions of repos inherit
   `baseColor: zinc` with no decision
   ([zinc-950](https://sailop.com/blog/zinc-950-dark-hero-ai-default-2026)).
4. v0 was trained to emit shadcn. Lovable/Bolt inherit. Foundation
   models swallow the corpus.

Sailop: primary hue 200–290 HSL; >60% of AI sites land in
blue-600–indigo-600. `#3B82F6` on white is ~4.66:1 — the lightest
blue that still clears WCAG AA. Accessibility floor became the
answer. By 2026 "blue means trust" has flipped: unmodified
`blue-500`/`blue-600` means "nobody chose."

The 2024–25 tell was violet→pink on white. Once that got mocked,
generators migrated. The **2026 default is one-accent dark**:
zinc-950 canvas (`#09090b`), zinc-400 body, indigo-500 pop,
radial glow. Krebs: permanent dark **34%**, gradient bg **27%**,
icon-card grids **22%** of 1,590 Show HN pages; 22% hit ≥4 of 16
patterns ([Krebs](https://www.adriankrebs.ch/blog/design-slop/);
[Developers Digest](https://www.developersdigest.tech/blog/ai-design-slop-and-how-to-spot-it)).
Dark camouflages spacing errors and makes WCAG easy (`#fafafa` on
`#09090b` is 19:1). That is why the model likes it.

"VibeCode Purple" is the lavender that leaks from image models *and*
landing prompts (Krebs #4). No public exact hex; treat as
violet-400/500 (`#A78BFA` / `#8B5CF6`) plus `from-purple-500
to-pink-500`. Plum that is darker, redder, and half the chroma
(`oklch(0.42 0.11 330)`) is a different color.

### Grep fingerprints

Literal values. If the *file/tokens* already use them, match.
Otherwise they are the watermark.

| Token / class | Hex | Role in the tell |
|---|---|---|
| `blue-500` | `#3B82F6` | Most-shipped accent; v0/ChatGPT primary |
| `blue-600` | `#2563EB` | shadcn button default |
| `indigo-500` | `#6366F1` | Tailwind UI demo; zinc-dark accent |
| `indigo-600` | `#4F46E5` | Bolt bias; HSL ~226° |
| `violet-500` | `#8B5CF6` | Gradient stop; "AI purple" |
| `purple-500` → `pink-500` | `#A855F7` → `#EC4899` | `bg-gradient-to-br` hero |
| `gray-50` | `#F9FAFB` | Light canvas; grep the `<body>` |
| `slate-50` / `slate-950` | `#F8FAFC` / `#020617` | 2023 shadcn shell |
| `zinc-950` / `zinc-900` / `zinc-400` | `#09090B` / `#18181B` / `#A1A1AA` | 2026 dark stack |
| `#FFFFFF` on `#F9FAFB` | — | 1.01:1 card/canvas (already in ui.md) |
| `#000` on `#FFF` | — | Mechanical neutrals, no hue |
| `yellow-400` stars | `#FACC15` | Testimonial default |
| `green-500` / `red-500` / `yellow-500` | `#22C55E` / `#EF4444` / `#EAB308` | Untuned status |
| `cyan-500` | `#06B6D4` | Glow / "not-blue" escape |
| `emerald-500` | `#10B981` | Dark-mode "one pop" rotation |

Sailop 2025-Q4 sample, ~600 generated sites (approximate):

| Tool | Primary | Accent purple | Gradient | Dark/light shell |
|---|---|---|---|---|
| v0 | `blue-600` ~78% | `purple-500` ~52% | `from-purple-500 to-pink-500` ~41% | `slate-950` ~67% |
| Lovable | `blue-500` ~62% | `violet-500` ~48% | blue-via-purple-pink ~38% | `slate-900` ~55% |
| Bolt | `indigo-600` ~54% | `purple-500` ~46% | indigo→purple ~33% | `zinc-950` ~58% |
| Claude Artifacts | `blue-600` ~70% | `purple-500` ~44% | mostly avoids | `slate-50` ~71% |
| ChatGPT canvas | `blue-500` ~64% | `purple-500` ~42% | purple-400→pink-400 ~29% | `gray-900` ~52% |

### Consistency tells (the hole)

These ship *after* someone "picked a brand color."

| Tell | Fix |
|---|---|
| Raw `bg-blue-500` / `text-indigo-600` next to kit `--primary` / `bg-primary` | Grep tokens in the file. One source. New hex is drift |
| New screen a shade off (Veljanoski) | Same primitive, not a remembered Tailwind step |
| Custom accent, still `ring-blue-500` / `hover:bg-blue-700` | Hover/focus/disabled are L± on the *same* hue |
| Status still `green-500`/`red-500`/`yellow-500` | Mute into the palette (forest/rust), keep the meaning |
| Dark = invert the light hexes | Second palette: raise L, drop chroma; elevation via surface steps |
| Neutrals are `slate-*` while accent is warm | Tint the gray with the brand hue (already in ui.md, still skipped) |
| Gray body on a colored surface | Text from the surface hue, not `text-gray-400` |
| Light accent as white-text button (mustard/coral) | Dark text on the fill, or a darker `--accent-text` for links |
| Hex ramps that hue-shift (orange→brown, blue→purple) | OKLCH: hold H and C, walk L. Sibling detail; noslop: don't invent a second hue for hover |
| `gradient-start` names; decorative color | Semantic roles (canvas/text/action/danger) — already in ui.md |
| Chart/KPI series = Tailwind rainbow + color-only | Distinct L/C + label; length/position for quantity |
| Mixing two centroids (indigo CTA + cream canvas + acid-green chip) | One accent. The rest recedes |
| Teal as the "not blue" pick | Next safe default. Hue 190–200 and low chroma, or don't |

OKLCH is the craft tool for ramps
([Sailop accent](https://sailop.com/blog/how-to-pick-accent-color-not-tailwind-blue-2026);
impeccable `colorize.md`). Noslop does not become a color-science
skill: lock 4–6 values from the file or the subject, derive hover as
darker/same-hue, don't paste a new swatch.

### Next centroids (fleeing indigo is not uniqueness)

frontend-design / impeccable already warn: cream `#F4F1EA` +
terracotta serif; near-black + acid green/vermilion; broadsheet
hairlines. Sailop's own "human" starters include Atelier cream,
Brutalist gold-on-black, Cyberpunk `#00FF41`. Those are legitimate
when the *subject* earns them. As the unprompted swap they are the
same failure.

Teal (`#2a8c9c` / `cyan-500`) is the documented escape hatch that is
already filling. Plum that is not violet-500 is still purple-family —
chroma and hue offset matter more than the word "not indigo."

Derive the accent from the product (name, material, competitive gap),
one sentence: "burnt sienna because the hero photographs as leather."
If you cannot write the sentence, you have a hex, not a pick.

### Already in noslop vs cheap fold

**Have:** indigo/violet/pink gradient; `blue-600`/`indigo-500`;
`#000`/`#fff`; gray-50 cards ~1:1; dark invert; hue-shifted
neutrals; semantic names; permanent dark + lavender; cream/terracotta
and black+acid-green as 2026 studio defaults; tokens match the file.

**Fold (generation-time, not a palette DB):**

1. Grep fingerprints: `#3B82F6` / `#2563EB` / `#F9FAFB` / `#09090B`
   when *inventing*. Match if the repo already is that.
2. Token locality: no raw Tailwind hue beside existing `--primary` /
   kit `primary`. Drift is a color bug, same class as invented Popover.
3. Derive hover/focus/status from the locked accent; don't keep
   `ring-blue-500` and `green-500`.
4. One line: ≤3 hues, roles are tints. 4–6 hex stays the lock.
5. Zinc-950 + indigo glow is the *current* dark centroid (name it;
   "permanent dark" is the Krebs stat, zinc is the hex).

**Leave to siblings:** 12 starter palettes, APCA vs WCAG, OKLCH
encyclopedia, pairing databases, impeccable Restrained/Committed/
Drenched strategies.

**Don't add:** always-light as the anti-dark reflex; "never blue"
(IBM/Apple/a real brand blue is a choice); a BM25 palette table in
`tells.csv`.

**Folded (same day).** Fingerprints, token drift, same-hue
hover/focus/status, ≤3 hues/roles-as-tints, zinc-950 dark centroid
→ `ui.md` + one SKILL slop-tell row + three CSV rows. No palette
DB, no APCA, no eval fixture.

### Eval if folding

Plant `--color-primary` (not blue) in the fixture theme. Agent adds a
new button: fail if it emits `bg-blue-500` / `bg-indigo-600` /
`from-purple-500`. Pass if it uses the token. Cheap, generation-time,
matches Veljanoski not Sailop's scanner.

## Round: code structure and simplicity (2026-08-30)

Went past the first-page recaps. Ranked by whether the source
*defines a testable rule*, not by SEO. Scrapes in
`.firecrawl/structure/scraped/`. Discarded: Medium “11 tips”,
`golang-standards/project-layout` (not a standard; see
[laurentsv](https://laurentsv.com/blog/2024/10/19/no-nonsense-go-package-layout.html)
and [go.dev/doc/modules/layout](https://go.dev/doc/modules/layout)),
Clean Code as a structure bible ([qntm](https://qntm.org/clean),
[Ousterhout vs Martin](https://github.com/johnousterhout/aposd-vs-clean-code),
[Muratori](https://www.computerenhance.com/p/clean-code-horrible-performance)).

### Canon (read these, not the summaries)

| Source | Claim that survives |
|---|---|
| [Hickey, Simple Made Easy](https://github.com/matthiasn/talk-transcripts/blob/master/Hickey_Rich/SimpleMadeEasy.md) | Simple ≠ easy. Simple = unbraided (one role, no interleaving). Easy = nearby/familiar. Modularity that still complects is fake. State complects value and time. |
| [Ousterhout, APOSD / CS190](https://web.stanford.edu/~ouster/cs190-winter23/) | Complexity = anything that makes the system hard to understand or change. Incremental. Deep modules: lots of function, small interface. Shallow + entangled methods are the Clean Code failure mode. Strategic over tactical. |
| [Gabriel, Worse is Better](https://www.dreamsongs.com/RiseOfWorseIsBetter.html) | Implementation simplicity beats interface completeness. Ship 50% that spreads; the last 20% is where MIT-style dies. |
| [tef, easy to delete](https://programmingisterrible.com/post/139222674273/write-code-that-is-easy-to-delete-not-easy-to) | Lines are spent. Repeat yourself to avoid a dependency; don’t to manage one. Layer clumsy-but-simple under pleasant-but-opinionated. Isolate what will change (Parnas). One hard problem per module, not “one thing” as tiny methods. |
| [Metz, Wrong Abstraction](https://sandimetz.com/blog/2016/1/20/the-wrong-abstraction) | Duplication cheaper than the wrong abstraction. Fastest way forward is back: inline, then re-extract. |
| [Abramov, Goodbye Clean Code](https://overreacted.io/goodbye-clean-code/) | DRY can trade away change. Don’t rewrite a teammate’s working code overnight. Optimize for evolution, not looks. |
| [Fowler, Yagni](https://martinfowler.com/bliki/Yagni.html) | Presumptive features cost build + delay + carry + repair. Abstractions that make *current* code harder are guilty. Yagni does *not* excuse skipping malleability (refactor, tests). Kohavi: ~⅔ of shipped features miss their metric. |
| [King, Parse don’t validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/) | A check that returns `()` threw the knowledge away. Parse at the boundary into a type that cannot represent the bad state; never re-check inside. |
| [Wlaschin / Minsky](https://fsharpforfunandprofit.com/posts/designing-with-types-making-illegal-states-unrepresentable/) | Optional+optional allows neither; a union of the three legal cases forbids the fourth. |
| [htmx LoB](https://htmx.org/essays/locality-of-behaviour/) | Behaviour of a unit should be obvious from that unit. Conflicts with DRY and SoC; distance of the spooky action is the severity. |
| [Google eng-practices](https://google.github.io/eng-practices/review/reviewer/looking-for.html) | Complexity = can’t be understood quickly, or callers will introduce bugs. Over-engineering: solve the problem you have *now*. Small CLs: one self-contained change. Approve once it *improves* health, not once it is perfect. Comments explain why. |
| [Go: layout](https://go.dev/doc/modules/layout), [package names](https://go.dev/blog/package-names), [proverbs](https://go-proverbs.github.io/) | Start with files in one package. `internal/`/`cmd/` when you actually have multiple consumers. No `util`/`common`/`api` dump. A little copying > a little dependency. Clear > clever. Bigger interface = weaker abstraction. |
| [Unix / ESR](http://www.catb.org/esr/writings/taoup/html/ch01s06.html) | McIlroy: one thing well, compose, throw away clumsy parts. Pike: don’t guess perf; data dominates; brute force until measured. Rule of Simplicity: add complexity only where you must. |
| [Beck / Lethain on Tidy First](https://lethain.com/notes-on-tidy-first/) | Tidying ≠ logic. Separate PRs. Guard clauses. Tidy before a change iff it lowers the cost of that change; else after, later, or never. |
| [Out of the Tar Pit](https://curtclifton.net/papers/MoseleyMarks06a.pdf) | Essential vs accidental complexity; state is the main accidental source (pairs with Hickey). |

### Consensus that is not Clean Code

These independent traditions agree. Treat disagreement with this
cluster as a smell.

1. **Simplicity is unbraiding, not familiarity or smallness.**
   Tiny functions and folder trees can still complect (Hickey,
   Ousterhout shallow modules, Go “too many packages”).
2. **Duplication is a holding pattern.** Copy twice; extract when
   the same *change* hits all copies. Inline when the shared helper
   grows flags (Metz, tef, Pike “a little copying”, Abramov).
3. **Put the helper next to the caller.** `util`/`common`/`misc`
   are failed package names (Go blog, tef, laurentsv).
4. **Don’t structure ahead of the second consumer.** Official Go
   layout: one package until it hurts. Unix: parsimony. Fowler:
   imagine the later refactor; often it’s cheap.
5. **Locality beats layering as a default.** Package-by-feature
   (javapractices) and LoB both say: a change should not require
   opening `controllers/` + `services/` + `dto/`. Layers are for
   *policy vs mechanism* (Unix, tef `requests` over `urllib3`),
   not for every noun.
6. **Validate once, at the edge, into a representation that
   cannot lie.** Parse-don’t-validate, illegal states, Google
   “define errors out of existence” (CS190: use judiciously),
   noslop trust.md already.
7. **Complexity is incremental.** Google: don’t accept CLs that
   degrade health by a little. Ousterhout: lots of little
   dependencies and special cases. Beck: coupling is the enemy.
8. **The patch is the unit.** Google small CLs; Beck tidy vs
   logic; noslop one slice. Drive-by rewrite is Abramov’s
   disaster mode.

### Real disagreements (do not flatten)

- **Comments.** Ousterhout wants interface comments *before* code
  and more of them; Google/noslop: why, not what; Hickey: don’t
  complect meaning into ceremony. For agents: why-comments stay;
  do not emit APOSD-density narration.
- **Function length.** Martin: 2–4 lines. Ousterhout: deep
  methods; combine entangled ones. qntm: the FitNesse “ideal”
  listing is a class of shallow wrappers. **Split when two stories
  interleaved, not at 80 lines.**
- **TDD.** Martin: design emerges. Ousterhout: TDD is too
  tactical; design squeezed out. For this skill: existing spec or
  a probe in a file you already touch — not a TDD ceremony.
- **Worse-is-better vs “define errors out of existence.”**
  New Jersey: simple implementation, caller retries. APOSD: don’t
  make the caller handle a case you can make impossible. Both
  reject completeness-as-virtue; they disagree on *where* the
  remaining ugliness lives. Prefer making the illegal state
  unrepresentable *at the boundary*; don’t invent retry loops
  inside trusted helpers.
- **SoC vs LoB.** Neither wins. Distance of the extra knowledge
  is the cost. A CSS file changing a button is milder than a
  jQuery handler in another package.

### Structure rules worth folding (if anything)

Already in SKILL (keep): locality, no speculative types, early
return, size-is-a-hint, copy twice / extract third, no `utils/`
for one caller, comments explain why.

**Cheap folds if we touch Structure again:**

- Name **complecting** (Hickey) as the test: if you must hold two
  modules in your head to understand one, they are not modules.
- Name **shallow**: a wrapper that only forwards, or a 3-line
  method whose callers still read the body.
- **Yagni costs:** delay + carry, not just “skip the feature.”
  An unused field is carry.
- **Go/Python layout:** do not invent `internal/`, `pkg/`,
  `cmd/`, `util/`, `types.ts` barrels because a blog said so.
  Official Go: files in one package; split when you have a second
  importable surface.
- **Tidy vs logic:** refactor.md already says no new files;
  add: don’t mix a rename-move with a behavior change (Google +
  Beck). Already implied by “no drive-by.”

**Don’t fold:** Ousterhout’s comment-first workflow; Clean Code
chapter 3 as a checklist; hexagonal/screaming architecture as
default tree; FCIS as a required folder (`domain/` + `app/`) —
the Google testing-blog version is “pure functions in the middle,
I/O at the edge,” which trust.md already says.

### Firecrawl query log (this round)

Search (then feedback): Hickey, Clean Code critiques, Worse is
Better, Effective Go, PEP 20, Google Python, LoB, Muratori, Beck,
Rust API, Ousterhout, Tar Pit, tef, Metz, Yagni, Abramov, parse
don’t validate, Google eng-practices, Go Proverbs, cognitive
complexity, SQLite, Unix, CS190, boring tech, FCIS, illegal
states, golang-standards critique, package-by-feature, Go package
names. Map: CS190 winter23. Scrape: the canon table above plus
CS190 intro/aposd, Google looking-for/standard/small-cls, Go
layout/names/proverbs, laurentsv, Lethain, Wlaschin, Unix ch01s06.
Google FCIS blog scrape was blocked (ads); treat as Bernhardt
Boundaries + “I/O at the shell.” Developer index was mostly
CLAUDE.md clones and YAGNI restatements — Fowler’s bliki is the
hit.

## Round: model style / quality issues (2026-08-30)

Source: Firecrawl search
`most code style / quality issues new models have`
(Downloads JSON + [arxiv:2503.06327](https://arxiv.org/html/2503.06327)
taxonomy, [arxiv:2407.00456](https://arxiv.org/html/2407.00456v1)
style inconsistencies). Developer-index and news hits were
Laravel/god-class/Pylint ceremony or already in trust.md.

### Already in Noslop (do not re-fold)

Swallowed except, invented success, `as any`, parse-at-boundary,
hardcoded secrets, path join, N+1, unused imports, restating
comments, copy-twice/extract-third, match-this-file format,
stdlib-after-tree ladder, types-green ≠ user path, defensive
checks on trusted inner paths (models *over*-validate; cleanup
already strips that).

### Folded (gaps only)

From the 19-subcategory taxonomy + top style miss (API usage
= builtin instead of the named helper):

| Tell | Where |
|---|---|
| Builtin that duplicates a named helper | SKILL ladder 2 |
| `pass` / return-args / hardcoded sample | SKILL, fix.md |
| else/fallback skips the named check | SKILL |
| used name not imported; ghost `hasattr`/`?.` | SKILL, ts/js |
| else after return; bool wrap; same call twice | SKILL, langs |
| stub that types-checks is not the path | Done |
| unused bindings; commented-out code | cleanup, leftovers |
| hook `{data, refetch}` with no error | react.md |
| emit field/method the type does not have | typescript.md |
| shadow `dict`/`list`/`id`/`type` | python.md |

### Don't fold

O(n²)→O(n log n) or list→generator as a default (optimize.md:
named bottleneck only). God-class extraction, magic numbers,
blank-line religion, hexagonal lint, Laravel Form Request as
universal, PhysicsNeMo docstring rules, Pylint score theater.
Self-repair introducing *new* files of issues: fix.md already
forbids "also fixed"; added "breaks another path in the same
function."

## Round: model style / quality issues, search 2 (2026-08-30)

Source: Firecrawl search same query, larger result set
(`…22_10_18.461Z.json`: 80 web, 100 papers). Most hits
repeat the first search or are generic style/PEP 8.

### New, testable

| Source | Tell | Fold |
|---|---|---|
| [nrehiew, Over-Editing](https://nrehiew.github.io/blog/minimal_editing/) | One-line bug, half the function rewritten; extra None checks, helpers, renames; tests still pass | SKILL, fix.md, `over-edit` |
| [Patchwork Problem](https://arxiv.org/html/2607.08981) | Locally-green patch: undeclared env, hallucinated dep, missing sibling auth, invented schema field, file that isn't there | SKILL, trust.md, tells |
| [Nimbalyst 5 patterns](https://nimbalyst.com/blog/bugs-ai-writes-patterns-in-ai-generated-code/) | Sibling copy-paste drift; refactor changes return/throw/default | sibling-drift, contract-change, refactor.md |
| [PLC](https://arxiv.org/html/2503.13620) | Code in the wrong language | `lang-mix` |
| [2406.08731](https://arxiv.org/html/2406.08731v1) | Missing/incorrect condition or code block | already half-spec / stub-logic |
| [2407.06153](https://arxiv.org/html/2407.06153v1) | Fewer lines, higher complexity | already named intermediates |
| [Codex #9372](https://github.com/openai/codex/issues/9372) | Compact unreadable / wants more comments | do **not** fold “add comments”; named intermediates already |

### Already in / don't fold

Hallucinated package, sibling `requireAuth`, `.env.example`,
tautological tests, happy-path-only, `as any`, secrets, path
join. SWE-bench-pass ≠ mergeable is over-edit. Codex “20%
comments” fights this skill.

## Deep Research follow-up: intent, degradation, and proof (2026-08-31)

The companion corpus [research-ai-want-hate.md](../research-ai-want-hate.md)
contains 286 deliberately phrased want/hate queries and 1,413 capped
search hits. It is useful for discovery and vocabulary, not prevalence:
the list is hate-heavy, ranking is biased, and repeated URLs are not
independent observations.

Targeted primary/authoritative follow-up:

- [METR's randomized developer study](https://metr.org/blog/2025-07-10-early-2025-ai-experienced-os-dev-study/?stream=top)
  measured realistic repository work and found a 19% slowdown for its
  early-2025 setting. METR separates that result from benchmark scores
  and anecdotes. Rule: measure the named task and do not generalize a
  local green check into productivity.
- [SlopCodeBench](https://arxiv.org/abs/2603.24755) evaluates repeated
  extensions and reports structural erosion in 77% of trajectories and
  verbosity in 75.5%; guidance improved initial quality but did not stop
  degradation. Rule: re-read and strip after extensions; add iterative
  evals, not only one-shot pass rates.
- [SpecBench](https://arxiv.org/abs/2605.21384) separates visible tests
  from held-out composition tests to measure reward hacking. Rule: a
  named test total is not proof of the composed user path.
- [NN/G's vague-prompt study](https://www.nngroup.com/articles/vague-prototyping/)
  found broad prompts produced repetition and weak hierarchy;
  [its real-context evaluation](https://www.nngroup.com/articles/ai-prototyping/)
  found specific requirements improved prototypes. Rule: name the UI
  job, hierarchy, states, references, and constraints before CSS.
- [Usable but Conventional](https://arxiv.org/abs/2605.15124) found
  positive pragmatic UX but neutral/negative originality and innovation
  ratings in a 92-person prototype study. Rule: check usability and
  originality separately; do not replace a product direction with a
  default centroid.
- [Everyone prefers human writers, including AI](https://arxiv.org/abs/2510.08831)
  found authorship labels changed literary evaluations in controlled
  experiments with 556 people and 13 AI evaluators. Rule: preserve voice
  and judge claim, fit, and evidence directly; do not use detectors as a
  humanization oracle.
- [WCAG 2.2](https://www.w3.org/TR/WCAG22/) supports the existing
  contrast, focus, and target-size rules. [React's guidance](https://react.dev/learn/synchronizing-with-effects)
  supports deriving values during render and reserving Effects for
  synchronization with external systems.

### Resulting improvements

Keep the existing minimal-diff, local-style, boundary-error, and
anti-centroid rules. Sharpen them with a short ordered Run contract in
`SKILL.md`, explicit `VERIFIED | NOT VERIFIED | INCONCLUSIVE` closeout,
voice/source rules in `copy.md`, reference-first UI constraints in
`ui.md`, composed-path language in test/QA guidance, Swift/Vue/Docker
loads, focused job routes, and `scripts/validate.py` plus stricter eval
result validation. Avoid a larger universal blacklist: the evidence
supports gates, artifacts, and feedback loops more strongly than more
prompt prose.




