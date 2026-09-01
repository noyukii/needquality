# Kotlin

Read this when touching `.kt` / `.kts`. Core rules in `SKILL.md` still
apply. Android app code (Activity, ViewModel, Compose):
[android.md](kotlin/android.md). JVM backend frameworks follow
[java.md](java.md) I/O and shared-state rules.

## Format

Match the file: `ktlint` / `ktfmt` only when configured. Match the
repo's style for expression bodies, named arguments, and trailing
commas. Emit Kotlin, not Java-in-Kotlin: no `getX()` wrappers around
properties, no builder ceremony where a data class with defaults exists.

## Nullability

`!!` on wire data, a map lookup, or a DB result is a crash with intent.
Parse, check, or fail with a named error.

```kotlin
// slop
val user = users[id]!!

// needquality
val user = users[id] ?: throw NotFoundException("user $id")
```

`requireNotNull` / `checkNotNull` with a message are for programmer
invariants, not trust-boundary input. A chain of `?.` that silently
skips required work is invented success — fail on the missing value.
`lateinit` is for framework injection points, not "I'll set it later."

## Types and structure

A sealed class or enum beats boolean flags that encode illegal states.
`when` over a sealed type lists every branch — no `else` that hides a
future variant. A data class is the default for values. No `Utils.kt`
or `Extensions.kt` dump for one function; put the extension next to its
caller.

## Coroutines

No `GlobalScope.launch` — use the caller's scope so cancellation and
failure propagate. No `runBlocking` inside production async paths.
Blocking I/O moves to `withContext(Dispatchers.IO)`. A `launch` whose
exception nobody observes is a swallowed failure — return the
`Deferred`, join it, or install the scope's error handler. Don't
launch an unbounded coroutine per element of a user-sized list.

## Time, strings, money

`java.time` on the JVM: `Instant` for instants, explicit `ZoneId` for
wall clock. Money is `BigDecimal` from a `String` or integer cents,
never `Double`. `String.length` is UTF-16 units, not characters —
be careful truncating user text. Normalize identifiers (NFC) before
uniqueness checks.

## Shared state and I/O

Check-then-act on a shared map or row is a race — `putIfAbsent`, a
unique constraint, or one conditional `UPDATE`. One HTTP client for
the process with explicit timeouts. Check response success before
decoding the body as success. Never build SQL with string templates
(`"WHERE id = $id"`) — bound parameters. A query per loop element is
N+1. A logged-in user's id parameter still needs an owner check.
HTTP / auth / money: [trust.md](trust.md).

## Leftovers

No `println` / `TODO()` in a finished path — `TODO()` throws in
production. No unused imports. Do not add `@Suppress` for a warning
this patch introduced. No hardcoded secrets. Don't wrap a boolean
(`return cond`, not `if (cond) true else false`); else after `return`
is noise. Bind a repeated expression only when one evaluation preserves
mutation, timing, exceptions, and observed state; leave intentionally
repeated or stateful calls alone.
