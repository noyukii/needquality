# Dart / Flutter

Read this when touching `.dart` / `pubspec.yaml`. Core rules in
`SKILL.md` still apply. Layout or a new look: [ui.md](ui.md). HTTP /
auth / money: [trust.md](trust.md).

## Format

`dart format` on touched files. Fix what `dart analyze` reports on
your lines; do not add `// ignore:` for a diagnostic this patch
introduced. Match the repo's null-safety idioms, `const` usage, and
state-management library — do not add a second one (bloc next to
riverpod) for one screen.

## Nullability and parsing

`!` on wire data, a map lookup, or an inherited widget that can be
absent is a crash with intent. Parse JSON into typed objects with
explicit checks (the repo's `fromJson` convention); fail on a missing
required field instead of defaulting it.

```dart
// slop
final name = (json['user'] as Map)['name'] as String? ?? '';

// needquality
final user = json['user'];
if (user is! Map<String, dynamic>) {
  throw FormatException('missing user in $endpoint response');
}
final name = user['name'] as String;
```

## Async

Await futures or return them — a dangling future's error is a
swallowed failure (`unawaited` only with a reason). HTTP calls get a
`timeout`, and the status code is checked before `jsonDecode` is
treated as success. Do not start a fetch per rebuild; kick it off in
`initState` / the repo's controller and cancel or ignore stale
responses.

## Widgets and state

Check `mounted` before `setState` after an `await`; do not use a
`BuildContext` across an async gap. Dispose what you create:
controllers, streams, timers, focus nodes. Derive display values in
`build`; do not copy constructor parameters into state and
synchronize them later. Lists that reorder need value keys, not
indexes. Use the semantic widget (`TextButton`, `TextField`,
`ListView.builder` for long lists) and keep labels/semantics on
icon-only controls.

## Time, strings, money

Store and compare `DateTime.toUtc()`; wall clock needs an explicit
location package if the app has one. Money is `Decimal` (or integer
cents) — never `double`. `String.length` is UTF-16 units — use
`characters` for user-visible truncation.

## Leftovers

No `print` in production paths (`debugPrint` or the repo's logger
during development only). No `TODO` stubs shipped as done. Secrets do
not go in source or `SharedPreferences` — the platform secure storage
the repo uses. Don't wrap a boolean; else after `return` is noise.
Bind a repeated expression only when one evaluation preserves
mutation, timing, exceptions, and observed state.
