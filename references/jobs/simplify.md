# Simplify

Read this when they said simplify, simpler, or less code. Shorter,
same behavior. Deletion is the tool.

1. Existing tests green before and after, or add one assertion
   that pins the behavior first.
2. Inline one-caller helpers and wrappers that only forward.
   Delete unused. Flatten nesting with early return. Don't delete
   a path they did not ask to remove. If two files must be read
   together, putting them in more folders is not simpler.
3. Named helper in the tree → import it; don't paste a "simpler"
   clone.

Don't: a new abstraction that "hides complexity", stripping
validation, or a rewrite. Shape-only is [refactor.md](refactor.md).
