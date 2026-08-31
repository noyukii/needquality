# Skill mechanics

The skill-specific branch of [writing-for-agents](../writing-for-agents.md).
Use it for frontmatter, invocation, packaging, and router decisions. The main
flow still controls how to write the instructions.

## Portable core

Every portable skill has one directory and one root `SKILL.md`. Its YAML
frontmatter contains `name` and `description`; keep trigger conditions in the
description because it is the discovery pointer. Put detailed or conditional
material in plain reference files linked from the root. A bundled reference is
not another skill and must not be named `SKILL.md`.

Treat these as the cross-agent contract:

- lowercase hyphenated directory and matching `name`;
- a description that states both capability and trigger conditions;
- imperative body instructions;
- relative links that remain inside the skill;
- one discoverable root, with shallow references loaded on demand.

## Invocation extensions

Implicit-versus-explicit invocation is host policy, not a portable frontmatter
contract. Keep `description` in portable frontmatter even for a skill intended
for explicit use.

- Claude and Cursor may support `disable-model-invocation`; treat it as their
  extension and verify the installed host version before using it.
- Codex uses `policy.allow_implicit_invocation` in `agents/openai.yaml`.
- Other hosts may expose neither control. Document the intended use and keep
  the portable skill valid without an extension.

Do not copy one host's extension into the common frontmatter and call it
portable. Product-specific configuration belongs under `agents/` or the
equivalent host-owned location.

## Router skills

Use one root router when several workflows share a quality contract. Keep a
deterministic route table in the root, link each route to a plain reference,
and validate that every bundled workflow is reachable. Prefer the longest
explicit phrase, select one primary route, then add orthogonal references such
as language or trust guidance.

Split a workflow into its own discoverable skill only when it has a genuinely
independent trigger and should be usable without the router. Otherwise a
second `SKILL.md` creates another discovery surface and can collide with the
router.
