# Uniqueness

Read this when inventing a landing, marketing, or campaign look, or
replacing the visual world. Core rules in `SKILL.md` still apply.
Skip this file for operate/settings/tables, matching existing
tokens, or a layout tweak inside an existing screen. Fingerprint
in [ui.md](ui.md). First screen: [ui/heroes.md](ui/heroes.md).
Tokens: [ui/color.md](ui/color.md) [ui/typography.md](ui/typography.md).
Fetches: [ui/inspo.md](ui/inspo.md). Confirm AI:
[ui/detect.md](ui/detect.md).

Banning Inter is not a look. The unprompted swap (paper canvas,
narrow column, left stack, one earth button) is the 2026 default.
Flattening chroma into matte — even with a different layout — is
the same default. Taste is this subject's artifact, combined with
living pages. Not "make it look better" and not a section recipe.

## Job first

Name **persuade** / **operate** / **read** before markup.

- **Read** (docs, spec, wiki, datasheet, long article): a narrow
  column, left type, muted field, hairline rows are often *right*.
  Use them. Do not invent a poster over a manual.
- **Operate** (app, settings, table): density and states. Not a
  memorable hero. [ui.md](ui.md).
- **Persuade** (landing, campaign, marketing): those same choices
  are the unprompted default. Do not start there. Invent a
  composition from the artifact. Use the doc-column only if the
  brief asks, or the product *is* a spec/docs site.
  "Make a site for X" with no docs/wiki/datasheet ask is
  **persuade**.

The rest of this file is for persuade, or for replacing a visual
world. Centroids below are legitimate when the job or brief earns
them. As the first idea they are the same failure.

## Process

Do not ship CSS before fetches. Do not start from a page recipe
(identity → facts → form).

1. **Name the subject and the job.** Audience, one artifact, persuade
   vs read vs operate. Guessable from the category → still the
   centroid.
2. **Name the finish** in one word from the artifact (enamel, wet
   metal, fluorescent print, lacquer, photographic, chrome, CRT,
   newsprint, uncoated). If that word is matte / dusty / muted /
   paper / sage / stone and the job is persuade, invent again from
   the object's sheen and chroma, not a quieter cousin of the last
   page. Keep matte when the artifact *is* uncoated paper, clay,
   dust, or concrete, or the job is **read**.
3. **Name the first viewport in one sentence** — where the artifact
   sits, what is large, what is aligned, and the finish. If that
   sentence is "narrow centered column, everything left, matte
   ground" and the job is persuade, invent again from the artifact
   (pack, mill, road, jacket), not from a README.
4. **Fetch living pages** — [inspo.md](ui/inspo.md). Three world
   sites, one 21st.dev hit, one X or gallery hit. Steal structure,
   type pair, density, chroma, sheen. Not logo or copy. A URL you
   did not open is not a reference.
5. **Confirm looks that may be AI** — [detect.md](ui/detect.md).
   If a detector (or 4+ fingerprint hits) says the page is the
   AI cluster, do not *copy* it. Keep looking. A confirmed-AI
   page can still teach one device the brief already asked for.
6. **Lock tokens from the fetches**, not from avoidance. ≤3 hues;
   roles are tints (4–6 named values). Copy chroma and sheen; do
   not desaturate a kept page into paper. One display + one body
   that are not the fingerprint faces unless the repo uses them.
   One radius, one density, one accent. Hues from the artifact or
   a kept page, one sentence ("the enamel on this pack", "this
   wet road", "the vest"). On persuade, one hue may own a whole
   region — a timid paper field plus a brown button is avoidance,
   not restraint. A large dusty fill is still matte.

Layout → theme → one motion. Full-page one-shots are slop. Write
hex/type/don'ts only if more screens follow (~2KB). Tokens stay in
existing theme/CSS. Don't add DESIGN.md unless asked.

**Self-check.** If someone could guess the look from the category,
or from category-plus-"not Inter", or from category-plus-matte,
rework. Swapping the logo onto another of this session's pages
must not work.

## Unprompted defaults (earn them)

Not bans. Skip as the *first* idea on a free persuade axis. Keep
when the job is read/docs/spec, the brief pins it, a kept fetch
is actually that world, or the artifact's material is that finish.

- Doc-column: max-width stack, all left, matte/paper/sage/cool-gray
  field, optional vertical rail, identity → labeled rows → boxed
  form
- Paper spec-sheet: hairline rules as the only layout, one
  rust/forest rectangle button, label-left fact rows
- All-matte finish: low chroma everywhere, no sheen, quiet
  mid-weight grotesk — independent of layout. Cream, sage, stone,
  cool-gray, dusty olive, and charcoal with no gloss are the same
  tell
- Cream `#F4F1EA` + terracotta + italic serif (Fraunces / Playfair
  / Instrument Serif)
- Near-black + acid green / vermilion + glow
- Teal / cyan as the "not blue" pick
- Geist / Space Grotesk / DM Sans / IBM Plex / Plus Jakarta as
  the "not Inter" face; mono as the UI face
- Broadsheet kickers, 01/02/03, decorative grid; cream card +
  hard offset shadow on sage

## Optional external detectors

Use an explicitly requested detector or design skill when the host exposes it.
Discover that capability from the current tool or skill inventory rather than
assuming a provider-specific filesystem path. Without one, use the bundled
fingerprint and [detect](ui/detect.md) checks. Do not install a detector as a
side effect of this flow.

## Don't

Don't scrape a brand into DESIGN.md. Don't fork 2–3 directions as ceremony. Don't skip
fetches because the defaults "should be enough." Don't treat a
centroid as never-allowed. Don't flatten a saturated fetch into
paper.
