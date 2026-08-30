# React

Read this when touching `.tsx` `.jsx`. The Load table already pulled
javascript.md (and typescript.md for `.tsx`). Layout, look, or a new
surface: [ui.md](ui.md). Logic-only JSX: kit import + `<button>` +
`<label>` + `:focus-visible`; do not load `ui.md`. Core rules in
`SKILL.md` still apply.

Do not hand-roll Popover/Modal/Select if `@heroui/react`,
`components/ui`, or another kit is already here.

Subset of `vercel-react-best-practices`, composition patterns, Next
file conventions, and [You Might Not Need an Effect](https://react.dev/learn/you-might-not-need-an-effect).
A dedicated perf / design pass loads those skills.

## Effects and state

Derive in render. `useEffect(() => setX(compute(props)))` is slop —
extra render and the copy drifts. Put interaction logic in the event
handler, not an effect. Reset a whole subtree with `key={id}`, not
`useEffect(() => setComment(""), [userId])`.

```tsx
// slop
useEffect(() => { setFullName(first + " " + last) }, [first, last])

// noslop
const fullName = `${first} ${last}`
```

A function component defined *inside* another remounts every render
(state and DOM reset). Module-level, or a file. Pass props; don't
close over parent to skip them.

Don't mutate state: `items.push`, `draft.x =`, or `state.list[i] =`
then `setState(state)`. Copy, or the project's updater.

Stale closures: `useEffect(() => { setInterval(() => save(draft)) }, [])`
captures the first `draft`. Functional `setState`, read a ref, or put
`draft` in the dependency list *and* clear the interval. Don't
`eslint-disable-next-line react-hooks/exhaustive-deps` to hide it —
that's how the array stays wrong.

`useEffect` fetch: if a Server Component (or the framework's loader)
can fetch, do that and pass props. Client fetch needs cleanup so a
slow response can't write into the next `id` — `AbortController` or
an `ignore` flag. Check `res.ok` before `.json()`. Don't use a
Server Action as a GET.

## Client / server

`'use client'` at the leaf that needs the browser, not the page or
layout. Don't put `'use client'` on a module that imports `fs` /
Prisma / secrets to silence an RSC error. Don't pass
`process.env` (non-`NEXT_PUBLIC_`), session tokens, or secrets into
Client Components. Don't pass non-serializable props across the RSC
boundary (functions, `Map`, class instances). `Date` becomes a string
— pass an ISO string. Client components cannot be `async function`.
`export const metadata` / `revalidate` / `dynamic` from a Client
Component is ignored.

`'use server'` at file top makes **every export** a public POST, not
a Server Component. Do not put it on a page to "make it a server
component" — that's the default. Authz and parse *inside each*
action; a page-level `auth()` does not cover them. Extra form fields
are untrusted. `formData.get('email') as string` into the DB is slop —
`schema.parse`. Client Zod is UX, not authz.

Don't call `cookies()` / `headers()` / session inside `cache()` /
`unstable_cache` / `'use cache'`. Don't `force-cache` data that varies
on cookies or `Authorization`. Next 15+: `params` / `searchParams`
/ `cookies()` are async — `await` them. `try { redirect(); notFound() }`
then `catch` eats the navigation — they throw.

A mutating click with no pending state double-submits. `useTransition`
/ `useFormStatus` / disable the button. Idempotency still lives on
the server. Auth only in `useEffect` + `router.replace('/login')` is
a flash; the server never checked.

Don't add `'use client'` so you can `useEffect`-fetch data the parent
can load. Don't import `getServerSideProps` / `getStaticProps` /
`pages/api` / `next/head` / `next/router` `query` into the App Router.

React 19: `ref` is a prop. Don't wrap a new function component in
`forwardRef`. Skip this if the file is already React 18.

## Render bugs

`{count && <Row />}` renders `0`. Use a ternary.
`key={i}` on a list that inserts or reorders remounts the wrong row —
stable id. `useId()` for SSR-safe ids, not `Math.random()` in render.

`Date.now()` / `new Date()` / `Math.random()` / `window` /
`localStorage` / `document` in render hydrates wrong — clock in an
effect, or a server-only node. Don't `suppressHydrationWarning` (or
delete `StrictMode`) to hide it. `useSearchParams()` needs a suspense
boundary.

No layout reads in render (`getBoundingClientRect`, `offsetHeight`).
Flex/grid instead. Uncontrolled inputs unless you need the value
every keystroke.

Large lists: don't `.map` thousands of rows; virtualize or
`content-visibility: auto`.

## XSS and secrets

React text children are fine. `dangerouslySetInnerHTML`, unsanitized
markdown-to-HTML, and `href` / `src` / `srcDoc` / `action` of
`javascript:` / `data:` are not. Sanitize with the project's library
(`DOMPurify`, `react-markdown` to elements), or don't render HTML.
SVG uploads are HTML. `next/image` `src` of a user URL is SSRF.

`NEXT_PUBLIC_*` / `VITE_*` / `REACT_APP_*` / `EXPO_PUBLIC_*` is public. Auth tokens:
not `localStorage` unless the project already chose that — XSS reads
it. Prefer the project's HttpOnly session helper.

## Structure

**No barrels.** Import the file (`from './button'`), not
`from '@/components'` that re-exports the world.

**Cheap reject first.** `if (!id) return` before the first `await`.
Independent fetches start together. Sequential `await` of independent
I/O is a waterfall.

**Boolean props to customize.** Don't. Compose, or an explicit
variant (`IconButton`, not `Button isIcon`). Don't add `isPending` to
a kit Button that already has a spinner slot.

Don't `useMemo` / `useCallback` every value "for perf." Wrap when a
child is actually skipping renders or the calc is visibly expensive.

Next.js `export const config = { matcher }` only routes traffic —
copy the sibling's `requireAuth` / `auth()` inside the handler.
