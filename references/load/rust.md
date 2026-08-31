# Rust

Read this when touching `.rs`. Core rules in `SKILL.md` still apply.

## Format

`cargo fmt` on touched files. Match the crate's error type (`thiserror`,
`anyhow`, `eyre`) instead of introducing a second one.

## Errors

`.unwrap()` / `.expect("…")` in non-test production code is a swallowed
failure with a crash on top. Use `?`, `map_err`, or handle. `expect` is
allowed when a violated invariant means a programmer bug, and the message
says which invariant.

`todo!()`, `unimplemented!()`, and `panic!("not implemented")` are not a
finished function. Do not ship them.

```rust
// slop
let user = users.get(id).unwrap();

// needquality
let user = users.get(id).ok_or(Error::NotFound { id })?;
```

## Types

Prefer an enum over boolean flags that encode states the other fields
make illegal. Prefer `String` vs `&str` as the existing API does.
Don't invent `utils.rs` or a subcrate for one function.

## Time and strings

`chrono`/`time`: instants are UTC; calendar dates are not
`DateTime<Utc>` at midnight. `str.len()` is bytes; iterate `chars()`
or use a grapheme crate when truncating user text. Normalize identifiers
before uniqueness checks.

## Shared state

Do not hold a `MutexGuard` across `.await`. Check-then-act on a row
without a unique constraint or `UPDATE … WHERE` is a race the borrow
checker will not catch.

Do not `.clone()` every `String` "to make it easier."
`.unwrap_or_default()` on a failed fetch is invented success. Money is
`rust_decimal` / integer cents, not `f64`. Outbound HTTP: a client
with a timeout; `error_for_status()` / `status().is_success()` before
`.json()`. Do not `Client::get(user_url)`. `cargo add` a recalled
name is slopsquatting — grep `Cargo.toml` / `Cargo.lock`. Logged-in
`id` from the path still needs an owner check.
`for row in rows { query(row.id) }` is N+1 — JOIN / `WHERE id = ANY($1)`.
Don't `tokio::spawn` an unbounded user-sized list. CSRF / JWT /
webhooks: [trust.md](trust.md) when this patch does HTTP.

Never `format!("SELECT … {}", id)` — `$1` / `?`. A struct field is
not a migration. Escaped templates are safe; `PreEscaped` of user
input is XSS. Don't deserialize a request into the same struct you
write to the DB.

## Leftovers

No `dbg!` / `println!` in library code. No unused imports (`cargo check`
will tell you; do not leave `#[allow(dead_code)]` to quiet a stub).
A used name is in scope. Don't wrap a boolean. Else after `return`
is noise. Bind a repeated expression only when one evaluation preserves
mutation, timing, errors, and observed state; leave intentionally repeated or
stateful calls alone.
`todo!()` / `unimplemented!()` is not the function. No
hardcoded secrets. Never `.danger_accept_invalid_certs(true)` on a
`reqwest::Client`. Never `base.join(user_filename)` into `File::open`
/ `ServeDir`.
