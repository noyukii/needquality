# Color

Read from [ui.md](../ui.md) when the patch sets palette, tokens,
status hues, or dark mode. Job: **roles**, not decoration.
Material: 26+ roles mapped to emphasis and containers. NeedQuality:
≤3 hues; 4–6 named values that are tints of those hues.

## Tells

| Tell | Fix |
|---|---|
| Indigo/violet/purple gradient; inventing `#3B82F6` / `#2563EB` / `#6366F1` / `#F9FAFB` / `#09090B` | Match the file. Else a hue from the subject |
| Raw `bg-blue-500` beside `--primary` / kit `primary` | One token source. Hover/focus/status = lightness on the *same* hue |
| `zinc-950` + indigo glow; `gray-50` + white cards; permanent dark + lavender | Tint off those hexes. Scene picks light/dark |
| Colors named `gradient-start` or used as decoration | Semantic roles: canvas, text, action, danger, success |
| White cards on `gray-50` (≈1:1); `#000` on `#fff` | Space or a real surface step. Soft dark `#121212`–`#1e1e1e` |
| Cream+terracotta / black+acid green / teal-as-not-blue / sage-paper spec-sheet / matte field + one earth button on a free persuade axis | Unprompted defaults. Keep for docs/spec. Else chroma and sheen from a fetched artifact; on persuade one hue may own a region |
| All-matte field (paper / sage / cool-gray / dusty olive / charcoal, no gloss) on a free persuade axis | Skip as the first idea. Keep for uncoated/clay/dust/concrete or **read**. Copy chroma and sheen from the artifact or a kept page; do not desaturate into paper |
| Color-only status or color-only series | Text + color. [charts.md](charts.md) |
| Dark as `invert()` or "dashboards are dark" | Second palette. Raise lightness; drop chroma on accents *near white/black* only — not as a look |
| Dark theme without `color-scheme: dark` | Set it on `html` |

## Why

Material 3 color system: roles (primary, on-primary, surface,
outline, error…) so contrast is a pairing, not a hex you hope
passes. Dark is a scheme, not inverted light. Semantic colors
(error, success) stay put when the brand hue shifts.

WCAG 2 contrast is a 2D cut through 3D color space
(pmid:27534328) — that is why gray-on-gray and pastel-on-pastel
fail even when they "look fine" on a calibrated screen.
Constrained recoloring (arXiv:2512.05067) exists because brand
hexes routinely miss 4.5:1.

NN/G dashboards: color is preattentive for *category*, not for
*magnitude*. Don't encode "how much" as hue.

A11y-as-autonomy (arXiv:2506.10324): contrast and theme are user
settings, not a brand flex. Honor `prefers-color-scheme` when
the product already ships two palettes; do not invent a third.

## In this patch

1. Lock tokens before CSS. One accent hue from a fetched page or
   the artifact, not "not indigo." On persuade, chroma and sheen
   come from that source — a timid paper canvas plus a brown chip
   is avoidance, and a large dusty fill is still matte. A hue may
   own a field. **Read**/docs may stay muted.
2. Hover/focus/disabled = same hue, different lightness.
3. Check body 4.5:1, large 3:1, chrome 3:1.
4. Surface steps for elevation, not heavier shadows.
   [space.md](space.md). Generic glass / mesh / aurora is slop.
   Sheen that *is* the subject (lacquer, wet asphalt, neon, chrome)
   is not. On persuade, do not escape to "or none."

## Sources

- [Material 3 color system](https://m3.material.io/styles/color/system/overview)
- WCAG 2.2 contrast (1.4.3 / 1.4.11)
- pmid:27534328 (WCAG contrast in 3D color space)
- arXiv:2512.05067 (minimal color shifts for contrast)
- [NN/G dashboards / color vs quantity](https://www.nngroup.com/articles/dashboards-preattentive/)
