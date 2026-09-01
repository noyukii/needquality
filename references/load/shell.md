# Shell

Read this when touching `.sh` / `.bash` / a file whose shebang is a
shell. Core rules in `SKILL.md` still apply.

## Match the dialect

The shebang is the contract: `#!/bin/sh` is POSIX — no arrays,
`[[ ]]`, or `local` beyond what the repo already uses; `#!/usr/bin/env
bash` may use bashisms. Match the file's existing style: `$(...)` vs
backticks, `[[ ]]` vs `[ ]`, function syntax. Run `shellcheck` on
touched files when the repo has it, and fix what it reports on your
lines.

## Quoting and expansion

Quote every expansion unless the file deliberately splits:
`"$var"`, `"$@"`, `"$(cmd)"`. An unquoted variable in `rm`, `mv`,
`cp`, or a test is the classic destructive bug.

```bash
# slop — empty $dir deletes from /
rm -rf $dir/build

# needquality
rm -rf "${dir:?dir is unset}/build"
```

Do not parse `ls` — glob or `find -print0 | while read -d ''`.
Filenames contain spaces and newlines; loops over command output use
null delimiters or globs.

## Failure

Decide what failure does. `set -euo pipefail` where the repo uses it;
otherwise check the commands that matter (`cd dir || exit 1` — an
unchecked `cd` runs the rest of the script in the wrong directory).
`cmd || true` is a swallowed failure unless the comment says why the
failure is acceptable. A pipeline's exit status is the last command's
unless `pipefail` — do not claim success off `grep | head`.

## Temp files and cleanup

`mktemp` / `mktemp -d`, never a predictable `/tmp/name`. Register
cleanup once: `trap 'rm -rf "$tmp"' EXIT`. Do not leave partial output
on failure — write to a temp file and `mv` into place.

## Trust

User or network input never reaches `eval`, an unquoted command
position, or an interpolated SQL/curl string. Building a command from
variables: arrays (`args=(-x "$val"); cmd "${args[@]}"`), not string
concatenation. Secrets do not go on command lines visible in `ps` or
into the script — environment or a secrets file the repo already
uses. `curl | sh` of an unpinned URL is an installation you cannot
review — download, checksum, then run, or match the repo's existing
installer. HTTP / auth / money: [trust.md](trust.md).

## Leftovers

No `set -x` left on. No commented-out blocks or `echo` debug lines in
the final script. Portable `echo` is a trap for flags/escapes —
`printf '%s\n'` when it matters. Exit codes are the API: `exit 0`
only on success; a `main`-style script ends with an explicit status
when the repo's scripts do.
