# Commit

Read this when they said commit, write a commit, or git commit.
Stage the named diff. Do not implement.

1. `git status` and `git diff` this turn. Stage only the paths
   they named, or the patch you just made. Split mixed hunks.
2. Message matches this repo's `git log`. Conventional if that is
   the log (`feat` / `fix` / `chore`). Subject = why. No AI
   footer unless they require it. No invented `Closes #N`.
3. Commit. Quote the hash. Do not push unless they asked.

Don't: new files they did not ask for, restyle, `--amend` or
`--no-verify` unless they asked.
