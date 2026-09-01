# Lua

Read this when touching `.lua` / `.rockspec`. Core rules in `SKILL.md`
still apply. Match the runtime: Lua 5.1/LuaJIT (Neovim, OpenResty,
games) and 5.3+/5.4 differ (integers, `goto`, `#` semantics,
`table.unpack` vs `unpack`) — grep the repo before using a version
feature.

## Scope

`local` everything. An assignment without `local` is a global — the
classic Lua bug and the classic slop tell. Localize repeated
module/table lookups only where the file already does (hot loops);
match the file otherwise.

```lua
-- slop: leaks a global, typo silently creates another
function process(items)
  results = {}
  for i = 1, #items do results[i] = transform(items[i]) end
  return reslts
end

-- needquality
local function process(items)
  local results = {}
  for i = 1, #items do results[i] = transform(items[i]) end
  return results
end
```

## Errors and nil

Fallible calls return `nil, err` or are wrapped in `pcall` — check
both. Ignoring the second return of `pcall` (or the `err` of
`nil, err`) is a swallowed failure; `or {}` / `or ""` on a failed call
is invented success. Match the file's convention (`nil, err` vs
`error()`) — do not introduce the other. `error()` with a message
beats a naked `nil` when the caller cannot proceed.

Indexing a possibly-`nil` table chain (`a.b.c.d`) crashes; check the
required link or fail with a named error, don't scatter `and`/`or`
guards that hide the missing data.

## Tables and strings

Arrays are 1-based, and `#t` is undefined with nil holes — do not
`t[#t + 1] = nil`-style build sparse arrays; use `table.insert` or a
running count like the file does. Building a string in a loop with
`..` is quadratic — collect into a table and `table.concat`.
`string.len` is bytes; UTF-8 user text needs the repo's utf8 helpers
for truncation. `pairs` order is undefined — sort keys when output
order matters.

## Trust and I/O

Never `load` / `loadstring` / `dofile` on user input — it is code
execution. User input never reaches `os.execute` / `io.popen` as a
concatenated string — avoid the shell or escape strictly with an
allowlist. Paths from users are validated before `io.open`. SQL and
HTTP through the host's bindings keep bound parameters, timeouts, and
status checks before treating a body as success. HTTP / auth / money:
[trust.md](trust.md).

## Leftovers

No `print` debug lines in library code — the host's logger
(`vim.notify`, `ngx.log`, the game's log). No unused locals or
commented-out blocks. Don't wrap a boolean (`return cond`), and no
`if cond then return true else return false end`. Bind a repeated
expression only when one evaluation preserves mutation, timing,
errors, and observed state.
