# Cleanup

Read this when they said clean up, cleanup, deslop, or polish.
Diff against `main`/`master` (or what they named). Strip AI slop
from *that* diff. Behavior stays unless the slop is a clear bug.

## Strip

- Extra comments: restating, banners, inconsistent with this file
- `try/catch` / defensive checks on trusted inner paths
- `any` / `as T` / `@ts-ignore` that only silences the compiler
- Deep nesting → early return
- Unused, leftover instrumentation, invented helpers, extra
  markdown, drive-by formatting
- Anything else that does not match this file's indent, imports,
  naming, or error pattern

Trust-boundary validation and authz stay. Ugly nearby code has a
reason; read it before rewriting.

## How

1. That diff is the world. Don't restyle files it doesn't touch.
2. Large diff: `python scripts/lookup.py --ext <ext>` from this
   skill directory (stdlib). Fingerprint dump, not a Load of
   ui.md. Skip lookup for a one-file logic patch.
3. Minimal focused edits. No new files, no architecture.
4. 1–3 sentence summary.

Don't: a formatter pass on the repo, "polish" that changes copy
they didn't ask to change.
