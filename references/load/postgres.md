# Postgres

Read this when the tree is Postgres, Supabase, or Neon. Also
[sql.md](sql.md) and [trust.md](trust.md). Core rules in
`SKILL.md` still apply. Grep the live schema first.

## Pool

One shared pool (or the framework's pool). Not a new connection
per request, not `Client.connect()` in a handler without
`release`. Serverless: the existing pooler / `pg` pool the repo
already uses. Don't add a second pooler.

## Types

Timestamps are `timestamptz` — a naive `timestamp` column silently
reinterprets across zones; match the existing columns either way.
Money is `numeric` / integer cents, never `real` / `double
precision`. `text` over `varchar(n)` unless the repo's convention
differs — a length cap is a check constraint, not a religion. JSONB
holds genuinely schemaless payloads; a field every query filters on
is a column, not a JSONB path.

## Explain before "faster"

A "faster query" claim needs `EXPLAIN (ANALYZE)` this turn, or
say you did not. Index the columns you just filtered or joined,
or say you didn't. Don't invent an index religion. A partial or
expression index matches the query it serves
(`WHERE deleted_at IS NULL`, `lower(email)`) — an index the planner
cannot use is write cost with no read win. `LIKE '%term%'` does not
use a btree; that is trigram/FTS territory the repo may already have.

## Writes

Upsert is `INSERT … ON CONFLICT` — not `SELECT` then branch.
Conditional state changes are one statement
(`UPDATE … WHERE state = 'pending'` and check the row count).
Batch related writes in one transaction; keep transactions short —
no network calls inside. A migration that rewrites or locks a big
table (`ALTER … SET NOT NULL`, adding an index) uses the safe form
the repo's tooling supports (`CONCURRENTLY`, validated constraints)
— and expand-contract for columns running code still reads.

## RLS

An applicable policy normally constrains rows. `USING (true)` /
`WITH CHECK (true)` intentionally grants broad access for the policy's
commands and roles; it is not the same as having no applicable policy.
With RLS enabled, no applicable policy means default-deny. Table owners
normally bypass RLS unless `FORCE ROW LEVEL SECURITY` applies, and roles
with `BYPASSRLS` bypass it. Tenant and owner come from `auth.uid()` or
the session — not a client-supplied id. See [trust.md](trust.md#row-level-security-postgres).

## Locks

Book, claim, reserve, unique email: `SELECT … FOR UPDATE`, a
unique constraint, or an idempotency row. Sequential
statements are not atomic. Name the lock or say you did not.
Queue-style polling uses `FOR UPDATE SKIP LOCKED` if the repo already
polls. An advisory lock is for cross-statement coordination the
schema cannot express — and it needs the same named release
discipline as any lock.
