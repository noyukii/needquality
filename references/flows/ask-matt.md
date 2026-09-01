From mattpocock/skills (MIT). Read when the Words/Load row names this file.

# Ask Matt

You don't remember every skill, so ask.

A **flow** is a path through the skills. Most paths run along one **main flow**, and two **on-ramps** merge onto it. Everything else is standalone, or a vocabulary layer that runs underneath.

## The main flow: idea → ship

The route most work travels. You have an idea and want it built.

1. **[grill-with-docs](grill-with-docs.md)** sharpens the idea by interview. Start here whenever you are **working in a working directory**: it's stateful, retaining what it learns in `CONTEXT.md` and ADRs. (No working directory? Use [grill-me](grill-me.md) instead, covered under Standalone. Both run the same [grilling](grilling.md) primitive; `grill-with-docs` is the one that leaves a paper trail, which makes it the better of the two whenever a repo is there to leave it in.)
2. **Branch: can you settle every question in conversation?** If a question needs a runnable answer (state, business logic, a UI you have to see), detour through a prototype, bridged by **[handoff](handoff.md)** in both directions (a prototype lives in its own directory, which is exactly what [handoff](handoff.md) is for; see Phase boundaries):
   - **[handoff](handoff.md)** out, then open a fresh session against that file,
   - **[prototype](prototype.md)** to answer the question with throwaway code,
   - **[handoff](handoff.md)** back what you learned, and reference it from the original idea thread.
3. **Branch: is this a multi-session build?**
   - **Yes** → **[to-spec](to-spec.md)** (turn the thread into a spec), then **[to-tickets](to-tickets.md)** to split it into tracer-bullet tickets, each declaring its **blocking edges**. On a local tracker that's one file per ticket under `.scratch/<feature>/issues/`, worked blockers-first by hand; on a real tracker the edges become native blocking links, so any ticket whose blockers are done can be grabbed: kick off **[implement](implement.md)** per ticket with a fresh context when the host supports one. Each ticket is self-contained, so the last one's context is disposable.
   - **No** → **[implement](implement.md)** right here, in the same context window.

   Either way, **[implement](implement.md)** builds each issue by driving **[tdd](tdd.md)** internally (one red-green slice at a time), then closes out by running **[code-review](code-review.md)**, a two-axis review (Standards + Spec) of the diff, before committing. Reach for **[tdd](tdd.md)** on its own when you just want to build a concrete behaviour test-first without a full spec, and **[code-review](code-review.md)** on its own whenever you want to review a branch or PR against a fixed point. **[implement-spec](implement-spec.md)** is the other implementer: parallel worktrees on one PR. Words: `implement-spec`. Not `implement the spec`.

### Context hygiene

Keep steps 1–3 in **one unbroken context window** (don't compact or clear until after [to-tickets](to-tickets.md)) so the grilling, spec, and tickets all build on the same thinking. Each [implement](implement.md) then starts fresh, working from the ticket.

The limit on this is the **[smart zone](https://www.aihero.dev/ai-coding-dictionary/smart-zone)**: the useful context remaining for sharp reasoning. If a session approaches its host limit before [to-tickets](to-tickets.md), use the host's context-compaction facility at the nearest phase boundary, or create a handoff when no such control exists.

## On-ramps

A starting situation that generates work, then merges onto the main flow.

- **Bugs and requests piling up** → **[triage](triage.md)**. It moves issues through triage roles and produces agent-ready issues, which **[implement](implement.md)** later picks up.

  Triage is only for issues **you didn't create**: bug reports, incoming feature requests, anything that arrives raw. Tickets that [to-tickets](to-tickets.md) produced are already agent-ready, so **don't triage them**.

- **Something's broken** → **[diagnosing-bugs](diagnosing-bugs.md)**. For the hard ones: the bug that resists a first glance, the intermittent flake, the regression that crept in between two known-good states. It refuses to theorise until it has a **tight feedback loop** (one command that already goes red on *this* bug), then fixes with a regression test. Its post-mortem hands off to **[improve-codebase-architecture](improve-codebase-architecture.md)** when the real finding is that there's no good seam to lock the bug down.

- **A huge, foggy effort: a greenfield project or a huge feature build, too big for one session** → **[wayfinder](wayfinder.md)**, the most cognitively demanding flow here. When the way from here to the destination isn't visible yet, it charts a **shared map** of **decision tickets** on the issue tracker and resolves them one at a time, producing **decisions, not deliverables**, until the fog is pushed back and the way is clear. Where **[grill-with-docs](grill-with-docs.md)** sharpens an idea you can hold in one session, wayfinder is for the idea you can't, and it's slower and denser, so save it for exactly that, never a well-scoped feature.

  When the map clears, **it hands off, it doesn't build**: merge onto the main flow at **[to-spec](to-spec.md)**, which collapses the map's linked decisions into a buildable plan, then [to-tickets](to-tickets.md) and [implement](implement.md) as usual. Looping the map straight into [implement](implement.md) skips that collapse and throws the linked detail away, so go straight to [implement](implement.md) only when the effort turned out genuinely small.

## Codebase health

Not feature work, just upkeep.

- **[improve-codebase-architecture](improve-codebase-architecture.md)** runs whenever you have a spare moment to keep the codebase good for agents to operate in. It surfaces **deepening opportunities**; picking one _generates an idea_ you can take into the main flow at [grill-with-docs](grill-with-docs.md). It's the survey that finds the candidates; **[codebase-design](codebase-design.md)** (below) is the bench you design the chosen one on.

## Vocabulary underneath

Two root-routed references run *beneath* the other flows, each the single source
of truth for its vocabulary. Reach them through `$needquality` when the
**words**, not the process, are the problem; other flows may route to them too.

- **[domain-modeling](domain-modeling.md)**: sharpen the project's *domain* language: challenge a fuzzy term, resolve an overloaded word ("account" doing three jobs), record a hard-to-reverse decision as an ADR. It's the active discipline [grill-with-docs](grill-with-docs.md) drives to keep `CONTEXT.md` a clean glossary.
- **[codebase-design](codebase-design.md)** is the deep-module vocabulary (module, interface, depth, seam, adapter, leverage, locality) for designing a module's *shape*: a lot of behaviour behind a small interface at a clean seam. [tdd](tdd.md) and [improve-codebase-architecture](improve-codebase-architecture.md) both speak it. **[setup-ts-deep-modules](setup-ts-deep-modules.md)** installs the dependency-cruiser rules that enforce that shape.

## Phase boundaries

A **phase** is a chunk of work inside a session: the grilling, the implementation, the QA. At the **boundary** between two of them you have five options, and picking between them is the fuzziest decision in this whole map:

- **Continue**: stay put. Costs nothing, loses nothing.
- **Fresh context**: start without the current transcript when nothing here matters to what's next and the host supports it.
- **[handoff](handoff.md)** writes a portable markdown file. Narrow: only for a **new harness**, a **new directory**, a **colleague**, or forking a side task **mid-phase**. What it buys is portability.
- **Subagent**: send a tightly-scoped task to its own window and get a report back.
- **Compact context**: use the host's summary/context-boundary control when relevant context must carry forward. It is the default at the bottom of the tree, not the first reach.

Read [PHASE-BOUNDARIES.md](ask-matt/PHASE-BOUNDARIES.md) for the ordered tree:
the five questions, the reasoning behind each branch, and why the
primary-source cost makes **Continue** the one to rule out first. Make the
decision **at** a boundary; mid-phase, continue or split independent work when
the host supports it.

## Standalone

Off the main flow entirely.

- **[grill-me](grill-me.md)**: the same relentless interview as [grill-with-docs](grill-with-docs.md), but **stateless**: it saves nothing locally and builds no `CONTEXT.md`. Reach for it when you are **not working in a working directory** (sharpening a plan, a design, a piece of writing, anything with no repo under it). If you are in a working directory, use [grill-with-docs](grill-with-docs.md) instead: it runs the same interview and leaves a paper trail, so it is strictly the better one.
- **[grilling](grilling.md)** is the interview primitive itself: rounds, the frontier, facts are the agent's job and decisions are yours. [grill-me](grill-me.md) and [grill-with-docs](grill-with-docs.md) are the two named ways in, and [triage](triage.md), [wayfinder](wayfinder.md) and [improve-codebase-architecture](improve-codebase-architecture.md) all run it internally. Reach for it directly only when you want the interview with no wrapper around it.
- **[resolving-merge-conflicts](resolving-merge-conflicts.md)** works an in-progress merge or rebase conflict hunk by hunk, resolving by **intent** traced to each side's primary source rather than by picking lines, then finishes the operation. It never runs `--abort`. Standalone and off every flow: reach for it when you are already mid-conflict.
- **[prototype](prototype.md)** is a small, throwaway program that answers one design question: does this state model feel right, or what should this UI look like. Throwaway is a constraint on how the code is written, not a promise to destroy it: the answer folds into the real code, and the prototype itself is kept as a **primary source** on a `prototype/<name>` branch out of main, pointed at from the implementation issue. It's the detour in step 2 of the main flow, but reach for it any time a design question is hard to settle on paper.
- **[research](research.md)**: investigate a question against **primary sources**, then leave a cited Markdown file in the repo. An independent worker may handle the reading legwork when the host provides one; otherwise do the same work sequentially in the current session. The file it produces is something to take *into* the main flow at [grill-with-docs](grill-with-docs.md), since research feeds the thinking rather than replacing it.
- **[to-questionnaire](to-questionnaire.md)** comes in when the thing blocking you isn't in your head or the codebase but in **someone else's**, and it writes them a questionnaire to fill in. It's the inverse of [grill-me](grill-me.md): instead of interviewing you about the subject, it interviews you about the **send** (who it's going to, what you need back) and aims the questions at the gap. What comes back is material for [grill-with-docs](grill-with-docs.md) or [to-spec](to-spec.md).
- **[wizard](wizard.md)** is for the steps only a **human** can take: provisioning infrastructure, setting up credentials or CI secrets, clicking through an unfamiliar third-party dashboard, running a one-off migration or cutover. It generates an interactive bash script that opens each URL, captures each value, and writes it into `.env` and GitHub secrets, so the procedure stops being something you re-explain to an agent every time. Root-routed, so the agent selects it when the task reaches a wall only you can pass. If the agent could just do it itself, it should; this is for where a human is genuinely in the loop.
- **[wait-what](wait-what.md)** is the corrective for a message that didn't land. Use it mid-conversation, inside any other flow, and the agent re-pitches what it just said with the context you were missing, in plain English, using the `CONTEXT.md` vocabulary. It works after the fact; [grill-with-docs](grill-with-docs.md) is the upfront cure, because a shared language agreed early is what stops the jargon arriving at all.
- **[teach](teach.md)**: learn a concept over multiple sessions, using the current directory as a stateful workspace.
- **[writing-for-agents](writing-for-agents.md)** is the reference for writing documents agents consume: skills, AGENTS.md, pointed-at docs.
- **[writing-fragments](writing-fragments.md)** mines a pile. **[writing-beats](writing-beats.md)** and **[writing-shape](writing-shape.md)** turn that pile into an article. Not the `document` job.
- **[loop-me](loop-me.md)** grills life/work loops into `workflows/*.md`.

## Precondition

**[tracker](tracker.md)**: read it before spec, tickets, triage, or wayfinder. It detects the tracker. Custom issue trackers also work.
