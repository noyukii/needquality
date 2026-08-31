# Migrate

Read this when they said migrate, write a migration, or migrate
the schema. One schema change. Also [sql.md](../load/sql.md) and
[trust.md](../load/trust.md). Postgres / Supabase / Neon →
[postgres.md](../load/postgres.md). Cross-product "migrate the
app off X" stays research + tickets, not this row.

1. Grep the live schema first. Do not guess names.
2. Expand-contract: add (nullable or default) → backfill → switch
   reads/writes → drop later. Name the lock or rollback.
3. Don't `DROP` / `TRUNCATE` / `prisma db push` / `migrate reset`
   on a shared DB unless that *is* the task.

Don't: app rewrite, a second table, invent columns.
