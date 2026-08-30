# Assets

Read from [ui.md](../ui.md) when the patch adds images, video,
icons, or quotes. Job: **evidence**. NN/G: people skip decorative
photos. Don't invent people.

## Tells

| Tell | Fix |
|---|---|
| Generated rasters (`picsum`, Unsplash-as-product, six-finger hands, SVG blob hero) | Real asset or labeled placeholder |
| Fake testimonials / "Trusted by" / bot counts | A named quote, or none |
| Emoji as icons; mixed Lucide + emoji + SVG blobs | Same icon language as the rest of the file |
| `→` / `↗` / `▸` as the icon (`Get started →`) | Kit icon, or the verb with no glyph. Match the file |
| `<img>` without width/height | Explicit dimensions; below-fold `loading="lazy"` |
| Hero stock that contradicts the product | NN/G: featured imagery must reflect the brand. Oil company + water stock is a lie |
| Autoplaying video | [motion.md](motion.md) · [heroes.md](heroes.md) |
| `rounded-2xl` + `shadow-lg` + `backdrop-blur` as the image treatment | Crop and type. Don't frame every asset as a card |

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

1. Real file from the repo, or a labeled placeholder (`Product
   screenshot`). No random Unsplash.
2. No invented names, faces, or logos.
3. Icons: one set. Size below the type. [cards.md](cards.md).

## Sources

- [NN/G: Homepage Design](https://www.nngroup.com/articles/homepage-design-principles/) (imagery, examples)
- [NN/G: Photos as Web Content](https://www.nngroup.com/articles/photos-as-web-content/)
- [Atomic Design, ch. 2](https://atomicdesign.bradfrost.com/chapter-2/)
- WCAG 1.1.1 Non-text Content
