# SQL / schema

Read this when touching `.sql`, Prisma/Drizzle/SQLAlchemy schema,
or a migration. HTTP, auth, or money in the same patch: the
`needquality-trust` skill. Grep the live schema (or `schema.prisma` / `models.py`)
before writing SQL — do not guess table or column names.

## Writes need a key

`UPDATE` / `DELETE` without `WHERE` is a full-table mutation. So is
`WHERE` that cannot be a key (`WHERE true`, a date with no tenant,
email with no unique). Check how many rows the same `WHERE` would
select before you run it. Wrap a write in a transaction if the
session isn't already in one.

```sql
-- slop — every user
UPDATE users SET email = 'ada@example.com';

-- needquality
UPDATE users SET email = 'ada@example.com' WHERE id = $1;
```

Don't run agent SQL against production. Don't `DROP TABLE` /
`TRUNCATE` / `migrate reset` / `prisma db push` on a shared DB
unless that *is* the task. Details: the `needquality-trust` skill,
section "Irreversible".

User text is not a SQL **identifier**. `ORDER BY ${sort}` /
`SELECT ${col}` is injection even when values are bound. Allowlist
column names, or a static map.

## Reads

`SELECT *` into an API/client payload is slop — name the columns the
caller needs. A query with no `LIMIT`/`FETCH` on a table that can
grow is unbounded. `OFFSET` for page 1 is fine; don't make deep
`OFFSET` the only paging on a growing table.

```sql
-- slop — comma join, no ON, cartesian
SELECT o.*, p.* FROM orders o, products p
WHERE o.created_at > '2026-01-01';

-- needquality
SELECT o.id, o.total, p.name
FROM orders o
JOIN products p ON p.id = o.product_id
WHERE o.created_at > '2026-01-01'
ORDER BY o.id
LIMIT 50;
```

Don't mix dialects (`LIMIT` vs `TOP` vs `FETCH`) — match this file's
engine. Phone/id stored as text compared to a number (`WHERE phone =
5551234567`) skips the index. `GROUP BY customer_id` plus extra
non-aggregated columns is not "latest row" — `DISTINCT ON` / window /
`ORDER BY … LIMIT 1` per group.

## Schema and indexes

A new field needs a migration. Don't rename / change type / tighten
nullability in one step while old code still runs: add the new
column (nullable or default) → backfill → switch reads/writes → drop
the old column in a later change. `NOT NULL` / unique / drop on
existing rows needs a backfill or default in the same change, or
don't. Don't drop a column the running code still reads. A new FK
gets an index if the tree already indexes FKs.

AI tables with no indexes on the columns you just filtered/joined are
the usual leftover — add the index the query uses, or say you didn't.
Don't invent an index religion. Unique email/username is a constraint,
not only `findByEmail` then insert.

Never `fmt.Sprintf("SELECT … %s", id)` / f-string SQL — `$1` / `%s`
bound. Don't concatenate user text into `LIKE` (`%`/`_`). Mongo: do
not pass the request body as the query object.

A struct tag / Zod field / Pydantic attribute is not a migration.
Don't migrate on boot or in the container entrypoint.
