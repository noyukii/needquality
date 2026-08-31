Read this when they said CI is red, fix CI, or make CI green. This is
failure isolation, not a feature implementation or refactor.

1. Identify the exact workflow, job, commit, and first actionable
   failure. Use the repo's check command or `gh pr checks` when a PR is
   in scope. Do not trust a summary badge alone.
2. Reproduce that failure on the same tree and environment when
   possible. Fix one cause. Do not skip, weaken, quarantine, or rewrite
   the check to make it green.
3. Re-run the same red command and the full check set. Report
   `VERIFIED`, `NOT VERIFIED`, or `INCONCLUSIVE` with commands and
   counts. If logs are truncated or the runner is unavailable, say so.

Don't: clean unrelated files, upgrade dependencies as a reflex, or
claim CI is green from a local command that is not the named check.
