From mattpocock/skills (MIT). Read when this skill's SKILL.md names this file.

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

Include a "suggested routes" section naming `$needquality` and the root-routed
flow or load slugs the next agent should select. Do not describe bundled
references as independently discoverable skills.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
