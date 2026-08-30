# Overlays

Read from [ui.md](../ui.md) when the patch is a dialog, popover,
select, tooltip, menu, toast, sheet, or tabs. Job: **borrow the
kit**. Custom `useState` + `absolute` drops focus trap, portal,
keyboard, and aria.

## Tells

| Tell | Fix |
|---|---|
| `useState(false)` + `fixed inset-0` / click-outside | Import the kit primitive. Fetch *that* component's docs |
| Second overlay library | One kit |
| `isOpen` when the file uses `open` | Match this repo's prop names |
| `z-[9999]` on internals | Kit portal. `className` is layout *around* the overlay |
| `isPending` / `isCompact` / `withIcon` on a kit component that has slots | Compose, or an explicit variant |
| Hover-only `<Tooltip />` as the only name | Visible text. Tooltip is extra, not the label |
| Toast that vanishes as the only error | Error next to the field. [forms.md](forms.md) |
| Toasts with no `aria-live`; `assertive` on every success | `role="status"` polite for success; assertive only for an error that does not take focus |
| Select "doesn't work" inside a Modal | Kit `portal` / `container` prop. Don't rewrite Select |
| Tabs as the only way to reach content | URL if they should survive refresh. Panels in the DOM |

## Why

Frost: these are molecules with contracts (focus, dismiss,
label). GOV.UK ships Notification banner, not a toast stack;
error summary takes focus. Nielsen #3 user control: Esc, Cancel,
undo. #4 consistency: platform dialogs, not a unique modal.

WCAG 4.1.3: status messages that don't take focus must be
programmatically determinable (`role="status"` / `aria-live`).
A modal *does* take focus — it is a change of context, not a
status message. Don't mix the two.

Sara Soueidan on live regions: polite for completions, don't
spam assertive. Kit Toast already chose a role; don't wrap it
in another live region.

Native before a widget: `<dialog>`, `<select>`, `popover` where
the kit uses them. CSS before measuring the DOM.

## In this patch

1. Name the kit from `package.json`. Grep the primitive.
2. Dialog/Sheet get a Title. Menu items in their Group.
3. Separator not `<hr>` if the kit has one.
4. Empty/Alert/Skeleton/Badge from the kit if they exist.

## Sources

- [NN/G: 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) (#3, #4)
- [WCAG 4.1.3 Status Messages](https://www.w3.org/WAI/WCAG22/Understanding/status-messages.html)
- [GOV.UK notification banner](https://design-system.service.gov.uk/components/notification-banner/)
- [Sara Soueidan: aria-live](https://www.sarasoueidan.com/blog/accessible-notifications-with-aria-live-regions-part-1/)
- [Atomic Design, ch. 2](https://atomicdesign.bradfrost.com/chapter-2/)
