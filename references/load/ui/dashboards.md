# Dashboards

Read from [ui.md](../ui.md) when the patch is an app home,
analytics, or "overview." Job: **operate**. A dashboard is a car
dash: glanceable status for *this* task, not a landing page.

## Tells

| Tell | Fix |
|---|---|
| Collapsible sidebar + header search/bell + **four** KPI cards | One real number this screen is for, or skip |
| Recharts `{ name: 'Jan', uv: 400 }` | Real series or no chart. [charts.md](charts.md) |
| "Welcome back" hero in an app | Title of the task |
| Glass nav / three feature cards / marketing hero | Landing stencil on the wrong job |
| Pie / donut / gauge as the primary number | Length or position (bar/line). Number + unit in type |
| Everything on one canvas: table + form + export + chart | One primary action. Rest behind a link or `<details>` |

## Why

NN/G (*Dashboards: Making Charts and Graphs Easier to
Understand*): operational dashboards answer "am I over the
limit?" in one glance; analytical ones flag "look here next."
Neither is exploration. Preattentive cues that *quantify* well
are **length** and **2D position**. Area, angle, and color-as-
magnitude do not.

Cleveland & McGill (1985), cited there: people compare bar
length accurately; they do not compare pie slices. Few
(*Information Dashboard Design*): one screen, no chart junk, no
gauges that waste space to show one number.

Dashboard layout-order study (PMC11435723): clutter and
symmetry-for-its-own-sake raise rated complexity. Four equal
KPIs is that clutter. Text on dashboards is not caption filler —
it is instruction vs insight (pmid:39255127 / arXiv:2407.14451).

Nielsen heuristic #8 (minimal): extra widgets compete. Heuristic
#1 (visibility of status): one honest number beats four fake
ones.

## In this patch

1. Name the question the screen answers in one sentence.
2. Put that number in type, then optionally a bar/line of the
   same data.
3. Density: [space.md](space.md). States: [states.md](states.md).
4. Dark only if the product already has it. [color.md](color.md).

## Sources

- [NN/G: Dashboards, preattentive](https://www.nngroup.com/articles/dashboards-preattentive/)
- Cleveland & McGill, *Graphical Perception* (1985)
- Stephen Few, *Information Dashboard Design*
- Edward Tufte, *The Visual Display of Quantitative Information*
- PMC11435723 (layout order / complexity)
- pmid:39255127 (text on dashboards)
