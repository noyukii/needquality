# Elixir

Read this when touching `.ex` / `.exs` / `mix.exs`. Core rules in
`SKILL.md` still apply. Phoenix app code (contexts, controllers,
LiveView): [phoenix.md](elixir/phoenix.md).

## Format

`mix format` on touched files. Match the file's pipeline style —
don't rewrite a `|>` chain into nested calls or vice versa. Fix what
`mix compile --warnings-as-errors` / credo report on your lines when
the repo uses them.

## Tagged tuples

Handle both arms. Matching only `{:ok, result}` crashes with a
`MatchError` that names nothing; `elem(result, 1)` treats an error
tuple as data.

```elixir
# slop
{:ok, user} = fetch_user(id)

# needquality
case fetch_user(id) do
  {:ok, user} -> render_user(user)
  {:error, :not_found} -> {:error, :not_found}
end
```

Chain happy paths with `with`, and give the `else` clauses names. "Let
it crash" applies to supervised processes with restart semantics — at
a request boundary, return a tagged error the caller renders. A
`rescue` that catches everything to return a default is a swallowed
failure.

## Structure and processes

Put the function in the module that owns the data; no `Util` /
`Helpers` module for one function. Don't reach for a GenServer to
hold state a database row or an ETS table already holds — a process
is a concurrency unit, not a class. `spawn` without a link or
supervisor is a process whose crash nobody sees — use `Task.async` /
`Task.Supervisor` and await, or the existing supervision tree. Don't
start an unbounded task per element of a user-sized list —
`Task.async_stream` with concurrency and timeout.

## Atoms and strings

Never `String.to_atom` on user input — atoms are not garbage
collected; use `String.to_existing_atom` or keep strings. External
params are string-keyed maps — pattern match string keys, don't
convert the map. Normalize identifiers before uniqueness checks.

## Time, money, data

`DateTime.utc_now/0` for instants; wall clock takes an explicit time
zone with the repo's tzdata. Money is `Decimal`, never floats. Ecto
queries use bindings and `^` pins — never string-interpolated
fragments with user input. Check-then-act (`Repo.get` then insert) is
a race — a unique constraint plus changeset error, or `Ecto.Multi` /
`Repo.transaction` for multi-step writes. A query per list element is
N+1 — `preload` or one query. A query that can grow takes `limit`.
A logged-in user's id param still needs an owner scope. HTTP / auth /
money: [trust.md](trust.md).

## Leftovers

No `IO.inspect` / `dbg()` left in production paths. No unused aliases
or imports. Do not ship a function head that returns a hardcoded
sample as done. Don't wrap a boolean (`cond?` functions return the
expression); else-like nesting after an early return pattern is noise.
No hardcoded secrets — runtime config (`config/runtime.exs`, env).
