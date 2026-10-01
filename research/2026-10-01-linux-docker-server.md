# Linux, Docker, and server management research

Date: 2026-10-01. Scope: author two skills and extend Docker guidance for an
existing Ubuntu/Debian VPS using systemd, Compose, and a reverse proxy.

The supplied plan reports completed Firecrawl research on this date. This
implementation rechecked primary sources through the web tool; it did not rerun
Firecrawl. Local pre-edit validation confirmed 34 skills, 79 evaluation cases,
and 3,078 of 3,200 estimated metadata tokens.

## Findings and sources

| Finding | Primary source checked |
|---|---|
| Inspect SSH include precedence and effective authentication methods; validate configuration and stage port transitions while preserving working access | [Ubuntu OpenSSH](https://ubuntu.com/server/docs/how-to/security/openssh-server/), [OpenSSH authentication](https://man.openbsd.org/sshd_config) |
| Service reload, restart, and manager daemon reload have different effects | [systemctl manual](https://www.freedesktop.org/software/systemd/man/latest/systemctl.html), [official source](https://github.com/systemd/systemd/blob/main/man/systemctl.xml) |
| Inspect effective limits before changing them; MemoryHigh throttles and MemoryMax can cause OOM termination | [resource controls](https://www.freedesktop.org/software/systemd/man/latest/systemd.resource-control.html), [official source](https://github.com/systemd/systemd/blob/main/man/systemd.resource-control.xml) |
| Published Docker ports require checks beyond UFW status; preserve backend-specific Docker networking rules | [Docker firewalls](https://docs.docker.com/engine/network/packet-filtering-firewalls/) |
| Mounted secrets need application/image support; _FILE is an image convention | [Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/) |
| Startup order differs from readiness; health conditions need healthchecks | [Compose startup](https://docs.docker.com/compose/how-tos/startup-order/) |
| A named Compose service can be rebuilt and recreated without recreating dependencies | [Compose production](https://docs.docker.com/compose/how-tos/production/) |
| Validate proxy configuration, reload through the installed mechanism, then verify traffic | [NGINX test](https://nginx.org/en/docs/switches.html), [reload](https://nginx.org/en/docs/beginners_guide.html) |
| Active PostgreSQL file copies are insufficient without shutdown or a consistent complete snapshot | [filesystem backups](https://www.postgresql.org/docs/current/backup-file.html) |
| pg_dump is consistent per database, omits roles/tablespaces, and a restore must handle SQL errors | [SQL dumps](https://www.postgresql.org/docs/current/backup-dump.html) |

## Assumptions and design decisions

- Discover the actual distribution and installed versions. These sources support
  the examples, not a mandate to replace packages, firewalls, proxies, or tooling.
- Keep job workflows and the existing ops boundary. Use Linux for the host,
  Docker for containers, and server for release/configuration/recovery chains.
- Trace CI variables through deployment and host files to the consuming process;
  this is a workflow rule, not proof of any configured deployment.
- Require isolated restore drills and schema-aware rollback. An image rollback
  is insufficient when a migration removed compatibility; this is a recovery
  design constraint, not a guarantee of automatic rollback.
- Keep research outside installable skill directories. Use short descriptions
  and directly linked runtime references; leave installer and validator logic.

## Evidence limitations

The freedesktop rendered systemd pages returned tool errors; the official
systemd repository manuals supplied the corresponding source checks. Latest
manuals may contain features absent from a target host; inspect installed
manuals before choosing commands. PostgreSQL's current source resolved to 18
at retrieval; use the deployed version's backup tooling and procedures.

No SSH connection, firewall mutation, container deployment, proxy reload,
database backup, or restore ran on a live server. Evaluation-schema validation
establishes fixture validity, not agent behavior. Native paid evaluation needs
dedicated authenticated profiles and is separate from deterministic checks or
any read-only forward-test of these instructions. Global installation is outside
scope; packaging can be checked in an isolated temporary skill root.

## Implementation verification

- `python3 -m unittest discover -s tests -v`: 88 tests passed after updating
  the repository inventory assertion from 34 skills to 36.
- `python3 scripts/validate.py --stats`: 36 skills, 89 evaluation cases, and
  3,148 of 3,200 estimated metadata tokens; references and packaging valid.
- `python3 scripts/eval.py --check`: all 89 cases have valid schema and fixtures.
  Ten cases were added; this check did not execute them against an agent.
- `python3 -m py_compile scripts/*.py` and `git diff --check`: passed.
- Temporary-root install and `scripts/install.py --root TARGET --check`:
  36 destinations without drift, including the final SSH reference. New runtime
  references matched their sources; the research note was excluded.
- Skill Creator's format validator passed for Linux, server, and Docker using
  PyYAML in a temporary isolated cache; their Codex YAML also parsed correctly.
- A read-only agent forward-tested four scenarios and repeated the SSH scenario.
  Its feedback clarified staged port transitions and authentication policy;
  final text also requires proving the selected key without fallback. This
  was not native discovery, a graded harness run, or live server verification.

Installer and validator logic remained unchanged. No global installation or
live server action was performed.
