# Navigation

Read from [ui.md](../ui.md) when the patch is a header, sidebar,
breadcrumbs, tabs-as-routes, skip link, or footer. Job:
**orient**. Frost: header is an organism (logo + nav molecule +
optional search). Jakob's law: logo top-left, home link, nav
where people already look.

## Tells

| Tell | Fix |
|---|---|
| Centered logo; logo that isn't a home link | Top-left (LTR). Implicit (logo) *and* explicit Home if the mark is abstract |
| Global nav only on hover / behind "Menu" with no signpost | Visible labels. Information scent |
| Glass `backdrop-blur` nav on a marketing page cloned into the app | App chrome is dense and stable, not a landing hero |
| No skip link; no `<nav>` / `<main>` | Skip to main. Landmarks |
| `target="_blank"` with no `rel` | `rel="noopener noreferrer"` |
| `div` onClick as navigation | `<a href>` / `Link` |
| Breadcrumbs that don't match the URL | Real path, or skip. GOV.UK breadcrumbs |
| Filters/tabs/pagination only in `useState` | URL if they should survive refresh or share |
| Hover-only current page | `aria-current="page"`. Contrast + text |

## Why

NN/G homepage: every page links home; logo top-left; nav in a
highly noticeable place; hide-on-hover menus fail. Heuristic #4
consistency with the rest of the web; #1 you-are-here.

GOV.UK: header, service navigation, back link, breadcrumbs,
skip link, footer — each has a job. Don't merge them into one
clever bar.

Fitts: primary nav items are large enough and not flush against
a destructive neighbor. Hick: ≤ a handful of top-level items;
the rest is information architecture, not a mega-menu of equal
weight.

Krug: users don't figure out your novel nav. Don't Make Me Think
applies hardest here.

## In this patch

1. Landmarks. Skip link first in the DOM.
2. One primary nav. Sidebar only if the product already has one
   — don't add the Linear/Notion chrome as a reflex.
3. Current item marked. Keyboard order = visual order.
   [operable.md](operable.md).

## Sources

- [NN/G: Homepage Design](https://www.nngroup.com/articles/homepage-design-principles/) (logo, nav, home link)
- [GOV.UK header](https://design-system.service.gov.uk/components/header/) · [skip link](https://design-system.service.gov.uk/components/skip-link/) · [breadcrumbs](https://design-system.service.gov.uk/components/breadcrumbs/) · [service navigation](https://design-system.service.gov.uk/components/service-navigation/)
- [Jakob's Law](https://lawsofux.com/jakobs-law/)
- Steve Krug, *Don't Make Me Think, Revisited*
