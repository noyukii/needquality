# Postgres

Read this when the tree is Postgres, Supabase, or Neon. Also
[sql.md](sql.md) and [trust.md](trust.md). Core rules in
`SKILL.md` still apply. Grep the live schema first.

## Pool

One shared pool (or the framework's pool). Not a new connection
per request, not `Client.connect()` in a handler without
`release`. Serverless: the existing pooler / `pg` pool the repo
already uses. Don't add a second pooler.

## Explain before "faster"

A "faster query" claim needs `EXPLAIN (ANALYZE)` this turn, or
say you did not. Index the columns you just filtered or joined,
or say you didn't. Don't invent an index religion.

## RLS

A policy must constrain. `USING (true)` / `WITH CHECK (true)`
is open. Tenant and owner come from `auth.uid()` or the
session — not a client-supplied id. trust.md already flags
open RLS; this file is the Postgres tell.

## Locks

Book, claim, reserve, unique email: `SELECT … FOR UPDATE`, a
unique constraint, or an idempotency row. Sequential
statements are not atomic. Name the lock or say you did not.
