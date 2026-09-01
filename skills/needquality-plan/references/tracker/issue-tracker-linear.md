From mattpocock/skills (MIT).

# Issue tracker: Linear

Issues and specs for this repo live as Linear issues. Use the
Linear MCP tools that are already connected. Do not ask them to
install a second skill.

## Conventions

- **Create an issue**: `save_issue` with title and body.
- **Read an issue**: `get_issue`, then `list_comments`.
- **List issues**: `list_issues` with team/project and status
  filters. Use `list_issue_statuses` when you need state names.
- **Comment on an issue**: `save_comment`.
- **Apply / remove labels**: `list_issue_labels`, then
  `save_issue` with the label set. Create a missing label with
  `create_issue_label` only when they asked.
- **Close**: `save_issue` with the Done/cancelled status from
  `list_issue_statuses`.

Resolve the team from `list_teams` if the issue id does not
already name one.

## Pull requests as a triage surface

**PRs as a request surface: no.** Linear is not a PR host.
External PRs stay on GitHub/GitLab; only file a Linear issue when
the user asked.

## When a skill says "publish to the issue tracker"

Create a Linear issue.

## When a skill says "fetch the relevant ticket"

`get_issue` on the id (e.g. `TEAM-123`).

## Wayfinding operations

Used by [wayfinder](../wayfinder.md). The **map** is a
single issue; tickets are child issues.

- **Map**: one issue labelled `wayfinder:map` (or that role in
  the body). Hold Notes / Decisions-so-far / Fog there.
- **Child ticket**: a Linear sub-issue of the map when the
  workspace supports it; otherwise `Part of TEAM-n` at the top
  of the child body. Labels: `wayfinder:<type>`
  (`research`/`prototype`/`grilling`/`task`). Once claimed,
  assign the ticket to the driving user (`list_users` /
  `save_issue`).
- **Blocking**: Linear blocked-by relations when the workspace
  has them. Otherwise a `Blocked by: TEAM-n, TEAM-n` line at the
  top of the child body. A ticket is unblocked when every
  blocker is Done.
- **Frontier query**: open children of the map, drop any with an
  open blocker or an assignee; first in map order wins.
- **Claim**: assign the issue to yourself, the session's first
  write.
- **Resolve**: `save_comment` with the answer, then mark Done,
  then append a context pointer to the map's Decisions-so-far.
