# Tests

Read this when they said test, add tests, or coverage. They asked
for tests. Tests are the deliverable.

1. Existing spec / runner first. New `*.test.*` only if there is
   nothing to join. Match that file's runner and style.
2. Assert a known outcome at a public seam. Empty, missing,
   duplicate, timeout — not demo input only. Not
   `expect(fn()).toBe(fn())`, not "the mock was called" unless
   that is the contract.
3. Mock at the I/O boundary. Don't `sleep`. Don't bless a giant
   snapshot.
4. Run the runner on the touched path this turn. Quote it.

Don't: a second framework, 100% coverage theater, deleting or
weakening the grader to get green.
