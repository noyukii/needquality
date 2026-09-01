# Laravel

Read this when the patch touches Laravel controllers, Eloquent models,
jobs, or migrations. [php.md](../php.md) still applies. Do not glob
`php/`.

## Controllers and input

Validate with a FormRequest (or `$request->validate`) and use
`validated()` — never `$request->all()` into `create`/`update`; that
is mass assignment even with `$fillable`. Authorization goes through
the existing policies/gates, and route model binding still needs an
owner scope:

```php
// slop
$post = Post::findOrFail($id);

// needquality
$post = $request->user()->posts()->findOrFail($id);
```

Match the sibling controller's response shape and status codes. Slow
work (mail, exports, webhooks) is a queued job on the configured
queue, not inline in the request.

## Eloquent and data

A loop touching `$model->relation` is N+1 — `with()` / `load()` or one
query. Queries that can grow take `limit`. Uniqueness is a DB unique
index plus the caught `QueryException` — the `unique:` validation rule
alone is a race. Conditional state changes are one query
(`where(...)->update(...)`), not read-check-save. Multi-write
operations wrap in `DB::transaction`. A model change ships its
migration; do not drop or rename a column running code still reads —
expand-contract.

## Views and config

Blade `{{ }}` escapes; `{!! !!}` on user text is XSS — reserve it for
trusted, already-sanitized HTML. CSRF middleware stays on. `env()`
outside `config/` returns null under config caching — read config,
put the `env()` call in a config file. Secrets stay in `.env` /
the deploy secret store, never committed. Match the repo's existing
conventions (API resources vs raw models, Inertia vs Blade) instead of
introducing a second pattern. Auth, uploads, webhooks, outbound HTTP:
[trust.md](../trust.md). Raw SQL: [sql.md](../sql.md).
