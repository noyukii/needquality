# Review

Read this when they said review, look over, check this, take a look,
or code review. A review is work you can run, not a memo.

Do not rewrite the product. Do not emit a report file. Do not
rubber-stamp. Two words ("review and fix") → this file, then
[fix.md](fix.md).

## Job

1. **Target.** Diff, PR, file, or function they named. Unnamed →
   `git diff` against `main`/`master` (or the repo default). PR
   number or URL → `gh pr diff`; do not `gh pr checkout` unless
   they asked to. Don't invent a second surface to review.

2. **Docs.** For each non-obvious API, import, or protocol in the
   target, fetch the real page (library docs, MDN, framework).
   Training-set memory is how hallucinated methods survive review.
   Quote the mismatch. Fetch blocked → say so and grep the installed
   types/README in the tree.

3. **Guidelines.** Repo `AGENTS.md` / `CONTRIBUTING` / `CLAUDE.md` /
   existing tests / the language file for these extensions (Load
   table). The file's own indent, helpers, and error pattern beat
   a generic checklist. This skill's rules apply to findings; they
   are not a license to restyle.

4. **Tests.** Extend an existing assertion or use a probe in a file
   already in scope that would go red if a finding is real. Run it
   this turn. If no test or probe seam exists, run the smallest
   relevant command and state that targeted test coverage was
   unavailable; never create a test file solely for review. A review
   with no command is a comment. User said "review" → verification is
   in scope. Tautological `expect(fn()).toBe(fn())` is not a review.

5. **Findings.** Only what you can point at: doc quote, failing
   test, guideline line, or a path you traced. Wrong / unsafe /
   unbounded at the named load. Each finding gets severity, file and
   line, impact, evidence, and the smallest fix. Skip nits, naming
   taste, and "consider extracting." If none, say no findings and
   name the command you ran.

## Don't

- Architecture lecture, factory, new folder, extra markdown
- Approve on "looks correct" / types green / a checklist you
  did not execute
- Drive-by rewrite of the code under review
- Review a file you did not open
- Security theater (flag every `any`) — exploitable only, or they
  asked for a security pass
