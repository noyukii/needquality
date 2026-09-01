# Android

Read this when the patch touches Android app code (Activity, Fragment,
ViewModel, Compose). [kotlin.md](../kotlin.md) still applies. Do not
glob `kotlin/`.

## Scopes and lifecycle

Coroutines launch in `viewModelScope` / `lifecycleScope` — never
`GlobalScope`. UI collection of flows uses
`repeatOnLifecycle(STARTED)` (or `collectAsStateWithLifecycle` in
Compose), not a bare `collect` in `onCreate` that keeps running in the
background. Nothing blocks the main thread: Room/DAO and disk I/O are
suspend functions or move to `Dispatchers.IO`. A ViewModel never holds
an Activity/Fragment `Context` or a View — that is the leak.

## State

One source of truth in the ViewModel (`StateFlow` / the repo's
holder); the UI renders it. Do not copy state into the view and
synchronize by hand. Represent loading / empty / error as states the
UI shows — a failed load is not an empty list.

## Compose

Hoist state; a composable takes values and lambdas, not the ViewModel
buried three levels deep when siblings pass state down. `remember`
keys include what the value derives from. Side effects live in
`LaunchedEffect` / `DisposableEffect` with correct keys — not directly
in composition. Lazy lists provide stable `key`s. Do not read state in
a scope broader than needed — that is the recomposition storm.

## Platform

User-visible strings go in resources when the repo localizes; match
the existing theme/tokens instead of hardcoding colors and sizes.
Runtime permissions follow the existing request flow — check, request,
handle denial; do not assume grant. Secrets and tokens go in the
repo's secure storage (Keychain-equivalent: EncryptedSharedPreferences
/ Keystore), never plain `SharedPreferences` or source. Network calls
use the existing client with timeouts; parse and check success before
using the body — a failed request is not an empty list.
[trust.md](../trust.md) when this patch does HTTP / auth / money.
