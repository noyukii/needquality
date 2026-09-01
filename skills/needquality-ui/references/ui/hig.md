# Cross-platform HIG lens

Use this with `ui.md` when designing or reviewing any interface. Apple’s
Human Interface Guidelines (HIG) are written for Apple platforms, but
their design principles are useful for web, Android, desktop, games, and
other products. Apply the principles below as a design review lens, not
as a requirement to copy Apple’s visual language.

Platform-specific sizes, safe-area rules, APIs, system components, and
input conventions are not portable. Look those up in the target
platform’s current documentation. Keep WCAG and the product’s existing
design system as independent requirements.

## Start with purpose

- Name the product value and the primary user task before adding UI.
- Keep the important path focused. Every visible element earns its place
  by helping people understand, decide, or act.
- Make the experience useful before making it distinctive.

## Give people agency

- Put people near the task or content they came for; keep chrome quiet.
- Show what is happening when work takes time, and give clear feedback
  when state changes.
- Let people explore, skip, exit, undo, or recover without losing work.
- Keep destructive actions reversible when possible; explain recovery when
  it is not.

## Earn trust

- Explain what the product does and why it asks for permissions or data.
- Collect and expose only what the task needs; protect sensitive data.
- Make system effects, automation, defaults, and irreversible consequences
  visible before they matter.

## Use familiarity deliberately

- Start with established patterns for navigation, input, status, and
  presentation. Customize when the product has a real reason.
- Keep equivalent controls consistent in wording, placement, appearance,
  and behavior across the product.
- Give feedback that identifies availability, progress, completion, and
  failure. Do not make people infer state from decoration.

## Design for flexibility

- Preserve meaning and context across viewport sizes, window resizing,
  orientation, input methods, locales, text expansion, and user settings.
- Support the simplest viable path for touch, pointer, keyboard, voice, and
  assistive technology when those inputs are in scope.
- Provide an explicit alternative for an important gesture or hidden
  interaction. Do not make core functionality gesture-only.
- Keep layout direction, date/number formats, text length, and localization
  in the design contract when the product is internationalized.

## Make it simple and legible

- Prefer clear, direct labels and a visible hierarchy over explanation
  hidden in tooltips or decorative copy.
- Group related content and controls; separate unrelated groups with space,
  alignment, or a meaningful surface change.
- Put essential information where reading and interaction begin. Use
  progressive disclosure for secondary detail, but signal that more exists.
- Use typography, spacing, and contrast to make relationships scannable.
  Do not use tiny type or low contrast to fit more content.

## Accessibility is part of the design

- Keep information available through more than one channel: do not rely on
  color, sound, motion, or a gesture alone.
- Use readable, scalable text; named controls; visible focus; sufficient
  contrast; and controls large and separated enough for the target input.
- Support keyboard and assistive-technology paths, and test them instead
  of treating labels or ARIA as proof of usability.
- Pair important audio with text or visual feedback where appropriate;
  provide captions, subtitles, audio descriptions, or transcripts for the
  relevant media.
- Respect reduced-motion and related user preferences. Avoid flashing,
  fast repetitive motion, autoplay, and time-limited content unless the
  task truly requires them and the user has control.
- Prefer explicit dismissal over auto-dismiss for information people may
  need time to read or operate.

## Craft without decoration

- Refine wording, spacing, states, transitions, and error recovery as one
  experience. Quality includes behavior, not only the first screenshot.
- Test realistic content, empty/loading/error/disabled states, long text,
  localization, assistive settings, and the smallest and largest supported
  contexts.
- Add personality where it reinforces the product’s purpose. Remove
  delight, effects, or materials that compete with the task.
- Iterate against real use. A polished static frame is not proof that an
  interaction is understandable, resilient, or accessible.

## Review gate

Before calling a UI change done, answer:

1. What is primary, and can people reach it without decoding the interface?
2. What feedback appears for waiting, success, failure, empty, disabled,
   and destructive states?
3. Can people recover, leave, undo, or use an alternative input path?
4. Does the layout survive supported sizes, text lengths, locales, and
   settings without losing hierarchy?
5. Can people perceive and operate it without relying on one sense or one
   input method?
6. Which details were tested in the real user path, and which remain
   unverified?

## Source

Distilled from Apple’s [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/),
including [Design principles](https://developer.apple.com/design/human-interface-guidelines/design-principles),
[Getting started](https://developer.apple.com/design/human-interface-guidelines/getting-started),
[Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility),
[Color](https://developer.apple.com/design/human-interface-guidelines/color),
[Layout](https://developer.apple.com/design/human-interface-guidelines/layout),
[Typography](https://developer.apple.com/design/human-interface-guidelines/typography),
[Materials](https://developer.apple.com/design/human-interface-guidelines/materials),
[Patterns](https://developer.apple.com/design/human-interface-guidelines/patterns),
[Components](https://developer.apple.com/design/human-interface-guidelines/components),
and [Inputs](https://developer.apple.com/design/human-interface-guidelines/inputs).
Pages fetched with Firecrawl on 2026-08-31. Re-check Apple’s pages for
current platform-specific guidance before implementation.
