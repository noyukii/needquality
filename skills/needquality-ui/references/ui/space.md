# Space / layout

Read from [ui.md](../ui.md) when the patch sets padding, grid,
density, or viewport. Job: **group**. Space is a scale, not
`py-20` on every section.

## Tells

| Tell | Fix |
|---|---|
| `py-20` on every section; 4px and 7px mixed; `grid-cols-3` as the only layout | 4/8 scale. More space above a heading. Asymmetry when content is unequal |
| Hairline rules as the only grouping (spec-sheet rows, full-bleed `<hr>` between every block) | Group by proximity and type. A rule is optional. Fine on a datasheet |
| Doc-column as the *whole landing*: `max-w-prose` / ~65ch page, all left, matte field, vertical rail | Skip as the first idea on **persuade**. Correct for **read**. `65ch` is a *measure* for prose, not the canvas |
| `min-h-screen` / `100vh` | `svh`/`dvh`. Keyboard and iOS toolbars steal `vh` |
| `overflow-x-hidden` as a layout fix | Find the overflow. `clip` if you must hide; don't mask a bug |
| `z-[9999]` | Named z scale. Kit portal for overlays. [overlays.md](overlays.md) |
| `!important` | Specificity. Don't fight the kit |
| Canvas pinned to `w-[1280px]` | Wrap at 320. Fluid grid |
| Sticky nav/banner hides the focused field | `scroll-padding-top` on `:focus-visible`; don't stack sticky layers |
| Truncate in a flex child with no `min-w-0` | `min-w-0` |
| Full-bleed under a notch | `env(safe-area-inset-*)` |
| No `<main>` / `<nav>` / heading skip | Landmarks. Sequential headings. DOM order = tab order |

## Why

Material spacing and GOV.UK layout: a spacing *scale* (usually
multiples of 4/8) so rhythm is shared across components. Frost:
templates place organisms; they do not invent a new gutter per
section.

NN/G hierarchy: grouping by proximity and common region. Padding
inside a card that matches the gap between cards collapses the
group.

Fitts (pmid:11539107 and later 2D touch work): spacing *between*
targets is as load-bearing as size. WCAG 2.5.8: undersized
targets may still pass if a 24px circle around each does not
intersect another. Don't pack icon buttons.

Chrome `interactive-widget=resizes-content` when a form must
stay above the OSK; `100vh` + visual viewport is a covered
submit. [forms.md](forms.md).

Operate surfaces are denser than marketing. Don't import landing
padding into a table view. [dashboards.md](dashboards.md).

## In this patch

1. One density for the job (persuade / operate / read).
2. 4/8 scale. Gap from the kit if it has one.
3. Landmarks. Skip link: [navigation.md](navigation.md).
4. Persuade: the first viewport is a composition, not a README
   stack. [uniqueness.md](../uniqueness.md).

## Sources

- [Material 3 spacing](https://m3.material.io/styles/spacing)
- [GOV.UK layout / spacing](https://design-system.service.gov.uk/styles/)
- [Atomic Design, ch. 2](https://atomicdesign.bradfrost.com/chapter-2/) (templates)
- [Fitts's Law](https://lawsofux.com/fittss-law/)
- WCAG 2.5.8 Target Size (Minimum)
