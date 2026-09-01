# Vue

Read this when touching `.vue`. Then read `javascript.md` for the
script and `typescript.md` when the script uses `lang="ts"`. Match the
repo's Vue major, Composition/Options API, and state library.

## State and structure

Use `computed` for values derived from props/state. Use `watch` only to
synchronize with an external system; do not copy a computed value into
another ref. Keep one source of truth. Reuse the repo's composable or
store; do not add `useFoo`, `utils.ts`, or a second state library for
one caller.

Prefer semantic elements and the existing component kit. Stable keys
must identify list items; do not use the index when items reorder.
Keep `<script setup>` / imports / macros in the file's existing style.

## Boundaries

`v-html` and unsanitized markdown are XSS. Render user text as text or
use the project's sanitizer. Do not pass request bodies wholesale into
stores or API calls; allowlist fields and parse unknown responses.
Outbound fetch needs a timeout/signal and a status check before JSON.
Authz belongs in the server boundary, not a route guard or hidden
button.

## Leftovers

No unused refs/imports, empty catch, `console.log`, `TODO`, or
`eslint-disable` added to quiet this patch. If a composable starts a
listener, timer, or request, clean it up on unmount and cancel stale
responses. Test the named route, not only component mounting.
