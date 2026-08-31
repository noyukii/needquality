# JavaScript

Read this when the load table says so. Core rules in `SKILL.md`
still apply. Do not re-read typescript.md / react.md / trust.md —
the Load table already pulled those when the extension needs them.

## Format

Match the file: semicolons, quotes, ESM vs `require`. Run the repo
formatter (`prettier`, `biome`, `eslint --fix`) on touched files.

`==` / `!=` only if *this* file already does. `parseInt` / `Number` /
`+` are not a schema (`parseInt("10px")`, `Number("") === 0`).
`Array.sort()` without a compare function is lexicographic
(`[10, 2, 1]` → `[1, 10, 2]`) and mutates the array (`const y = x.sort()`).

## Errors

Empty `catch`, `catch { console.error(e) }` then continue, and
`catch (e) { throw e }` with nothing added are all slop. Catch to
recover, to add context (`throw new FooError("…", { cause: e })`),
or to clean up and rethrow.

Do not invent success: `items ?? []` is fine for "missing means
empty"; it is not fine for "the request failed so pretend there were
no items."

## Promises and fetch

A floating promise (`fetch(...)` with no `await` / `.catch`,
`arr.forEach(async …)`, `map(async` without `Promise.all`, or
`doWork()` fired from a handler) is an unhandled rejection — Express 4
hangs, Node dies. `fetch` only throws on network failure. HTTP
success is 2xx: check `res.ok` (or `status/100 == 2`) before
`.json()`. A 5xx body is not data. `Promise.allSettled` then keeping
only `fulfilled` is invented success. After `res.json` / `res.send`,
`return` — a second write is headers-already-sent.

`fetch(url)` needs an `AbortSignal` (or the client's timeout). No
timeout hangs the worker. Independent I/O starts together
(`Promise.all`). Sequential `await` of independent work is a
waterfall. Do not `Promise.all` a check-then-act. Do not
`Promise.all` an unbounded user-sized list of I/O.

```js
// slop — 500 becomes "data"
const data = await (await fetch(url)).json()

// needquality
const res = await fetch(url, { signal: AbortSignal.timeout(10_000) })
if (!res.ok) throw new Error(`prices ${res.status}`)
const data = await res.json()
```

JSON at a trust boundary: `JSON.parse` in `try`, or the project's
parser. Invalid JSON is a failure, not `{}`.

## Prototype pollution

`JSON.parse('{"__proto__":{"isAdmin":true}}')` is a normal own key.
`Object.assign(target, parsed)`, lodash `merge` / `defaultsDeep`, and
`obj[key] =` of user keys then write `Object.prototype`. Spread of a
parsed object (`{ ...defaults, ...parsed }`) is not the same bug at
one level — still allowlist keys. Do not `Object.assign(user, req.body)`
or recursive-merge query/body into config.

```js
// slop
const settings = Object.assign({}, defaults, JSON.parse(raw))

// needquality — allowlisted keys only
const parsed = JSON.parse(raw)
const settings = {
  theme: parsed.theme === "dark" ? "dark" : defaults.theme,
  locale: typeof parsed.locale === "string" ? parsed.locale : defaults.locale,
}
```

Reject keys `__proto__`, `constructor`, `prototype` if you must loop
user keys. Don't `for (const k in body)` / `'admin' in body` of
parsed JSON. `Map` / `Object.create(null)` for dictionaries from user
input.

## DOM

User-controlled HTML is XSS. `el.innerHTML`, `document.write`,
Vue `v-html`, Svelte `{@html}`, unsanitized markdown, SVG uploads,
and `href` / `src` / `srcDoc` / `action` / `formAction` of
`javascript:` / `data:` / `file:` are not.
`postMessage` with `targetOrigin: '*'` plus `event.data` as code or
HTML is the same class. Sanitize with the project's library, or
don't render HTML.

No `eval` / `new Function` / `setTimeout("string")`. Do not import a
package that is not in `package.json` / workspaces.

`addEventListener` / `setInterval` without a matching `remove` /
`clear` on the same path leaks. Browser `fetch` in a long-lived
listener still needs abort.

## Node

Never `path.join(dir, userFilename)` / `sendFile` of a user path
(`../` counts). `Buffer.from(user, encoding)` : don't guess encoding
from the body. `readFileSync` / `execSync` on a request path blocks
the event loop — async, or don't. `child_process.exec` with a user
string is `shell=True`. Tokens: `crypto.randomUUID` / Web Crypto, not
`Math.random`.

Never `NODE_TLS_REJECT_UNAUTHORIZED=0` / `rejectUnauthorized: false`.

Webhook route: verify the HMAC on the *raw* body (timing-safe)
before acting. Unsigned POST is public.

`new PrismaClient()` (or a new pool) inside a handler is slop — one
module-scoped client; pooler URL in serverless. Module-scope
`let currentUser` / a request cache on the singleton leaks across
requests (Node and RSC).

## Time and strings

`new Date("2026-03-08")` is midnight UTC; `new Date("2026-03-08T00:00")`
is midnight local. They are different days outside UTC. Do not treat
either as a birthday. `string.length` counts UTF-16 units —
`"👍".length === 2`. Truncate with `Intl.Segmenter` or a well-named
helper, not `.slice(0, n)` on user text.

## Leftovers

A `node --test` probe goes in a file you already touch. Do not
create `*.test.js`. A used name is imported. No unused bindings.
Don't `if (cond) return true; else return false` — `return cond`.
Else after `return` is noise. Same expression twice in one
function → bind. `obj.fn?.()` of a method this file's type or
imports do not have is a ghost. CSRF / JWT / public env / SQL:
[trust.md](trust.md) when this patch does HTTP or a store.

Not `localStorage.setItem('token'` / `sessionStorage` for the session
JWT unless the project already chose that. Any XSS reads it. Prefer
the project's auth helper.

Money: integer cents or a decimal **string** — not `number` /
`parseFloat`. Thin wrappers (`export const fetchUsers = (id) => api.fetchUsers(id)`)
get deleted; call `api.fetchUsers` at the site. Don't create
`src/utils`, `src/types`, or a `features/*/services` tree for one
callsite.
