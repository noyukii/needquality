# Heroes

Read from [ui.md](../ui.md) when the patch is a landing first
screen. Job: **persuade**. Not inside an app — that is
[dashboards.md](dashboards.md). Strings: [copy.md](../copy.md).

A hero is an *organism* (Frost): heading + supporting line + one
primary action, sometimes an artifact. It sits in a homepage
*template*. Conventions of placement (logo top-left, nav, one
obvious next step) are Jakob's law. Look (type, hue, subject)
must not be the training-set stencil. Process:
[uniqueness.md](../uniqueness.md).

## Tells

| Tell | Fix |
|---|---|
| Pill "Now in beta" + full-sentence H1 + two equal CTAs | Short title. One primary action; secondary is a text link |
| Paper spec-sheet hero: all-caps condensed H1 + hairline fact rows + boxed schematic + one earth button | Unprompted 2026 default on persuade. Keep for a real spec. Else first viewport from the artifact. [uniqueness.md](../uniqueness.md) |
| Doc-column hero: left stack in a centered measure, matte ground, rail, then facts then form | Same. Invent alignment/bleed/overlap from the artifact unless the job is **read** |
| Generic welcome occupying the fold | Tagline that names the job. NN/G: cheerful welcomes are not information |
| Full-bleed photo / mesh / aurora / SVG blob with no product | Image of *this* work, or type only. Decorative graphics get skipped |
| Autoplaying video / carousel as the hero | Still frame. Pause/stop if motion lasts >5s (WCAG 2.2.2) |
| False floor: full-viewport image, nothing hints at more | Content that continues. Don't trap people in one screen |
| "Learn more" / "Get started" / "Click here" | Verb + object with information scent |
| Hero inside a dashboard or settings | Title of the task. See [dashboards.md](dashboards.md) |

## Why

NN/G homepage principles (Wang, 2024): say who you are and what
you do above the fold; show examples of the actual offering, not
category labels; one visual hierarchy for the top task; keep
motion down — moving things look like ads (banner blindness).
People scan; they do not read a paragraph H1
([How Users Read on the Web](https://www.nngroup.com/articles/how-users-read-on-the-web/)).

Hick's law: two equal CTAs raise decision time. Fitts's law: the
primary control is large and near where the eye already is.

Visual hierarchy for health-data layouts (PMC11491599): assign
size/contrast to the information rank *first*, then pick type and
color. Same order here: name the one thing the hero is for, then
style it.

Krug (*Don't Make Me Think*): self-evident billboard, not a
brochure. Norman (*Design of Everyday Things*): the button must
signify the action.

## In this patch

1. One H1. Product language, not a slogan.
2. One primary CTA. Secondary only if a real second job exists.
3. Logo and nav findable (Jakob). They do not force a left stack
   for the rest of the viewport.
4. Skip the fingerprint *clusters* on a free persuade axis.
   Fetch: [inspo.md](inspo.md). Confirm: [detect.md](detect.md).
5. Tokens from [color.md](color.md) / [typography.md](typography.md)
   locked before CSS.

## Sources

- [NN/G: Homepage Design, 5 Principles](https://www.nngroup.com/articles/homepage-design-principles/)
- [NN/G: 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/) (esp. #2 language, #8 minimal)
- [Atomic Design, ch. 2](https://atomicdesign.bradfrost.com/chapter-2/)
- [Hick's Law](https://lawsofux.com/hicks-law/) · [Fitts's Law](https://lawsofux.com/fittss-law/)
- Steve Krug, *Don't Make Me Think, Revisited*
- Don Norman, *The Design of Everyday Things*
