# Next.js

Read this when `next` is in the lockfile and the patch touches
`app/`, `pages/`, `next.config.*`, `middleware.ts`, `proxy.ts`,
or `route.ts`. Also [react.md](react.md). Core rules in
`SKILL.md` still apply. Read the lockfile major before writing
`middleware.ts` vs `proxy.ts` (Next 16+).

## Files

`error.tsx` is `'use client'`. `global-error.tsx` renders
`<html>` + `<body>`. `loading.tsx` is the segment Suspense
boundary. `route.ts` and `page.tsx` cannot share a folder.
Prefer `unauthorized()` / `forbidden()` over a client
`router.replace('/login')` flash. GET `route.ts` conflicts with
`page.tsx` in the same segment.

## Image, link, font, metadata

`next/image`, not `<img>`. `width` / `height` or `fill`. `fill`
requires `sizes`. `priority` on the LCP / hero; below-fold stays
lazy. Remote hosts only via `images.remotePatterns`.
`next/link` for internal routes, not `<a href>`. Fonts via
`next/font`, not a render-blocking Google Fonts `<link>`.
`generateMetadata` / `export const metadata` only in Server
Components. `viewport` is a separate export. OG via `next/og`
or file conventions.

## Data

Suspense the slow island — do not `await` page data before
returning shell. Start independent promises before the first
`await`; defer `await` into the branch that uses it.
`after()` from `next/server` for logging after the response when the
installed Next major supports it — do not `await` side effects before
`return`. `cache()` from
`react` for per-request dedup of `auth()` / `getUser()`;
primitive args only. Pass only fields the client renders across
the RSC boundary.

## Scripts and bundle

`next/script` with an explicit strategy. `next/dynamic` (or
`import()`) for heavy client widgets not needed for first paint.
`ssr: false` when the package touches `window`. Statically
analyzable `import()` — not `import(PAGE_MODULES[name])`.
Defer analytics until after hydration. Do not static-import
`@vercel/analytics` in the root layout.

`'use server'` = public POST, matcher ≠ authz, async `params` /
`cookies`: already in [react.md](react.md). Do not repeat.
