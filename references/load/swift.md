# Swift / SwiftUI

Read this when touching `.swift`, SwiftUI, or Swift concurrency. Core
rules in `SKILL.md` still apply. Match the deployment target and the
existing observation/navigation style.

## Format

Run `swiftformat` / `swiftlint` only when the repo configures them,
and only on touched files. Match the file: `guard` vs `if let` style,
trailing closures, access control, `struct` vs `class` conventions.
Do not use a language or SDK feature newer than the deployment target.

## Errors and optionals

`try?` that discards the error and `try!` / force-unwrap on fallible
work are swallowed failures. Handle, or propagate with `throws` and
let the boundary decide.

```swift
// slop
let user = try? decoder.decode(User.self, from: data)
return user ?? User.placeholder

// needquality
do {
    return try decoder.decode(User.self, from: data)
} catch {
    throw APIError.malformedBody(underlying: error)
}
```

`!` is acceptable only for a documented programmer invariant.
`guard let` with a named failure beats a pyramid of `if let`. A
failed request is not an empty array or a placeholder model. Use the
repo's error type; do not add a second one beside it.

## State and views

Keep `body` declarative. Derive display values during rendering; do not
copy props into `@State` with `onAppear` or an effect. Use the existing
`ObservableObject` / `@Observable` model as the source of truth. Do not
create a nested view type or a second state store for one expression.
Represent loading / empty / error as states the view renders — not a
spinner that never resolves.

Use `Button`, `NavigationLink`, `TextField`, `List`, and `Form` for
their semantics. A gesture on a decorative view is not a button. Give
icon-only controls an accessibility label and keep visible focus and
Dynamic Type working. Native materials or Liquid Glass are chrome,
not a reason to restyle every surface; match the product and OS.
Stable identity for list items (`Identifiable` / explicit `id:`), not
array indexes when items reorder.

## Concurrency and I/O

Use `.task(id:)` for view-lifetime async work so SwiftUI can cancel it.
Do not start a new unbounded `Task` from every render or `onAppear`.
Keep UI state on `@MainActor`; do not hold a lock across `await`.
Propagate cancellation and errors. Check `Task.isCancelled` in loops
that outlive the view. Shared mutable state crossing tasks belongs in
an actor or one isolated owner — not a class with "we're careful."

Use the existing `URLSession` configuration and request timeout. Check
the HTTP status before treating the decoded body as success; parse a
structured error body only to construct the failure. Parse unknown
JSON into `Decodable` types; do not force-cast (`as!`) or force-unwrap
wire data. Secrets belong in Keychain, not `UserDefaults` or source.
Use the repo's persistence transaction/uniqueness rule for writes —
check-then-act on a store is a race. HTTP / auth / money:
[trust.md](trust.md).

## Time, strings, money

`Date` is an instant. Wall-clock math goes through `Calendar` with an
explicit `TimeZone` — do not add `86400` and call it tomorrow. Money
is `Decimal`, never `Double`; user-visible formatting goes through the
repo's `FormatStyle` / formatter. `String.count` counts grapheme
clusters — fine for user text; byte or UTF-16 limits (APIs, DB
columns) are measured in the encoding's view.

## Leftovers

No `try!`, `as!`, `fatalError`, `TODO`, or `print` in a finished path
— the repo's logger, or nothing. Keep `Task` handles, timers,
notifications, and continuations cancellable or removed on the same
lifecycle path. No unused imports or dead `@State`. Don't wrap a
boolean (`return cond`); else after `return` is noise. Run
`swiftformat`, `swiftlint`, and the existing test/build command only
when the repo has them.
