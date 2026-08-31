Read this when they said QA this, QA pass, or test the user path. QA is
a product pass, not a unit-test summary.

1. Name the route or flow, test data, and expected outcome. Use the
   repo's browser/API harness; no harness means report that limitation.
2. Exercise the happy path plus relevant empty, loading, error,
   disabled, permission, and mobile states. Re-enter after navigation;
   stale screenshots or element handles are not evidence.
3. File findings with path, observed result, and reproduction. Do not
   implement unrelated fixes during the pass. Close with one verdict
   and the edges not checked.

Don't: call a screenshot, types check, or unit-test total a QA pass.
