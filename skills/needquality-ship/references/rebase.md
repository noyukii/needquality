# Rebase

Read this when they said rebase onto, tidy commits, or squash these.
This is a requested history rewrite, not the merge-conflict flow.

1. Check branch, base, status, and the commits in scope. A dirty tree
   is a stop; do not stash or overwrite work automatically.
2. Fetch only the named base if needed. Rebase onto that ref, or use
   interactive rebase for the exact squash/reorder they named.
3. On conflict, stop and hand to `resolving-merge-conflicts`; do not
   guess at intent. Abort on request or when the operation cannot be
   completed safely.
4. Re-read the resulting diff and commit list. Verify tree identity
   and run the existing narrow check before reporting success.

Don't: force-push, amend an unnamed commit, rewrite a shared branch, or
mix a behavior change into a history-cleanup request.
