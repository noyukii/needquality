# Web templates

Read from [ui.md](../ui.md) for any new web page, docs site, theme,
template, component, story, or component-library package. Job:
**baseline**. Templates reduce blank-page invention while leaving the
product's content, branding, and required behavior to the task.

## Selection order

1. Existing repository template, starter, sibling pattern, primitive,
   registry block, or story/example.
2. Official framework, component-library, or theme starter/template.
3. Smallest native scaffold supported by the existing stack.

Inspect the chosen baseline and adapt it in place. Keep its useful
semantics, composition, responsive behavior, and state structure. Do
not copy placeholder branding, content, people, or a template's visual
identity into the product without evidence.

An explicit request for a custom implementation may bypass this order.
Still apply [ui.md](../ui.md), the installed kit's documented API, and
the relevant accessibility patterns. If no baseline fits, use the
smallest native scaffold and say why in the closeout.

## Documentation sites

For MkDocs, use the existing `mkdocs.yml` and installed theme as the
baseline. For a new site, start with `mkdocs new` or the official theme
starter. Make ordinary changes with theme configuration,
`extra_css`, `extra_javascript`, or `custom_dir`/overrides. Build a
theme from scratch only when the user asks for custom work or the
existing theme cannot express the required contract.

For another documentation framework, use its installed theme and
official starter/extension path after checking the version in the repo.

## Component libraries

Before writing a component, inspect the package exports, nearest
component, design tokens, compound/slot pattern, registry, and story or
example template. Compose existing primitives before creating a new
one. Preserve accessible names, focus behavior, keyboard interaction,
loading/empty/error/disabled states, and the library's public prop
conventions. Do not clone a kit primitive or add a forwarding wrapper
that has no interface of its own.

New component-library code is web UI even when its change is described
as an API, refactor, or behavior change: the rendered contract and its
operability remain in scope.

## Sources

- [MkDocs: Customizing Your Theme](https://www.mkdocs.org/user-guide/customizing-your-theme/)
- [MkDocs: Developing Themes](https://www.mkdocs.org/dev-guide/themes/)
- [Material for MkDocs: Creating Your Site](https://squidfunk.github.io/mkdocs-material/creating-your-site/)
- [Material for MkDocs: Customization](https://squidfunk.github.io/mkdocs-material/customization/)
- [W3C: WCAG 2.2](https://www.w3.org/TR/WCAG22/)
- [W3C: ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [Vercel: Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines)
