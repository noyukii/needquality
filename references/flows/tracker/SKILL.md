---
name: tracker
description: >
  Detect which issue tracker this repo uses and read that sibling
  file. Used by spec, tickets, triage, and wayfinder.
---

From mattpocock/skills setup docs (MIT). Read when spec, tickets,
triage, or wayfinder need a tracker.

Pick one sibling and stop. Never ask them to install or run
another skill.

1. Linear MCP is usable →
   [issue-tracker-linear.md](issue-tracker-linear.md)
2. `git remote -v` is a GitHub host and `gh` works →
   [issue-tracker-github.md](issue-tracker-github.md)
3. GitLab host and `glab` works →
   [issue-tracker-gitlab.md](issue-tracker-gitlab.md)
4. Else → [issue-tracker-local.md](issue-tracker-local.md)

A named custom tracker still uses
[issue-tracker-local.md](issue-tracker-local.md). Write one
paragraph of their workflow at the top of the first issue you
create; do not invent a second tracker file.

Then [triage-labels.md](triage-labels.md). Apply those labels when
they exist on the tracker; otherwise write the canonical role in
the issue body.

Domain glossary: [domain.md](domain.md).
