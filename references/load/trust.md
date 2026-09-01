# Trust boundaries

Read this when the patch touches HTTP, auth, DB, money, uploads,
webhooks, or outbound I/O. Core rules in `SKILL.md` still apply.

The happy path compiles. These fail in production, under a second
user, or in the browser.

## Authn is not authz

Scope every query to this session's user or org. Bare
`findUnique({ where: { id } })` is IDOR. Logged-in ≠ admin; UI hide ≠
server check. Client headers (`X-User-Id`, `X-Forwarded-For`) are not
identity. Don't rate-limit on client headers.

**Owner fields come from the session.** `userId` / `orgId` / `role` /
`isAdmin` on writes come from the session, never from the body. An
allowlisted `orgId` in JSON is still the client picking a tenant.

**One auth model per route:** cookie session (including JSON `fetch`
with credentials) → CSRF token or strict Origin on
POST/PUT/PATCH/DELETE and any GET that mutates. Skip CSRF only if
cookies cannot authenticate — not because the body is JSON. Origin
must exact-match and reject missing. SameSite is extra, not instead.
Node `jwt.decode` / `jose.decodeJwt` / `JSON.parse(atob(payload))`
never verify — `jwt.verify` / `jwtVerify` with an algorithm allowlist.
Never `algorithms: ['none']` / `verify_signature=False`. PyJWT
`decode(token, key, algorithms=…)` is verify. A `'use server'` file
exports public POSTs: parse and authz inside each; a page-level check
does not cover them.

A new POST copies the nearest sibling's `requireAuth` / `auth()`,
parse, timeout, and error shape — not a lone owner check later.
Next.js `matcher` only routes traffic. Copy the sibling's check
inside the handler.

Authorization must protect the operation that uses the value. A
detached check followed by a later read/write is a TOCTOU race; keep
the predicate in the same transaction or conditional statement. UUIDs,
hidden fields, and client-side guards are identifiers or UX, not
authorization.

GraphQL needs authz at each resolver or field that exposes data, not
only at the endpoint. Public queries also need the repo's depth,
complexity, or cost limit when that boundary exists. CSP is defense in
depth; it does not replace output encoding, safe sinks, or authz.

A new auth or route is not mounted because it compiles. Hit the tree's
documented local probe (`/health`, `/api/auth/ok`, or the route's safe
fixture) and parse the response. If no probe exists, say so.

## Lists and fan-out

No `LIMIT`/`take`, or a cap the client can raise without bound, is a
load bomb. Default a page size; hard-cap (`min(n, 100)`).
`Promise.all(items.map(fetchRelated))` is still N+1. JOIN, `include`,
or `WHERE id IN (...)`.

Don't `Promise.all` / `asyncio.gather` / `go func()` an unbounded
user-sized list of I/O (`body.ids.map(charge)`). Cap, queue, or chunk.
`OFFSET` for a small page 1 is fine. Don't make deep `OFFSET` the only
pagination on a table that can grow — keyset (`WHERE id < $cursor`) if
you already have an ordered unique column.

## Outbound I/O

`requests.get` / `fetch` / `http.Get` with no timeout hang the worker.
Pass `timeout`, `AbortSignal`, or a context deadline.

**HTTP success is 2xx (200–299).** `fetch` only throws on network error.
Check `res.ok` / `raise_for_status()` / `status/100 == 2` before treating a
parsed body as success. Parse a structured error body only to construct the
failure. `StatusOK` is 200 only — 201/204 are success. A 5xx body is not
successful data.

Retry of create/charge/order needs an **idempotency key you persist**
(or a unique constraint). Minting `crypto.randomUUID()` per attempt,
or accepting `Idempotency-Key` and ignoring it, is a comment. Don't
mint a new UUID on retry.

Cert errors: fix the CA. Never `verify=False` / `InsecureSkipVerify` /
`NODE_TLS_REJECT_UNAUTHORIZED=0`.

## Don't fetch a user URL

`fetch(req.body.url)`, image proxy, "scrape this", webhook callback
URL: SSRF. Allowlist hosts (not a one-shot IP check: redirects bypass
it). `hostname.includes('paypal.com')` is not an allowlist
(`not-paypal.com`). Cloud metadata (`169.254.169.254`,
`metadata.google.internal`) is not a host you fetch. Open redirect:
don't send the browser to a user-supplied `next=` without an
allowlist. `next.startsWith('/')` is not enough (`//evil`, `/\evil`).

## Don't render user HTML

React text nodes are safe. `dangerouslySetInnerHTML`, `innerHTML`,
Vue `v-html`, Svelte `{@html}`, unsanitized markdown, SVG uploads,
and `javascript:` hrefs are XSS.
Sanitize with the project's library, or don't render HTML.

## Don't spread the body into an update

`{...req.body}` / `queryset.update(**request.POST)` is mass assignment.
Allowlist fields. JS: `JSON.parse` of `__proto__` is an own key;
`Object.assign` / lodash `merge` of that payload pollutes
`Object.prototype`. Allowlist keys; don't recursive-merge body/query
into config. Mongo: do not pass the request as the query (`$gt`).
Parameterize SQL; never `` `... '${q}'` ``. Don't concatenate user
text into `LIKE` — escape `%`/`_` or reject them. User text is not a
SQL identifier (`ORDER BY ${sort}`) — allowlist column names. A leading `%` on a
big table is a seq scan; prefix match, or the project's search helper.

## Don't eval untrusted data

`eval` / `new Function` / `pickle.loads` / `yaml.load` (use
`safe_load`) / `subprocess(..., shell=True)` with user input. JSON, or
a list argv with no shell. User text is template *data*, never the
template source (`jinja.from_string(user)`). Do not invent nested
`+`/`*` validators. Use a parser.

## Schema matches the code

A new field without a migration is a production break. Don't drop a
column the running code still reads. Don't rename / change type /
tighten nullability in one step while old code still runs — add
nullable → backfill → switch → drop later. `NOT NULL` / unique / drop on
existing rows needs a backfill or default in the same change, or don't.
`process.env.NEW_FLAG` when the key isn't in `.env.example` is the
same tell. Declare it in the same change, or don't. A new flag is off
when unset (`?? true` is fail-open). The `.env.example` default is
`false`.

No `localhost`, `DEBUG=True`, debug toolbar, or seed credentials as
production defaults. Don't migrate in process boot / the container
entrypoint. A new FK / `@relation` gets an index if the tree already
indexes FKs. Don't invent an index religion. `UPDATE` / `DELETE`
without a key in `WHERE` is a full-table write — [sql.md](sql.md).
Grep the schema before writing SQL; do not guess column names.

## Webhooks, money, CORS, errors, logs

Webhooks are public POST. Read the raw body in the provider-required form,
verify the signature and basic envelope, then deduplicate and durably store or
enqueue the event. Return success only after durable acceptance. Process slow
business work asynchronously and idempotently by event id.
Provider references: [Stripe webhooks](https://docs.stripe.com/webhooks) and
[GitHub webhook best practices](https://docs.github.com/en/webhooks/using-webhooks/best-practices-for-using-webhooks).

Money is not `float`. Decimal or integer cents. Prefer a decimal
string on the wire. JS `number` reintroduces binary float.

CORS is an allowlist. `cors()` / `Origin: *` plus cookies or
`Authorization` is a credential leak. Fine for public read-only.

Errors stay on this side. No stack traces, SQL, or paths in the JSON.
`200` + `{ error }` is not an error. `/health` that always 200 while
the DB is down is a lie. 503 when deps fail. Login/signup without a
rate limit is brute-force-open. Don't glue email/SMS headers from
user strings (`"Subject: "+u`).

Logs are not a dump. No tokens, passwords, cookies, full bodies, card
numbers, or emails. Never interpolate a raw user string
(`log.info(f"login {u}")`). Newlines forge log lines.

## Cleanup matches setup

`setInterval` / listeners / files / DB connections get `clear` /
`abort` / `close`. SSE / WebSocket / `ReadableStream`: abort on unmount
and on the request `AbortSignal`. Uploads and downloads: size, type,
and a name *you* generated. Never `join(dir, userFilename)` (including
`../`). Archive extract only into a directory you created. Cache: a
TTL; user-specific data is not a global key. Don't read `cookies()` /
`headers()` inside `cache()` / `unstable_cache` / `'use cache'`.

`NEXT_PUBLIC_` / `VITE_` / `REACT_APP_` / `EXPO_PUBLIC_` is public. Service-role,
Stripe, and OpenAI keys stay on the server. Don't pass them (or the
session) into a Client Component.

### Row-level security (Postgres)

With PostgreSQL RLS enabled, no applicable
policy is default-deny. `USING (true)` intentionally permits every row covered
by that policy. Table owners and roles with `BYPASSRLS` normally bypass RLS;
use `FORCE ROW LEVEL SECURITY` when the owner must be subject to policies.
See [PostgreSQL row security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html).
Don't `force-cache` / statically shell data that varies on
`cookies` / `Authorization`. `next/image` `src` of a user URL is
SSRF — allowlist hosts. Passwords: argon2/scrypt/bcrypt + timing-safe
compare, not SHA-256/`==`. Don't use `Host` / `x-forwarded-host` for
reset links or cache keys.

## Irreversible commands

Don't run, generate, or "just try":

- `rm -rf`, `rmdir /s /q`, `DROP TABLE` / `DROP DATABASE`,
  `migrate reset`, `prisma migrate reset`, `prisma db push` /
  `prisma db push --force` on a shared or live DB
- `--shadow-database-url` aimed at anything but a disposable local DB
- force-push, history rewrite, `chmod -R`, infrastructure teardown
- a cleanup glob that includes `~/`, `/`, `C:\`, or `D:\`

Quote paths that contain spaces. Production database URLs stay out of
the session. Acknowledging "DO NOT RUN / don't delete" in prose and
then executing it is the same failure as ignoring it. A destructive command
that failed is not a prompt to broaden the path. Recheck the exact target and
authorization before choosing a different diagnostic.
