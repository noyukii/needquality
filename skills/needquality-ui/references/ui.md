# UI / design-system kit

Read this for any web-facing work: pages, docs sites, themes,
templates, components, stories, and component libraries. UI guidance is
an implementation contract, not optional polish. It covers semantics,
keyboard behavior, states, tokens, responsive layout, visual hierarchy,
and accessibility even when the requested change is behavior or API
only. Non-UI web logic can use its language/framework reference alone.
`SKILL.md` decides when to load this file. Core rules there still apply:
don't invent an existing thing; look it up. For new web work, read
[templates.md](ui/templates.md). Strings: [copy.md](copy.md). Inventing a landing: [uniqueness.md](uniqueness.md)
(fetches: [ui/inspo.md](ui/inspo.md); confirm:
[ui/detect.md](ui/detect.md)).

For a new or changed interface, use the portable design lens in
[hig.md](ui/hig.md). It distills Apple’s cross-platform Human Interface
Guidelines into checks that also apply to web, Android, desktop, games,
and other products; target-platform APIs, dimensions, and conventions
stay in their own platform documentation.

One file per surface. Read only the part this patch builds.
Do not glob `ui/`.

| Part | File |
|---|---|
| Cross-platform design principles and UX review | [ui/hig.md](ui/hig.md) |
| Landing first screen | [ui/heroes.md](ui/heroes.md) |
| Landing research (new look only) | [ui/inspo.md](ui/inspo.md) |
| Confirm AI look (new look only) | [ui/detect.md](ui/detect.md) |
| Feature / bento cards | [ui/cards.md](ui/cards.md) |
| App home / KPI | [ui/dashboards.md](ui/dashboards.md) |
| Type | [ui/typography.md](ui/typography.md) |
| Color / dark | [ui/color.md](ui/color.md) |
| Space / layout | [ui/space.md](ui/space.md) |
| Forms | [ui/forms.md](ui/forms.md) |
| Tables | [ui/tables.md](ui/tables.md) |
| Charts | [ui/charts.md](ui/charts.md) |
| Modal / popover / toast / tabs | [ui/overlays.md](ui/overlays.md) |
| Header / nav / skip | [ui/navigation.md](ui/navigation.md) |
| Loading / empty / error | [ui/states.md](ui/states.md) |
| Motion | [ui/motion.md](ui/motion.md) |
| A11y / focus / hit | [ui/operable.md](ui/operable.md) |
| Images / icons / quotes | [ui/assets.md](ui/assets.md) |

## Before CSS

Name the job: **persuade** (landing), **operate** (app/settings), or
**read** (docs). Name the primary user action, content hierarchy, and
states it must show. A reference image, existing token, or named
component is a constraint, not inspiration; match it before inventing.
"Make it beautiful" is not a specification. Ask for one missing
decision rather than filling the screen with cards, copy, or effects.

For component-library work, name the component role, public states,
semantic element, keyboard path, and composition boundary before CSS.
Use the library's existing primitives, slots, tokens, registry entries,
and examples as the baseline. A new primitive needs a real missing
contract or an explicit custom request.

## Fingerprint

Undo these before the user sees the diff. If *this repo* (file,
tokens, or DESIGN.md) already is that look, match it. Four or more
on a *new* surface is the centroid. Brief can earn any one; the
cluster is slop.

| Tell | Fix |
|---|---|
| Inter / Roboto / Poppins / Geist as the only face; Geist / Space Grotesk / Instrument Serif / DM Sans / IBM Plex / Plus Jakarta / Fraunces / Playfair as the "not Inter" swap; IBM Plex Mono / JetBrains Mono / Geist Mono / Fira Code on chrome or tables | Display + body from the *subject* (fetched pages), unless the repo uses those. Mono for code. [typography.md](ui/typography.md) |
| Indigo/violet/purple gradient; inventing `#3B82F6` / `#2563EB` / `#6366F1` / `#F9FAFB` / `#09090B` (`blue-500`/`indigo-500`/`gray-50`/`zinc-950`) | Match the file. Else a hue from a fetched artifact, not "not-blue." [color.md](ui/color.md) |
| Paper spec-sheet *cluster*: muted cream/beige/sage/cool-gray canvas + hairline rules + one rust/forest rectangle button + label-left fact rows + boxed form | 2026 default on a *free persuade* axis. Fetch living pages. Keep when the job is a spec/datasheet. [uniqueness.md](uniqueness.md) |
| Doc-column *cluster*: one centered stack, everything left, matte field, optional vertical rail, identity → facts → form | Same: skip as the first idea on persuade. Correct for **read**/docs. [space.md](ui/space.md) [heroes.md](ui/heroes.md) |
| Cream `#F4F1EA` / beige canvas + terracotta + italic serif hero (Fraunces / Playfair / Newsreader); tracked mono kickers; 01/02/03; decorative grid wallpaper; cream card + hard offset shadow on sage | Next centroid. Brief can earn one; the cluster is slop. [color.md](ui/color.md) [heroes.md](ui/heroes.md) |
| All-matte finish: low chroma everywhere, no sheen, quiet mid-weight grotesk (paper / sage / cool-gray / dusty olive / charcoal) — even when the layout is not a doc-column | Unprompted default on a *free persuade* axis. Copy chroma and sheen from the artifact. Keep for uncoated/read. [color.md](ui/color.md) [uniqueness.md](uniqueness.md) |
| Raw `bg-blue-500` beside `--primary` / kit `primary`; custom accent still `ring-blue-500` / `green-500` | One token source. Hover/focus/status = lightness on the *same* hue. [color.md](ui/color.md) |
| `zinc-950` + indigo glow; `gray-50` + white cards; permanent dark + lavender as the only theme | Tint off those hexes. Scene picks light/dark. Dark is a second palette, not `invert()`. [color.md](ui/color.md) |
| Centered hero: pill "Now in beta", full-sentence H1, two CTAs; hero → 3 cards → pricing → FAQ | Short title; break the order or drop a section. [heroes.md](ui/heroes.md) |
| Exactly three equal feature cards, icon-in-rounded-square, Lucide; bento of equal cells on dark | Hierarchy, not a grid to fill. Icon smaller than the type. Lucide on a control is chrome, not this tell. [cards.md](ui/cards.md) |
| Collapsible sidebar + header search/bell + **four** KPI cards; Recharts `{ name: 'Jan', uv: 400 }`; "Welcome back" hero in an app | One real number this screen is for, or skip. Title of the task. [dashboards.md](ui/dashboards.md) |
| `min-h-screen` / `100vh` / `z-[9999]` / `overflow-x-hidden` / `!important` | `svh`/`dvh`; named z scale; kit portal; `clip`; specificity. [space.md](ui/space.md) |
| Placeholder-only label; `div` onClick; `outline-none` with no `:focus-visible` | `<label>`, `<button>`/`<a>`, visible focus in the brand color. [forms.md](ui/forms.md) [operable.md](ui/operable.md) |
| Generated rasters (`picsum`, Unsplash-as-product, six-finger hands, SVG blob hero); fake testimonials / "Trusted by" / bot counts | Real asset or labeled placeholder. A named quote, or none. Don't invent people. [assets.md](ui/assets.md) |
| `rounded-2xl` + `shadow-lg` on every box; generic glass `backdrop-blur` on nav/cards; mesh/aurora/orbs behind the hero | Elevation via surface steps. Generic decoration is slop. Sheen that *is* the subject (lacquer, wet asphalt, neon, chrome) is not. On persuade, do not escape to none. [color.md](ui/color.md) [motion.md](ui/motion.md) |
| Gradient text on "AI"; 01/02/03 eyebrows; emoji as icons; three-tier "Most popular" glow | Same icon language as the rest. Price how this product sells. [typography.md](ui/typography.md) [assets.md](ui/assets.md) |
| Hover-only row actions; color-only status; fake "12 unread"; table + form + export on one canvas | Persistent actions; text + color; real counts; one primary action. [tables.md](ui/tables.md) |
| Inline `·` (`THIS MAC · 3.9 MB`); `→` as the mark (`Get started →`); dark all-caps mono table (Q / NAME / SIZE) + hairline + acid-green selected row | Match the file. Else comma or a list; kit icon or inline SVG (verb has no glyph); kit Table / this product's density. [copy.md](copy.md) [tables.md](ui/tables.md) [assets.md](ui/assets.md) |

Also skip when the axis is free (persuade, no brief pin):
hero-metric as page structure, same-size icon+heading+text cards,
nested cards, dark mode as a reflex, graph-paper wallpaper,
terminal mockup as decoration, all-caps mono table as the
datagrid, autoplaying carousel, over-rounding, hairline + wide
shadow together, hairline rules as the only layout, italic serif
as the unprompted hero, the doc-column as the whole page, an
all-matte field with no sheen. A **read** surface may keep the
column, muted field, and hairlines.

Operate/settings/tables: density and states, not a memorable hero.
A glass nav or three feature cards inside a dashboard is the landing
stencil on the wrong job. Famous-app skins (Linear / Raycast / Stripe)
are the next centroid — pair from the subject's world. Validate the
primary action and empty/loading/error/disabled states, not just the
first screenshot.

## Don't invent an existing thing (UI)

The workspace kit (HeroUI, shadcn, MUI, Chakra, coss, Radix, …)
already has Popover, Modal, Select, Tooltip, Menu, Toast, Tabs. A
custom one from `useState` + `absolute` + click-outside drops focus
trap, portal, keyboard, and aria. Detail: [overlays.md](ui/overlays.md).

1. Name the kit from `package.json` and nearby imports. One kit.
2. Search that kit for the primitive. Grep, local wrapper, installed
   types, or the kit skill. Fetch *that* component's docs before
   markup. Red flags: `useState(false)` + `fixed inset-0`; a second
   overlay lib; `isOpen` when the file uses `open`.
3. Match *this* repo's composition. Do not invent `isOpen` / `open` /
   `visible`. A missing import is not "absent."
4. Do not add a second overlay library. Do not wrap the kit in
   `CustomX` that only forwards props.

```tsx
// slop
function Popover({ open, onClose, children }: Props) {
  useEffect(() => { /* click outside */ }, [open])
  if (!open) return null
  return <div className="fixed inset-0 z-50">{children}</div>
}

// needquality — looked up in @heroui/react, then imported
import { Popover } from "@heroui/react"
```

If a Select "doesn't work" inside a Modal, look up that kit's
portal/`container` prop. Compose as the kit documents: items in
their Group; Dialog/Sheet get a Title; Separator not `<hr>`;
Empty/Alert/Skeleton/Badge if those exist. `className` is layout
around the overlay, not `z-[9999]` on internals. Do not add
`isPending` / `isCompact` / `withIcon` to a kit component that
already has slots — compose, or an explicit variant.

Native before a widget: `<input type="date">` / `type="email"` /
`inputmode` / `autocomplete` before a picker. CSS (flex/grid,
`min-w-0`) before measuring the DOM in JS.

Inventing a landing/marketing look: [uniqueness.md](uniqueness.md).
Research before CSS: [inspo.md](ui/inspo.md). Confirm:
[detect.md](ui/detect.md).

## Type, color, space

[typography.md](ui/typography.md) · [color.md](ui/color.md) ·
[space.md](ui/space.md).

Craft after the face is chosen. Models set `leading-relaxed` and
`font-bold` on everything.

| Tell | Fix |
|---|---|
| One line-height on headings and body; heading and body within ~4px | Headings ~1.1–1.25, body ~1.5–1.65. A scale, not 20/18/16 |
| `font-bold` (700) on every heading; only 400 and 700 exist | Body/chrome 400/500/600. Display weight from the kept page |
| Body `< 16px`; chrome `< 11px`; `px` on body type; prose the full viewport | `1rem` body; chrome ≥12px; `max-width: ~65ch` |
| No tracking; `tracking-tighter` until glyphs collide; all-caps body | Slight negative on large display only. Caps for a few words |
| Headings wrap to a widow (`… of` on its own line) | `text-wrap: balance` (headings), `pretty` (body) |
| `font-family: Inter` with no fallback; no `font-display` | Stack + `swap` |
| Colors named `gradient-start` or used as decoration | Semantic roles: canvas, text, action, danger, success |
| `py-20` on every section; 4px and 7px mixed; `grid-cols-3` as the only layout | 4/8 scale. More space above a heading. Asymmetry when content is unequal |
| No `<main>` / `<nav>` / heading skip; `<html>` without `lang` | Landmarks. Sequential headings. DOM order = tab order |
| White cards on `gray-50` (≈1:1); `#000` on `#fff` | Space or a real surface step. Soft dark `#121212`–`#1e1e1e`, not pure black |

Dark: raise lightness; drop chroma on accents only near white/black,
not as a look. Elevation via surface steps, not heavier shadows.
Do not skip it when the product already has tokens. Do not force
it because "dashboards are dark." On persuade, chroma and sheen
come from the artifact — do not flatten into paper.

## Forms, tables, charts

[forms.md](ui/forms.md) · [tables.md](ui/tables.md) ·
[charts.md](ui/charts.md). Empty/loading/error:
[states.md](ui/states.md).

| Tell | Fix |
|---|---|
| Error on first keystroke; toast that vanishes as the only error | Validate after blur/submit. Error next to the field. Keep the value. Multi-field: summary at top, focus it |
| Secret password rules after failure; OTP that blocks paste; six one-char boxes | Show the rule first. Allow paste (`autocomplete="one-time-code"`) |
| `<select>` for 2–3 options; First + Last; phone as three boxes; two-column form | Radios; one field per identity; one column |
| Re-ask name/email on step 2 of the same flow | Prefill editable, or let them pick (WCAG 2.2) |
| Sticky nav/banner hides the focused field | `scroll-padding-top` on `:focus-visible`; don't stack sticky layers |
| `"No records"` / `<Empty />` while loading; `data ?? []` after error | Loading ≠ empty ≠ error |
| Skeleton that doesn't match the layout; skeleton on a <1s load | Mirror the real blocks, or skip |
| Hover-only `<Tooltip />`; color-only series; pie/area for magnitude | Length/position (bar/line). Same numbers as a table/`<details>` |
| Drag-only reorder / slider-only value; content `opacity: 0` until scroll | A click/keyboard path. Visible at rest |
| Field error for "service down" | That's a page, not a red border |
| Table of numbers in proportional figures | `tabular-nums`; `min-w-0` |

Localize: no `"You have " + n + " items"`. Don't nail button width to
English. Logical properties if RTL is in scope.

## Operable

[operable.md](ui/operable.md) · [motion.md](ui/motion.md) ·
[navigation.md](ui/navigation.md).

The look can pass a screenshot and still be inoperable. If the kit
already solved focus/label, use the kit. User HTML is XSS —
`dangerouslySetInnerHTML` / `v-html` / `{@html}` / `javascript:` hrefs
are not a styling choice.

| Tell | Fix |
|---|---|
| `text-gray-400` body under 4.5:1; `text-gray-500` on dark | Body 4.5:1, large 3:1, chrome 3:1 |
| Icon-only button, no name; identical "Copy" on twelve buttons | `aria-label` or hidden text; name what gets copied |
| Color-only error; happy path only (no empty/loading/error/disabled) | Text next to the field. Those screens *are* the product |
| Motion with no `prefers-reduced-motion`; `transition: all`; bounce; motion >5s | List properties; `transform`/`opacity`; 150–300ms ease |
| Press that reflows neighbors (`hover:scale-105`) | Color/border; bounds stay put |
| `onPaste` + `preventDefault`; submit disabled from first paint | Allow paste. Disable after the request starts; spinner *with* the label |
| Email/tel/date as `type="text"`; `<input>` under 16px; `user-scalable=no` | Native `type` / `autocomplete`. Never disable zoom |
| Filters/tabs/pagination only in `useState` | URL if they should survive refresh or share |
| Truncate in a flex child with no `min-w-0`; `<img>` without width/height | `min-w-0`; explicit dimensions; below-fold `loading="lazy"` |
| Hardcoded `3/18/26` / `$1,000` | `Intl.DateTimeFormat` / `NumberFormat` |
| Destructive with no undo; full-bleed under a notch | Confirm or an undo window. `env(safe-area-inset-*)` |
| Dark theme without `color-scheme: dark` | Set it on `html` |
| Toasts with no `aria-live`; `assertive` on every success; no skip link | `role="status"` polite for success; assertive only for an error that does not take focus |
| `target="_blank"` with no `rel` | `rel="noopener noreferrer"` |
| Hit target too small; `div` onClick as navigation | ≥24×24 CSS px (AA) or 44×44 touch; `<a href>` / `Link` |
| Keyboard overlays submit (`resizes-visual`); canvas pinned to `w-[1280px]` | `interactive-widget=resizes-content` if the form must stay above the OSK. Wrap at 320 |
