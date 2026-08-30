# Tables

Read from [ui.md](../ui.md) when the patch is a data grid, list
that behaves like a grid, or summary list. Job: **compare**.
GOV.UK Table / Summary list exist; don't invent a card grid of
the same rows.

## Tells

| Tell | Fix |
|---|---|
| Hover-only row actions | Persistent actions, or a row menu from the kit |
| Color-only status | Text + color |
| Fake "12 unread" | Real counts or none |
| Table + form + export on one canvas | One primary action |
| `"No records"` / `<Empty />` while loading; `data ?? []` after error | Loading ≠ empty ≠ error. [states.md](states.md) |
| Table of numbers in proportional figures | `tabular-nums`; `min-w-0` |
| Hardcoded `3/18/26` / `$1,000` | `Intl.DateTimeFormat` / `NumberFormat` |
| Truncate with no way to see the rest | `min-w-0` + title/expand. Don't hide the primary key |
| Custom sort/filter only in `useState` | URL if they should survive refresh or share |
| `<div>` rows that look like a table | `<table>` / kit Table, with headers |
| Dark all-caps mono table (Q / NAME / SIZE), hairline box, solid accent selected row, `·` in cells | Kit Table / this product's density. Headers match the file (not a new caps+mono language). Mono on numbers if at all. Selection from the existing accent, not a new acid green |

## Why

GOV.UK table: captions, column headers, numeric alignment.
Summary list for a *single* record's fields — not a 1-row table
dressed as cards.

Tidwell (*Designing Interfaces*): datagrid pattern is scan-
down, compare-across. Zebra is optional; alignment and headers
are not. Nielsen #6 recognition: sort/filter state visible, not
only in the URL bar after you already know.

Few / Tufte: a table often beats a chart for a few numbers. If
the chart exists, the same numbers must be available as a table
or `<details>`. [charts.md](charts.md).

Fitts: row actions that appear on hover fail pointer and
keyboard users. Persistent "Edit" / overflow menu.

## In this patch

1. Kit Table if the kit has one. `<th scope>` if you write HTML.
2. One primary column. Secondary data can wrap or hide at 320.
3. Empty/loading/error are three screens.
4. Localize numbers and dates.

## Sources

- [GOV.UK table](https://design-system.service.gov.uk/components/table/)
- [GOV.UK summary list](https://design-system.service.gov.uk/components/summary-list/)
- Jenifer Tidwell, *Designing Interfaces*
- Stephen Few, *Show Me the Numbers*
