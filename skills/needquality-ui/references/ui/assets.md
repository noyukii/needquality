# Assets

Read from [ui.md](../ui.md) when the patch adds images, video,
icons, or quotes. Job: **evidence**. NN/G: people skip decorative
photos. Don't invent people. A **mark** on a control is a kit
icon or inline SVG.

## Tells

| Tell | Fix |
|---|---|
| Generated rasters (`picsum`, Unsplash-as-product, six-finger hands, SVG blob hero) | Real asset or labeled placeholder |
| Fake testimonials / "Trusted by" / bot counts | A named quote, or none |
| Emoji as icons; mixed Lucide + emoji + SVG blobs | Same icon language as the rest of the file |
| `→` / `↗` / `▸` as the mark (`Get started →`) | Kit icon or inline SVG. The verb has no glyph |
| `<img>` without width/height | Explicit dimensions; below-fold `loading="lazy"` |
| Hero stock that contradicts the product | NN/G: featured imagery must reflect the brand. Oil company + water stock is a lie |
| Autoplaying video | [motion.md](motion.md) · [heroes.md](heroes.md) |
| `rounded-2xl` + `shadow-lg` + `backdrop-blur` as the image treatment | Crop and type. Don't frame every asset as a card |

## Marks

A mark is a directional, status, or nav symbol on a control
(arrow, external, chevron, close, check, warning). Text-only is
correct for Save / Cancel / a labeled primary with no mark.

1. Same icon import already in the file or nearby.
2. Kit slot from that kit's docs. Named import, not a barrel.
3. No icon package: inline SVG, 16–24px, `currentColor`,
   `aria-hidden` if the label is visible. One family per file.
   Copy a path; do not invent a stroke. Do not add a package
   for one button.
4. Icon-only controls still need a name.
   [operable.md](operable.md).

Done: grep *this* diff for `→` `↗` `▸` `›` in button/link text.

## Why

NN/G homepage 2.4 / *Photos as Web Content*: decorative graphics
are skipped. The fold is too expensive for a blob. First
impressions form in milliseconds; a mismatch (generic welcome,
wrong image) is abandonment, not "atmosphere."

Heuristic #2 match the real world: a screenshot of *this*
product beats a 3D abstract. Krug: billboard, not mood board.

WCAG 1.1.1: meaningful images need alt that names the function;
decorative `alt=""`. Don't put the H1 only inside the image.

Frost: a hero image dimension is an *atom* with constraints
(aspect, max weight). Templates must survive missing images —
type still has to carry the job.

## In this patch

1. Real file from the repo, or a labeled placeholder
   (`Product screenshot`). No random Unsplash.
2. No invented names, faces, or logos.
3. Marks: the ladder above. One set. Size below the type.
   [cards.md](cards.md). Lucide as an equal feature-grid is that
   file's slop; Lucide as chrome on a control is this one.

## Sources

- [NN/G: Homepage Design](https://www.nngroup.com/articles/homepage-design-principles/) (imagery, examples)
- [NN/G: Photos as Web Content](https://www.nngroup.com/articles/photos-as-web-content/)
- [Atomic Design, ch. 2](https://atomicdesign.bradfrost.com/chapter-2/)
- WCAG 1.1.1 Non-text Content
