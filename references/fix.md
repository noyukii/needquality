# Fix

Read this when they said fix, bug, or broken. Reproduce, then one
root-cause patch.

1. Get a command red on *this* bug, or name why you cannot.
   Already gone → stop.
2. Grep callers (and sibling DTO, middleware, tests). One guard
   at the shared site, not a patch on the ticket path only.
3. Don't wrap in `try/catch` / `items ?? []` / `?.` through
   required data. Don't delete the test that exposed it.
4. Run the failing command until green. Quote it.

Don't: shotgun guards, a rewrite, a sibling feature, "also fixed."
