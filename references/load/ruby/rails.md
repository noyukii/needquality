# Rails

Read this when the patch touches Rails models, controllers, jobs, or
migrations. [ruby.md](../ruby.md) still applies. Do not glob `ruby/`.

## Controllers

Strong parameters, always — `params.require(:post).permit(:title,
:body)`, never `params[:post]` wholesale into `create`/`update`.
Scope by the current user; `before_action :authenticate_user!` is not
ownership:

```ruby
# slop
@post = Post.find(params[:id])

# needquality
@post = current_user.posts.find(params[:id])
```

Match the sibling controller's response shape and status codes. Slow
work (mail, exports, webhooks) goes through the installed ActiveJob
adapter, not inline in the request.

## Models and queries

A view or loop touching `record.association` is N+1 — `includes` /
`preload` / `eager_load`. Queries that can grow take `.limit`.
Uniqueness is a DB unique index plus the rescued
`ActiveRecord::RecordNotUnique` — `validates_uniqueness_of` alone is a
race. Conditional state changes are one query
(`where(...).update_all(...)` or optimistic locking), not
read-check-save. Multi-write operations wrap in a transaction. No new
callbacks for one caller — call the method; a callback chain that does
I/O is where the next bug lives.

## Migrations

A model change ships its migration. Expand-contract: do not drop or
rename a column the running code still reads; add, backfill, switch,
then remove in a later deploy. Data backfills that can be large are
batched (`in_batches`), not one `update_all` holding a lock. Match the
repo's `strong_migrations`-style constraints when installed.

## Views and config

Templates escape by default — no `html_safe` / `raw` on user text.
CSRF protection stays on. Secrets live in credentials / ENV, never
committed YAML. Turbo/Hotwire vs API-only, form builders, and
serializer conventions: match the sibling, not a new pattern. Auth,
uploads, webhooks: [trust.md](../trust.md). Raw SQL:
[sql.md](../sql.md).
