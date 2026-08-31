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
`expo-router` or React Navigation, not `next/link`.

## Lists and images

Lists are `FlashList` / `FlatList`, not `.map` plus CSS
`content-visibility`. Images are `expo-image` or RN `Image` with
an explicit size. Not `next/image`, not `<img>`. User URLs stay
untrusted (SSRF / file) — keep the threat, change the API.

## Chrome

`SafeAreaProvider` / `react-native-safe-area-context` and a
keyboard controller are required chrome. Web `:focus-visible` /
`100vh` does not substitute.

## Do not import web

No `next/*`, no `react-dom`, no `'use client'`. App Router and
RSC rules do not apply. `EXPO_PUBLIC_*` is public — same as
other `*_PUBLIC_*` prefixes in [react.md](react.md).
