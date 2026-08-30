# Refactor

Read this when they said refactor. Same behavior, different shape.
The named code only.

1. Name the smell in one line (duplication, nesting, wrong layer).
   Can't → one question, or stop.
2. Existing tests must cover the behavior, or add one assertion
   first. Then change shape. Run them.
3. Extract / inline / move / rename. No new file, type, wrapper,
   or config. No `fooV2`. One-caller helper stays next to the
   caller. Don't mix a rename or move with a behavior change —
   two diffs. If callers still have to read the extracted body,
   you split too far: combine.
4. Stop when the named smell is gone. Don't restyle neighbors.

Don't: rewrite the module, add a pattern, "while I'm here."
"Simplify" is [simplify.md](simplify.md). "Clean up" is
[cleanup.md](cleanup.md).
