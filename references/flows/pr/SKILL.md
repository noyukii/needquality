---
name: pr
description: Open a pull or merge request from this-turn diff.
---

Read this when they said open a PR, create a pull request, open an
MR, write a PR description, or ship a PR. One branch. Do not
implement. Two-axis review stays the review row.

1. Status this turn: branch, `git diff` against the base
   (`main` / `master` or the repo default), `git log`.
2. Title matches this repo's PR style. Body from this-turn diff:
   Summary + Test plan. No invented `Closes #N`.
3. Open with `gh pr create` or `glab mr create` from the remote.
   Quote the URL.

Don't: force-push, merge, review-as-rewrite, a second feature.
