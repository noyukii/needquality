# Postgres

Read this when the tree is Postgres, Supabase, or Neon, after
[sql.md](sql.md). HTTP, auth, or money in the same patch: the
`needquality-trust` skill. Grep the live schema first.

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

An applicable policy normally constrains rows. `USING (true)` /
`WITH CHECK (true)` intentionally grants broad access for the policy's
commands and roles; it is not the same as having no applicable policy.
With RLS enabled, no applicable policy means default-deny. Table owners
normally bypass RLS unless `FORCE ROW LEVEL SECURITY` applies, and roles
with `BYPASSRLS` bypass it. Tenant and owner come from `auth.uid()` or
the session — not a client-supplied id. See the `needquality-trust` skill,
section "Row-level security (Postgres)".

## Locks

Book, claim, reserve, unique email: `SELECT … FOR UPDATE`, a
unique constraint, or an idempotency row. Sequential
statements are not atomic. Name the lock or say you did not.
