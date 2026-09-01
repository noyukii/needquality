# Phoenix

Read this when the patch touches Phoenix controllers, contexts,
channels, or LiveView. [elixir.md](../elixir.md) still applies. Do not
glob `elixir/`.

## Contexts

Business logic lives in the context module, not the controller or
LiveView — add the function to the existing context that owns the
data; do not invent a new context for one function. Controllers and
LiveViews call context functions and render the tagged result — a
`Repo` call in a controller next to context-using siblings is drift.

## Changesets and input

`cast/3` with an explicit allowlist of fields — params are
string-keyed user input, never trusted wholesale, never atomized.
Ownership is a query scope, not an `if` after the fetch:

```elixir
# slop
post = Repo.get!(Post, id)

# needquality
post = Repo.get_by!(Post, id: id, user_id: socket.assigns.current_user.id)
```

Uniqueness is a DB unique index plus `unique_constraint/3` on the
changeset — an existence check first is a race. Multi-step writes use
`Ecto.Multi` in one transaction.

## LiveView

`mount/3` assigns everything the render needs; auth comes from the
existing `on_mount` / plug pipeline, not ad-hoc session digging.
`handle_event` pattern matches the event name and validates params
like a controller would — the socket is a user boundary. Large or
growing collections use `stream/3` (or temporary assigns), not a full
list re-assigned every update. Slow work moves to a `Task` /
Oban-style job the repo already uses, with a `handle_info` that
updates assigns — do not block the LiveView process.

## Config and boundaries

Runtime secrets belong in `config/runtime.exs` / env, never compiled
into releases via `config.exs`. New routes go through the existing
pipelines (`:browser`, `:api`, auth plugs) — a route outside the auth
pipeline is a hole, not a shortcut. Webhooks, uploads, outbound HTTP:
[trust.md](../trust.md). Raw SQL: [sql.md](../sql.md).
