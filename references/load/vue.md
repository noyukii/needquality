# Vue

Read this when touching `.vue`. Then read `javascript.md` for the
script and `typescript.md` when the script uses `lang="ts"`. Match the
repo's Vue major, Composition/Options API, and state library.

## Format

Match the file: `<script setup>` vs `setup()` vs Options API, SFC
block order, macro style (`defineProps` destructure vs object). Do not
migrate a component between API styles as drive-by work. Emit the
file's ref style — `ref` vs `reactive` — instead of introducing the
other for one value.

## Reactivity

Use `computed` for values derived from props/state. Use `watch` only to
synchronize with an external system; do not copy a computed value into
another ref. Keep one source of truth.

```vue
// slop — second source of truth, drifts
watch(() => props.items, (v) => { visible.value = v.filter(f) })

// needquality
const visible = computed(() => props.items.filter(f))
```

Destructuring `props` or a `reactive` object detaches reactivity —
`toRefs` / `computed`, or keep the object. A `watch` that starts a
listener or interval returns/cleans it up (`onWatcherCleanup`, the
cleanup callback) and cancels stale async work before applying a
late response.

## State and structure

Reuse the repo's composable or store; do not add `useFoo`, `utils.ts`,
or a second state library for one caller. A new composable is earned
by a second consumer, not by ceremony. Represent loading / empty /
error as state the template renders — a failed fetch is not an empty
list.

Prefer semantic elements and the existing component kit. Stable keys
must identify list items; do not use the index when items reorder.
Keep `<script setup>` / imports / macros in the file's existing style.
`v-if` and `v-for` do not share a tag; hide-vs-destroy (`v-show` vs
`v-if`) follows what the toggle means, not habit.

## Boundaries

`v-html` and unsanitized markdown are XSS. Render user text as text or
use the project's sanitizer. Do not pass request bodies wholesale into
stores or API calls; allowlist fields and parse unknown responses.
Outbound fetch needs a timeout/signal and a status check before JSON.
Authz belongs in the server boundary, not a route guard or hidden
button — the guard is UX, the server check is the control. HTTP /
auth / money: [trust.md](trust.md).

## Leftovers

No unused refs/imports, empty catch, `console.log`, `TODO`, or
`eslint-disable` added to quiet this patch. If a composable starts a
listener, timer, or request, clean it up on unmount and cancel stale
responses. No `setTimeout` to dodge a lifecycle/DOM race —
`nextTick` or the correct hook. Test the named route, not only
component mounting.
