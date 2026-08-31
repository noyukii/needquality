# Operable

Read from [ui.md](../ui.md) when the patch can look fine in a
screenshot and still fail a keyboard, a screen reader, or a
thumb. Job: **use**. If the kit already solved focus/label, use
the kit. User HTML is XSS — `dangerouslySetInnerHTML` / `v-html`
/ `{@html}` / `javascript:` hrefs are not a styling choice.

## Tells

| Tell | Fix |
|---|---|
| `text-gray-400` body under 4.5:1; `text-gray-500` on dark | Body 4.5:1, large 3:1, chrome 3:1. [color.md](color.md) |
| Icon-only button, no name; identical "Copy" on twelve buttons | `aria-label` or hidden text; name what gets copied |
| Color-only error | Text next to the field. [forms.md](forms.md) |
| Placeholder-only label; `div` onClick; `outline-none` with no `:focus-visible` | `<label>`, `<button>`/`<a>`, visible focus in the brand color |
| Hit target too small | ≥24×24 CSS px (AA, 2.5.8) or 44×44 touch. Fitts: size + distance |
| `user-scalable=no`; `<input>` under 16px | Never disable zoom. Native `type` |
| No skip link; heading levels skip | [navigation.md](navigation.md) |
| Focus hidden under sticky chrome | WCAG 2.4.11 Focus Not Obscured. `scroll-padding-top` |
| `target="_blank"` with no `rel` | `rel="noopener noreferrer"` |
| Destructive with no undo | Confirm or an undo window. Heuristic #3 |
| Toasts with no live region | [overlays.md](overlays.md) |
| Dark theme without `color-scheme: dark` | Set it on `html` |

## Why

Nielsen's 10 heuristics (1994, reviewed 2024) are the interaction
baseline: status, language, exits, conventions, prevent errors,
recognition, shortcuts, minimal, recover, docs.

WCAG 2.2 adds: focus not obscured (2.4.11), target size 24×24
(2.5.8), accessible authentication without recall-and-type
barriers (3.3.8). Fitts (1954; HCI restatements pmid:11539107,
touch pmid:36762820): small distant targets cost time and
errors. Laws of UX restates size, spacing, placement.

Inclusive Design Patterns (Pickering): native controls, visible
focus, don't disable zoom. GOV.UK focus-state guidance: don't
remove the ring; brand it.

Contrast in 3D color space (pmid:27534328) is why "it looks OK
on my MacBook" is not a check. Beyond-compliance a11y
(arXiv:2506.10324): personalization beats a single passing
theme.

## In this patch

1. Keyboard: tab order = DOM order. `:focus-visible` in *this*
   file.
2. Name every control. Icon-only needs an accessible name.
3. Contrast checked on the actual tokens, not Tailwind's
   default gray.

## Sources

- [NN/G: 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [WCAG 2.2 what's new](https://www.w3.org/WAI/standards-guidelines/wcag/new-in-22/)
- [Fitts's Law](https://lawsofux.com/fittss-law/)
- pmid:11539107 · pmid:36762820 (pointing / button size)
- pmid:27534328 (contrast)
- Heydon Pickering, *Inclusive Design Patterns*
- [GOV.UK focus states](https://design-system.service.gov.uk/get-started/focus-states/)
