# Go

Read this when touching `.go`. Core rules in `SKILL.md` still apply.

## Format

`gofmt` (or `goimports`) is not optional. Run it on touched files. Match
the package's error-wrapping style (`fmt.Errorf("…: %w", err)` vs
`errors.Join`).

## Errors

Return `error`. Do not `panic` in library code unless the invariant is
truly "this process is corrupt." Callers at the boundary (`main`, HTTP
middleware) decide to log, exit, or map to a status.

Empty `if err != nil {}` and `_ = err` are swallowed exceptions. Handle
or return.

```go
// slop
data, _ := json.Marshal(v)

// needquality
data, err := json.Marshal(v)
if err != nil {
    return fmt.Errorf("marshal user: %w", err)
}
```

Do not wrap every line in a new error type. Wrap at the boundary where
the extra context is something a caller can use.

## Structure

Keep `package` scope small. Do not invent `IUserRepository` with one
`UserRepository` — a function or a concrete struct is enough until a
second implementation exists.

Don't invent `cmd/`, `internal/`, `pkg/`, or `util.go` on a
one-package module. Files in the same directory until a second
importable surface exists. `golang-standards/project-layout` is not
the Go team; [go.dev/doc/modules/layout](https://go.dev/doc/modules/layout)
is. Name the file after the thing (`invoice.go`, not `helpers.go`).
A little copying beats a new module for ten lines.

## Time and strings

`time.Now()` is an instant with a location. Store UTC
(`t.UTC()`); parse with an explicit location, not the machine's.
Range over a `string` for runes; `len(s)` is bytes. Compare
user-facing identifiers in NFC if uniqueness matters.

## Shared state

```go
// slop
if !slot.Reserved {
    slot.Reserved = true
    db.Save(&slot)
}
```

Use a single conditional update or a unique constraint. Do not copy
the check-then-act into a goroutine and hope.

```go
// needquality
res, err := db.ExecContext(ctx,
    `UPDATE slots SET reserved = true WHERE id = $1 AND reserved = false`, id)
if err != nil {
    return err
}
n, err := res.RowsAffected()
if n == 0 {
    return ErrConflict
}
```

## I/O

Request-scoped work takes a `context.Context` with a deadline from
the handler — not `context.Background()`. `http.Get` / `sql.Query`
without a context or `Timeout` hang. `defer resp.Body.Close()` /
`defer rows.Close()`; check `rows.Err()`. Check `status/100 == 2` before
decoding — not only `http.StatusOK` (201/204 are success). `go func()`
from a handler without a bound or wait is a leak. A send with no
receiver, or a receive on a channel nobody closes, is the same leak —
`select` on `ctx.Done()`, buffer, or close. Don't write a `map` from
two goroutines without a mutex. One `sql.DB` for the
process (`SetMaxOpenConns`); don't `sql.Open` per request. Money:
`int64` cents or `shopspring/decimal`, not `float64`. CSRF / JWT /
webhooks: the `needquality-trust` skill when this patch does HTTP.

A slice from the DB with no `LIMIT` is unbounded. Related rows:
join or one `IN` query, not `for _, id := range ids { db.Get(id) }`.
Logged-in `r.URL.Query().Get("id")` still needs an owner check.

Do not `http.Get(r.URL.Query().Get("url"))`. `html/template` is the
default; `template.HTML(userInput)` is XSS. `json.Unmarshal` into a
struct with explicit fields, not `map[string]any` dumped into an
update. Never `fmt.Sprintf("SELECT … %s", id)` — `$1`. A struct tag
is not a migration. User argv to `exec.CommandContext`; never
`sh -c` concatenated.

## Leftovers

No `fmt.Println` / `log.Println` debug in library packages. No unused
imports (the compiler will stop you — do not "comment them out for
later"). A used name is imported. Don't wrap a boolean
(`return cond`, not `if cond { return true }`). Else after
`return` is noise. Bind a repeated expression only when one evaluation
preserves mutation, timing, exceptions, and observed state; leave intentionally
repeated or stateful calls alone.
No API keys in source. Never `tls.Config{InsecureSkipVerify: true}` to
silence a cert. Never `filepath.Join(uploadDir, r.FormValue("name"))`
into `os.Open` / `http.ServeFile` / `http.Dir`.
