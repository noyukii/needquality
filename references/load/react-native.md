# React Native

Read this when the lockfile or an import is `react-native` or
`expo`. The Load table already pulled javascript.md (and
typescript.md for `.ts` / `.tsx`). **Skip [react.md](react.md)** —
that file is web (`div`, `next/image`, `'use client'`,
`:focus-visible`). Layout or a new look: [ui.md](ui.md). HTTP /
auth / money: [trust.md](trust.md). Core rules in `SKILL.md`
still apply.

## Primitives

`View` / `Text` / `Pressable` / `TextInput` / `StyleSheet`. No
`div`, `span`, `onClick`, `className`, `window`, `document`,
`localStorage`, `dangerouslySetInnerHTML`. Navigation is
`expo-router` or React Navigation, not `next/link`. Text lives
inside `<Text>` — a raw string in a `View` throws at runtime.
Platform differences go through `Platform.select` / `.ios.tsx` /
`.android.tsx` like the repo already does, not `if` forests.

## State and effects

Same React rules as web: derive during render, no prop-copies into
state, effects synchronize with external systems only. Cancel or
ignore stale async work before applying a late response — navigation
away does not unmount a screen in a stack, so a fetch can resolve
into a screen the user left. Represent loading / empty / error /
offline as states the screen renders — a failed request is not an
empty list.

## Lists and images

Lists are `FlashList` / `FlatList`, not `.map` plus CSS
`content-visibility`. Stable `keyExtractor`, and a `renderItem` that
is not a new inline closure re-created per render when the repo
memoizes. Images are `expo-image` or RN `Image` with
an explicit size. Not `next/image`, not `<img>`. User URLs stay
untrusted (SSRF / file) — keep the threat, change the API.

## Chrome and a11y

`SafeAreaProvider` / `react-native-safe-area-context` and a
keyboard controller are required chrome. Web `:focus-visible` /
`100vh` does not substitute. Touch targets stay at the platform
minimum; icon-only controls get `accessibilityLabel`, actionable
views get `accessibilityRole` — a `Pressable` on a decorative view
is not a button.

## Storage and secrets

Tokens and secrets go in the platform secure store (`expo-secure-store`
/ Keychain / Keystore) — never `AsyncStorage`, never source.
`EXPO_PUBLIC_*` is public — same as other `*_PUBLIC_*` prefixes in
[react.md](react.md); nothing secret rides in it. Deep-link and push
payloads are user input — validate before navigating or writing.

## Do not import web

No `next/*`, no `react-dom`, no `'use client'`. App Router and
RSC rules do not apply. A web polyfill for one API is carry — use the
RN/Expo module the repo already has.
