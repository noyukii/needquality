# Cards / feature grids

Read from [ui.md](../ui.md) when the patch is a set of feature
tiles, a bento, or a product grid. Job: **rank**. Cards are a
repeated *molecule* (Frost). Equal cells are a grid to fill, not
a hierarchy.

## Tells

| Tell | Fix |
|---|---|
| Exactly three equal cards, icon-in-rounded-square, Lucide | Unequal weight. One lead, or a list. Icon smaller than the type. Lucide as chrome on a control is the fix — [assets.md](assets.md) |
| Bento of equal cells on dark | Size and span follow content. Empty cells are padding, not "balance" |
| Nested card in a card | One surface. Inner content is type + space |
| Icon + heading + paragraph, same size, three times | If the copy is the point, drop the icons. If the artifact is, show it |
| Card is the click target *and* contains a button | One hit target. Whole card `<a>` *or* a button, not both |
| `rounded-2xl` + `shadow-lg` on every box | Surface step. See [color.md](color.md) |
| Cream tile + hard offset black shadow on sage/paper (sticker neo-brutalist) | Next centroid. Elevation from the fetched world, or none |

## Why

NN/G visual hierarchy: contrast, scale, grouping. If everything
is a card, nothing is. Proximity (Gestalt) already groups; a
border is optional.

Hick / choice overload: three parallel "features" with equal
CTAs is three decisions. One path, or a scannable list.

Frost's product-grid organism: the *same* molecule repeated is
fine for catalogs (item, price, image). It is slop for a
marketing "why us" where the three items were invented to fill
the row.

Eye-tracking on dashboards (PMC11435723): layout order and
symmetry change perceived complexity. A 3-column equal grid
reads as decoration, not as a task.

## In this patch

1. Ask whether this is a catalog (repeat) or an argument (rank).
2. Catalog: one molecule, real data, not three lorem features.
3. Argument: a heading + evidence. Not a card component.
4. Hit target ≥24×24 CSS px (WCAG 2.5.8); 44×44 if touch.
   [operable.md](operable.md).

## Sources

- [NN/G: Visual Hierarchy](https://www.nngroup.com/articles/visual-hierarchy-ux-definition/)
- [Atomic Design, ch. 2](https://atomicdesign.bradfrost.com/chapter-2/) (organisms / product grid)
- [Hick's Law](https://lawsofux.com/hicks-law/)
- *The Effects of Layout Order on Interface Complexity* (PMC11435723)
