# Forms

Read from [ui.md](../ui.md) when the patch is inputs, validation,
or a multi-step flow. Job: **collect**. GOV.UK: one thing per
page unless the questions are a single unit. Strings:
[copy.md](../copy.md).

## Tells

| Tell | Fix |
|---|---|
| Placeholder-only label | Visible `<label>`. Placeholder is a format example only |
| Error on first keystroke; toast that vanishes as the only error | Validate after blur/submit. Error next to the field. Keep the value |
| Multi-field errors with no summary | Error summary at top, focus it ([GOV.UK error summary](https://design-system.service.gov.uk/components/error-summary/)) |
| Secret password rules after failure; OTP that blocks paste; six one-char boxes | Show the rule first. Allow paste (`autocomplete="one-time-code"`) |
| `<select>` for 2–3 options; First + Last; phone as three boxes; two-column form | Radios; one field per identity; one column |
| Re-ask name/email on step 2 of the same flow | Prefill editable, or let them pick (WCAG 2.2 Accessible Authentication) |
| Field error for "service down" | That's a page, not a red border. [states.md](states.md) |
| `onPaste` + `preventDefault`; submit disabled from first paint | Allow paste. Disable after the request starts; spinner *with* the label |
| Email/tel/date as `type="text"`; `<input>` under 16px | Native `type` / `autocomplete`. Never disable zoom |
| Landing closer = sharp box + two fields + one earth rectangle button | Unprompted spec-sheet closer on persuade. Fine on a datasheet. Else form chrome from a kept fetch |
| Keyboard overlays submit (`resizes-visual`) | `interactive-widget=resizes-content` if the form must stay above the OSK |

## Why

Baymard: labels above the field, still visible while typing.
Inline/placeholder labels fail at correction. Floating labels
are a compromise, not a replacement.

GOV.UK (Paul, 2015, *One thing per page*): split questions —
easier for low-confidence users, better on mobile, errors and
branches stay local. Question pages pattern: legend as heading,
hint, then control.

Wroblewski (*Web Form Design*): path to completion, align
labels, don't ask what you will not use. Nielsen #5 error
prevention, #9 diagnose and recover: name the field, the
failure, the next step. No "invalid" / "please."

WCAG 2.2: don't require recall of a password *into* a login
field that blocks paste (3.3.8). Status messages that don't take
focus still need a live region (4.1.3) if they are toasts.
[overlays.md](overlays.md).

Hick: fewer fields, progressive disclosure. Radios for 2–3
choices so options are visible (recognition, not recall —
heuristic #6).

## In this patch

1. Native control before a widget. Kit Input/Select if present.
2. One column. Labels stay.
3. Errors: next to the field + summary if several.
4. Copy: [copy.md](../copy.md).

## Sources

- [Baymard: Form design](https://baymard.com/learn/form-design)
- [GOV.UK question pages](https://design-system.service.gov.uk/patterns/question-pages/)
- [One thing per page](https://designnotes.blog.gov.uk/2015/07/03/one-thing-per-page/)
- [GOV.UK error summary](https://design-system.service.gov.uk/components/error-summary/)
- Luke Wroblewski, *Web Form Design*
- WCAG 2.2 3.3.8 Accessible Authentication, 4.1.3 Status Messages
