# Motion

Read from [ui.md](../ui.md) when the patch animates, transitions,
or autoplays. Job: **continuity**, not attention. If it doesn't
explain a state change, delete it.

## Tells

| Tell | Fix |
|---|---|
| Motion with no `prefers-reduced-motion` | Honor it. Instant or fade only |
| `transition: all`; bounce; motion >5s | List properties; `transform`/`opacity`; 150–300ms ease |
| Press that reflows neighbors (`hover:scale-105`) | Color/border; bounds stay put |
| Autoplaying carousel / video in the hero | Still. Pause/stop if >5s (WCAG 2.2.2) |
| Parallax, scrolljacking, autoforwarding | NN/G: disorienting; looks like ads; vestibular risk |
| Content `opacity: 0` until scroll | Visible at rest |
| Skeleton shimmer as the only "alive" signal on a slow load | OK if layout matches. [states.md](states.md) |
| Mesh/aurora/orbs behind the hero | Generic decoration is slop. Sheen that *is* the subject is not. On persuade, do not escape to none. [heroes.md](heroes.md) [color.md](color.md) |

## Why

WCAG 2.2.2 Pause, Stop, Hide; 2.3.3 Animation from Interactions:
motion from scrolling/gestures can be disabled. `prefers-reduced-
motion` is the CSS hook ([web.dev](https://web.dev/articles/prefers-reduced-motion)).

NN/G homepage: don't use motion to draw attention — movement is
read as advertising (banner blindness). Paramount-style autoplay
with no pause fails both UX and 2.2.2.

Material motion: easing and duration as a *system* (standard /
emphasized), transform/opacity so you don't trigger layout.
150–300ms is the usable band for UI; longer is a scene.

Laws of UX (Doherty): feedback fast. Animation that delays the
result is the opposite.

## In this patch

1. Transform/opacity only for enter/exit of *this* state.
2. Reduced-motion media query in the same file as the animation.
3. No layout animation (`width`/`height`/`top`) unless the kit
   already does that flip.

## Sources

- [web.dev: prefers-reduced-motion](https://web.dev/articles/prefers-reduced-motion)
- [WCAG 2.2.2](https://www.w3.org/WAI/WCAG22/Understanding/pause-stop-hide.html) · [2.3.3](https://www.w3.org/WAI/WCAG21/Understanding/animation-from-interactions.html)
- [NN/G: Homepage — minimize motion](https://www.nngroup.com/articles/homepage-design-principles/)
- [Material 3 motion](https://m3.material.io/styles/motion/overview)
- [Doherty Threshold](https://lawsofux.com/doherty-threshold/)
