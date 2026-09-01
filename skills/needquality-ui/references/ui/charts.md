# Charts

Read from [ui.md](../ui.md) when the patch plots numbers. Job:
**compare quantities**. If the number is one value, use type.
[dashboards.md](dashboards.md) for the screen around the chart.

## Tells

| Tell | Fix |
|---|---|
| Recharts `{ name: 'Jan', uv: 400 }` | Real series or skip |
| Pie / donut / area / gauge for magnitude | Length (bar) or position (line/scatter) |
| Color-only series | Text + color; pattern or direct labels |
| Hover-only `<Tooltip />` as the only values | Same numbers in a table or `<details>` |
| Chart as decoration / "analytics vibe" | Delete it. One number the screen is for |
| Legend far from the marks, 8 hues | Direct label. ≤5 series or it's a table |
| Animation that replays on every render | Enter once. Honor reduced motion. [motion.md](motion.md) |

## Why

Cleveland & McGill (1985): elementary perceptual tasks ranked —
position along a common scale and length beat angle and area.
NN/G restates this for dashboards: pie, donut, treemap, and
radial gauges fail at-a-glance quantity. Color pops a *category*;
it does not scale a *value*. ~8% of men are color-vision
deficient; don't make hue the only series key.

Tufte: data-ink. Chartjunk (gradients, 3D, fake depth) is the
fingerprint of generated dashboards. Few: bullet graphs beat
gauges when you must show a measure against a target.

Dashboard text study (pmid:39255127): titles and annotations
carry the insight. A chart without a sentence ("this week vs
last") is a picture of a library.

## In this patch

1. Bar or line first. Pie only for part-to-whole with ≤3 slices
   *and* the numbers printed.
2. Accessible name. Don't rely on color.
3. Pair with the table of the same data, or skip the chart.

## Sources

- Cleveland & McGill, *Graphical Perception and Graphical Methods for Analyzing Scientific Data* (1985)
- [NN/G: Dashboards, preattentive](https://www.nngroup.com/articles/dashboards-preattentive/)
- Edward Tufte, *The Visual Display of Quantitative Information*
- Stephen Few, *Information Dashboard Design* / *Show Me the Numbers*
- pmid:39255127 / [arXiv:2407.14451](https://arxiv.org/abs/2407.14451)
