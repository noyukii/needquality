# Zig

Read this when touching `.zig` / `build.zig`. Core rules in `SKILL.md`
still apply. Match the repo's Zig version — std APIs move between
releases; grep the vendored std or build files instead of recalling a
signature.

## Format

`zig fmt` on touched files. Match the file's naming and error-set
style. Keep `comptime` for what must be compile-time; a runtime value
does not need a comptime ceremony.

## Errors

`try` propagates; `catch` handles. `catch unreachable` on an
operation that can actually fail is a crash with intent — reserve it
for proven invariants.

```zig
// slop
const file = std.fs.cwd().openFile(path, .{}) catch unreachable;

// needquality
const file = std.fs.cwd().openFile(path, .{}) catch |err| {
    return err;
};
```

An empty `catch {}` or `catch |_| {}` swallows the failure. Name the
error set you handle; `anyerror` in a signature loses the contract the
compiler could check. `unreachable` is an assertion, not error
handling.

## Allocation and lifetime

Take the allocator as a parameter like the surrounding code; do not
hardcode a global allocator in library code. Every allocation has an
owner and a `defer`/`errdefer` free on every path — `errdefer` for the
partial-construction path. Do not return a pointer or slice into a
local or a freed buffer. Reads of `undefined` are undefined behavior,
not zero — initialize before use.

## Bounds and integers

Slices from outside get their lengths checked before indexing. Integer
casts on user-derived sizes are explicit (`@intCast`) and checked —
size math can overflow before allocation (`std.math` checked ops).
Sentinel-terminated pointers from C interop are validated before use.

## I/O and trust

Check every syscall-ish result the file's convention checks — short
reads/writes are results, not errors. User input never reaches a
shell-string exec — argv arrays via `std.process`. Paths from users
are resolved and validated before open. Never build SQL or commands by
concatenation. HTTP / auth / money: [trust.md](trust.md).

## Leftovers

No `std.debug.print` left in library paths — the repo's logging
(`std.log`) or nothing. No `TODO` / stub bodies shipped as done. No
dead `comptime` branches or commented-out code. Don't wrap a boolean;
else after `return` is noise. Bind a repeated expression only when one
evaluation preserves mutation, timing, errors, and observed state.
