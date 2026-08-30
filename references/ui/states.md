# States

Read from [ui.md](../ui.md) when the patch is loading, empty,
error, disabled, or success. Job: **status**. Nielsen #1:
visibility of system status. Loading ≠ empty ≠ error.

## Tells

| Tell | Fix |
|---|---|
| `"No records"` / `<Empty />` while loading | Skeleton or busy that matches the layout |
| `data ?? []` after error | Don't invent success. Show the failure |
| Skeleton that doesn't match the layout; skeleton on a <1s load | Mirror the real blocks, or skip |
| Frame-only skeleton (header, blank canvas) | NN/G: users assume the page is broken |
| Totally blank empty panel | Name what belongs here + one action to populate it |
| Disabled submit from first paint | Disable after the request starts; spinner *with* the label |
| Toast as the only error | Persistent message. [forms.md](forms.md) / [overlays.md](overlays.md) |
| Happy path only | Empty / loading / error / disabled *are* the product |

## Why

NN/G skeleton screens: a wireframe of the *coming* layout
reduces perceived wait. Animated shimmer is optional; a
header-only frame is not a skeleton. Spinners are for short
unknown waits; skeletons for full-page structure. Don't skeleton
a sub-second local render.

NN/G empty states: blank is ambiguous (still loading? error?
new?). Use the hole to teach and to start the task — a button
that creates the first record, not "No data."

Heuristic #1 and #9: say what happened and how to continue.
WCAG 4.1.3: a status that doesn't take focus still needs a role
so AT hears it. Doherty threshold (Laws of UX): feedback <400ms
feels like a conversation; beyond that, show wait.

GOV.UK: error message + error summary; notification banner for
page-level success. Don't reuse a red field border for downtime.

## In this patch

1. Three branches at the data boundary: pending, empty, failed.
2. Empty invites one next step. Copy: [copy.md](../copy.md).
3. Don't disable the control before the user can try.

## Sources

- [NN/G: Skeleton Screens 101](https://www.nngroup.com/articles/skeleton-screens/)
- [NN/G: Empty-State Interface Design](https://www.nngroup.com/articles/empty-state-interface-design/)
- [NN/G: Visibility of System Status](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [Doherty Threshold](https://lawsofux.com/doherty-threshold/)
- [WCAG 4.1.3 Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
