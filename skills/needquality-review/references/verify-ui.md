# Verify UI

Read this when they said screenshot this, verify in the browser,
click through, or prove the UI works. One user path. Not a rewrite.
"Check this" without a browser verb is [review.md](review.md).

1. Named route or flow. Live page. Prefer the repo's Playwright
   or agent-browser if present.
2. Drive it: click, type, submit. A screenshot or first paint is
   not done. Open every route that reads the state you wrote.
3. One verdict: VERIFIED | NOT VERIFIED | INCONCLUSIVE plus
   evidence. No browser → name what you could not verify.

Don't: restyle, add features, claim from a snapshot alone.
