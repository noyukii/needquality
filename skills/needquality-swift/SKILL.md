# Swift / SwiftUI

Read this when touching `.swift`, SwiftUI, or Swift concurrency. Core
rules in `SKILL.md` still apply. Match the deployment target and the
existing observation/navigation style.

## State and views

Keep `body` declarative. Derive display values during rendering; do not
copy props into `@State` with `onAppear` or an effect. Use the existing
`ObservableObject` / `@Observable` model as the source of truth. Do not
create a nested view type or a second state store for one expression.

Use `Button`, `NavigationLink`, `TextField`, `List`, and `Form` for
their semantics. A gesture on a decorative view is not a button. Give
icon-only controls an accessibility label and keep visible focus and
Dynamic Type working. Native materials or Liquid Glass are chrome,
not a reason to restyle every surface; match the product and OS.

## Concurrency and I/O

Use `.task(id:)` for view-lifetime async work so SwiftUI can cancel it.
Do not start a new unbounded `Task` from every render or `onAppear`.
Keep UI state on `@MainActor`; do not hold a lock across `await`.
Propagate cancellation and errors. A failed request is not an empty
array or a placeholder model.

Use the existing `URLSession` configuration and request timeout. Parse
unknown JSON into `Decodable` types; do not force-cast (`as!`) or
force-unwrap wire data. Secrets belong in Keychain, not `UserDefaults`.
Use the repo's persistence transaction/uniqueness rule for writes.

## Leftovers

No `try!`, `as!`, `fatalError`, `TODO`, or `print` in a finished path.
`!` is acceptable only for a documented programmer invariant. Keep
`Task` handles, timers, notifications, and continuations cancellable or
removed on the same lifecycle path. Run `swiftformat`, `swiftlint`, and
the existing test/build command only when the repo has them.
