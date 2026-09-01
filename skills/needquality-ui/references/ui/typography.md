# Typography

Read from [ui.md](../ui.md) when the patch sets faces, sizes, or
line-height. Job: **read**. Display + body from the *subject*,
unless the repo already chose.

## Tells

| Tell | Fix |
|---|---|
| Inter / Roboto / Poppins / Geist as the only face; Geist / Space Grotesk / Instrument Serif / DM Sans / IBM Plex / Plus Jakarta / Fraunces / Playfair as the "not Inter" swap | Display + body from a fetched subject page |
| Italic serif as the unprompted hero (Fraunces / Playfair / Recoleta / Newsreader italic) | Roman, or a display face from the fetches. Editorial only if the brief is editorial |
| IBM Plex Mono / JetBrains Mono / Geist Mono / Fira Code on chrome, labels, or tables | Mono for code. UI type from the subject |
| One line-height on headings and body; heading and body within ~4px | Headings ~1.1–1.25, body ~1.5–1.65. A scale, not 20/18/16 |
| `font-bold` (700) on every heading; only 400 and 700 exist | Body/chrome 400/500/600. Display weight and contrast copy the kept page (800/900, inked, outlined, chromatic when the fetch has them). A quieter grotesk at 600 is not a type choice |
| Body `< 16px`; chrome `< 11px`; `px` on body type | `1rem` body; chrome ≥12px |
| Prose the full viewport | Body *measure* `max-width: ~65ch`. Not the whole landing canvas — that is the doc-column default |
| No tracking; `tracking-tighter` until glyphs collide; all-caps body | Slight negative on large display only. Caps for a few words |
| Headings wrap to a widow (`… of` on its own line) | `text-wrap: balance` (headings), `pretty` (body) |
| `font-family: Inter` with no fallback; no `font-display` | Stack + `swap` |
| Gradient text on "AI"; 01/02/03 eyebrows | Same type language as the rest |

## Why

Bringhurst (*The Elements of Typographic Style*): a scale, not
ad-hoc sizes; body that can be read in long stretches. Material
3 treats type as a *role* system (display / headline / title /
body / label), not one `font-bold`. GOV.UK updated type scale:
body that stays ≥16px on the web.

Glanceable-typography work (pmid:32425139, pmid:32089101):
short-form UI type is not book type. Contrast against busy
backgrounds fails first. Don't set display type on a mesh hero
and hope.

Visual-attention study on mobile learning UIs (PMC10328315):
attention tracks color, text, and typography together — a
"unique" face that is still Inter-adjacent does not create
hierarchy. Size and weight do.

WCAG: body 4.5:1, large text 3:1. Large means 18pt/14pt bold,
not "the H1 looks big." [operable.md](operable.md).

## In this patch

1. Two families max unless the repo has more. Not the fingerprint
   faces unless the file already uses them. Weight and contrast
   from the kept page — do not flatten display to 600.
2. Roles: display, body, chrome. Not a new size per section.
3. `lang` on `<html>`. Tabular nums on tables:
   [tables.md](tables.md).

## Sources

- Robert Bringhurst, *The Elements of Typographic Style*
- [Material 3 typography](https://m3.material.io/styles/typography)
- [GOV.UK type scale](https://design-system.service.gov.uk/get-started/new-type-scale/)
- pmid:32089101 (legibility at-a-glance)
- pmid:32425139 (type over complex backgrounds)
- PMC10328315 (visual attention / type)
