# C / C++

Read this when touching `.c` / `.h` / `.cc` / `.cpp` / `.hpp` /
`.cxx`. Core rules in `SKILL.md` still apply.

## Format

Run `clang-format` only when the repo has a `.clang-format`. Match the
file: naming, brace style, C standard or C++ standard from the build
files — do not use a newer standard's feature than the target. Match
the repo's error convention (return codes + `errno`, status types,
exceptions, `std::expected`) — do not introduce a second one.

## Ownership and lifetime

Match the file's ownership style. In C++ code that uses smart
pointers, a naked `new` / `delete` is slop — `std::unique_ptr` /
`make_unique`; `shared_ptr` only when ownership is genuinely shared.
Every resource has one owner and a release on every path — RAII in
C++, a single `goto cleanup` or mirrored `free` in C. Use after free,
double free, and returning a pointer/reference to a local are the
bugs to re-read for.

```cpp
// slop
const std::string& name() { std::string s = build(); return s; }

// needquality
std::string name() { return build(); }
```

## Bounds and integers

Every buffer write has a bound: `snprintf`, not `sprintf`; explicit
length checks before `memcpy`. In C++, prefer `std::string`,
`std::vector`, `std::span`, and `.at()` when the index comes from
outside. Size math on untrusted input checks overflow *before*
allocating (`n * sizeof(T)` can wrap). Signed/unsigned comparisons on
user-derived sizes are bugs. Casts are explicit and named
(`static_cast`), not C casts that silence the compiler.

## Errors

Check the return of everything that can fail: `malloc`, `fopen`,
`read`/`write` (short counts), `snprintf` truncation. Do not ignore a
status the file's convention checks elsewhere. In C++, catch by
`const&`, and only the exceptions you can handle — an empty `catch (...)`
is a swallowed failure. Initialize variables before use; an
uninitialized read is undefined behavior, not a zero.

## Shared state

Data raced between threads needs a mutex, an atomic, or a redesign —
"it's just a flag" is still UB. Do not hold a lock across a blocking
call the file doesn't already. Check-then-act on shared state moves
inside the lock or becomes one atomic operation.

## I/O and trust

`printf(user_string)` is a format-string vulnerability —
`printf("%s", user_string)`. User input never reaches `system` /
`popen` as a string — `exec*` with an argument vector. Paths from
users are validated after resolution — no `fopen(concat(dir, name))`.
Never build SQL by concatenation — the library's bound parameters.
HTTP / auth / money: [trust.md](trust.md).

## Leftovers

No `printf` / `std::cout` debug lines in library code. No
`using namespace std;` in headers. No commented-out code, dead
`#ifdef 0` blocks, or `// TODO` stubs shipped as done. Compile with
the repo's warning flags and fix what this patch introduced — do not
add pragmas or casts to silence a real diagnostic. No hardcoded
secrets. Else after `return` is noise; don't wrap a boolean.
