<div align="center">
  <img src="assets/needquality.png" alt="needquality" width="780">
</div>

<h3 align="center">Small, focused guidance for reliable software changes</h3>

<p align="center">
  Use the skill when work needs less ceremony and more signal.
</p>

## What it is

NeedQuality is a routed agent skill for code and agent documentation. It maps
the user's request to one job, loads only matching references, keeps the
change small, and requires fresh evidence for claims.

## Why one skill

NeedQuality routes each request to one job and loads only matching references.
One entry point replaces manual skill selection and keeps scope, patch, and
proof consistent.

> [!IMPORTANT]
> This skill does not replace skills like [impeccable](https://github.com/pbakaus/impeccable) or [anti-ui-slop](https://www.skills.sh/site/uizze.com/anti-ui-slop) **fully**, though it is a way to improve results.

## How it works

1. **Scope** the named behavior and the boundary that can fail.
2. **Load** the matching job and references.
3. **Patch** the smallest reliable slice, reusing what is already there.
4. **Prove** the result with a fresh check and report what was verified.

## Coverage

Coverage counts overlap. They describe reference inventory, not a percentage
of every possible software topic.

| Area | Coverage |
| --- | --- |
| UI and design | 19 dedicated UI references |
| UX, accessibility, and operability | HIG, navigation, forms, states, motion, overlays, operability, accessibility, and UI-verification guidance |
| Languages and frameworks | JavaScript, TypeScript, Python, Go, Rust, SQL, Swift, React, React Native, Next.js, Vue, Docker, and Postgres |
| Workflow and process | 58 flow documents |
| Quality and delivery | 17 job documents |
| Evidence and testing | 96 tells, 24 evaluation cases, and 29 fixtures |
| Research and trust boundaries | Research routing, primary-source rules, outbound I/O, auth, and security guidance |
