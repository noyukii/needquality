# Fix

Read this when they said fix, bug, or broken. Reproduce, then one
root-cause patch.

1. Get a command red on *this* bug, or name why you cannot.
   Already gone → stop.
2. Grep callers (and sibling DTO, middleware, tests). One guard
   at the shared site, not a patch on the ticket path only.
3. Don't wrap in `try/catch` / `items ?? []` / `?.` through
   required data. Don't delete the test that exposed it. `pass`,
   returning the input, or a hardcoded sample is not a fix.
4. Run the same failing command after the patch. Quote its fresh exit
   and output. Then run the narrow regression already in the repo. A
   repair that breaks another path in the same function is not done.

Don't: shotgun guards, a rewrite of the rest of the function,
a rename, extra validation, a new helper, a sibling feature,
"also fixed." The failing line is the patch.
