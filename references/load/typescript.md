# TypeScript

Read this when touching `.ts` `.mts` `.cts` `.tsx`. JavaScript
runtime is already loaded when the Load table says so. Core rules
in `SKILL.md` still apply.

## Format and types

Match the file: semicolons, quotes, `type` vs `interface`, `import type`.
Run the repo formatter (`prettier`, `biome`, `eslint --fix`) on touched
files instead of hand-rewriting indent.

Prefer parsing over asserting:

```ts
// slop
const user = payload as User
const id = data as unknown as string

// needquality
const user = parseUser(payload) // throws or returns Result
```

`as any`, `as unknown as T`, `@ts-ignore`, `@ts-expect-error` on
unknown wire data is slop even with a why-comment — parse or narrow.
A why-comment is only for a compiler hole on *trusted* values.
Primitive parameters do not get `String(x)` / `Number(x)`
re-coercion — the type already said what they are.

Do not re-declare an exported `type`/`interface` that already exists under
the same name in another file. Import it. Don't add `types.ts` /
`interfaces.ts` for one type — it lives next to the user.

A Zod schema with only `z.infer` hits and no `.parse`/`.safeParse` at
the handler is a type alias — the wire is open.

Don't add `@ts-nocheck` / `eslint-disable` to silence a diagnostic you
introduced. Fix the code.

A field you emit exists on the type you already import. Don't add
`foo?:` only to make a ghost method compile. `obj.fn?.()` /
`in` / `'fn' in obj` of a method the type does not have is a
ghost — call the real API or implement it.

## Shared state (Prisma / ORM)

```ts
// slop — both requests pass the check
const slot = await db.slot.findUnique({ where: { id } })
if (slot.isReserved) throw conflict()
await db.slot.update({ where: { id }, data: { isReserved: true } })

// needquality — one winner
const n = await db.slot.updateMany({
  where: { id, isReserved: false },
  data: { isReserved: true },
})
if (n.count === 0) throw conflict()
```

Do not `await` inside a lock if the await is I/O. Do not
`Promise.all` a check-then-act and call it concurrency-safe.
Read-modify-write of a JSON/JSONB column (`{ ...row.meta, k: v }`)
loses concurrent keys — `jsonb_set` / `||`, or version the row.

N+1:

```ts
// slop — still N queries if you Promise.all it
const posts = await db.post.findMany()
const withAuthors = await Promise.all(
  posts.map(async (p) => ({ ...p, author: await db.user.findUnique({ where: { id: p.authorId } }) })),
)

// needquality
const posts = await db.post.findMany({
  take: 50,
  include: { author: { select: { id: true, name: true } } },
})
```

`new PrismaClient()` inside a handler is slop — one module-scoped
client. Unique email is a constraint (or the store's equivalent), not
only `findByEmail` then insert.

Money: integer cents or Prisma `Decimal` from a **string** — not
`number` / `parseFloat`.

## Next server (`.ts` actions / `route.ts`)

`'use server'` at file top exports public POSTs. Parse and authz
inside each. `formData.get('x') as string` is slop — `.parse`.
Don't call `cookies()` / `headers()` inside `cache()` / `'use cache'`.
Next 15+: `params` / `searchParams` / `cookies()` are async.

## Leftovers

Internal imports: grep which package exports the symbol; declare
`workspace:*` in that package's manifest before importing.

Next.js `export const config = { matcher }` only routes traffic.
Client-writable metadata is not a role. RLS: `USING (true)` or no
policy are not equivalent. `USING (true)` grants broad access for the
policy's commands and roles; enabled RLS with no applicable policy is
default-deny, subject to table-owner and `BYPASSRLS` exceptions. See
[trust.md](trust.md#row-level-security-postgres).
