# Ready-made example project — everything already filled in

`coffee-bar-example-project.zip` is a complete, finished Coffee Bar project:
all 25 tools filled in, both datasets embedded, charts and stats ready to
look at. Drop it in and open it — nothing to type.

Use it to see what good output looks like before (or instead of) typing a
project yourself. It is the same worked example the docs and tests use.

## Install it

**Windows**

1. Download `coffee-bar-example-project.zip` from this folder on GitHub
   (click the file, then the download button).
2. Open File Explorer and paste this into the address bar:
   `%USERPROFILE%\.sigma-ai\projects`
   (If the `projects` folder doesn't exist yet, launch Sigma AI once and
   create any project — that makes it.)
3. Right-click the zip → **Extract All…** → extract it into that folder.
   You should end up with `...\.sigma-ai\projects\coffee-bar-example\`
   containing `project.json` and an `artifacts` folder. If you instead get
   `...\projects\coffee-bar-example-project\coffee-bar-example\`, move the
   inner `coffee-bar-example` folder up one level.

**Mac**

Same idea: unzip into `~/.sigma-ai/projects/` (in Finder, press
`Cmd+Shift+G` and paste `~/.sigma-ai/projects`).

## Open it

In Sigma AI, click **Open a project**, then:

1. Find the field labelled **Or open by project ID**.
2. Type `coffee-bar-example`.
3. Click **Open**.

No restart needed.

**It will not appear in the list above that field.** That list is a
recently-opened history kept per machine, not a scan of your projects
folder — a project you dropped in by hand has never been opened here, so
it is not in the history. Typing the ID once is what puts it there; after
that it shows up in the list like any other project.

If **Open** reports it can't find the project, the unzip nested one level
too deep. Paste `%USERPROFILE%\.sigma-ai\projects\coffee-bar-example` into
File Explorer's address bar (`~/.sigma-ai/projects/coffee-bar-example` on
Mac) — you should land in a folder with `project.json` sitting directly
inside it. If that path doesn't exist, go up to `projects` and move the
inner `coffee-bar-example` folder up one level.

## How it's built

`make-example-project.py` in this folder turns a golden-harness Coffee Bar
run into the zip. It exists because the two writers name artifacts
differently: the harness uses scenario-scoped ids (`coffee-charter`) that are
frozen into golden files, while every tool form in the app loads one
hardcoded id (`charter`). Ship the harness output directly and you get a
project whose rail says **Done** beside all 22 tools while every form renders
blank and says *Not saved yet* — which is exactly what the first cut of this
zip did. The script does the translation, rewrites the cross-references that
ride along with it, and collapses the three tools that were run twice (COPQ,
pilot, proof) into v1/v2 of one artifact instead of dropping either.

`desktop/tools/example-project-probe.mjs` is the check: it opens this zip in
the real production bundle and fails if any tool renders empty or is missing
known content from the worked example.

## What's inside

The full DMAIC thread, engine-computed throughout:

- **Define** — picker routed to full DMAIC, charter (8.4 → 5.0 minutes),
  COPQ totalling $4,021/quarter, SIPOC, VoC → CTQ tree
- **Measure** — process map, spaghetti diagram, check sheet, time study,
  yield calculator, collection plan, measurement check, baseline
  (mean 8.41, stable, Cpk −1.14 — predictable and predictably bad),
  Pareto/histogram/run charts
- **Analyze** — fishbone with evidence-backed verified causes, FMEA,
  hypothesis test (a real result that comes back "significant but minor")
- **Improve** — solution matrix, two pilot rounds, before/after proof with
  the remaining-gap loop
- **Control** — frozen I-MR control chart, control plan, 5S audit,
  standard work
- **Wrap** — A3 with tollgates, closed cleanly

Two datasets ride along (`wait-times.csv`, the check-sheet export), so the
baseline and chart screens work immediately with no import step.

## Notes

- It opens as a **closed** project (the A3 was completed). Everything is
  readable; if you want to edit, re-open the phase you want from the rail.
- Editing it changes only your copy. To start over, delete the
  `coffee-bar-example` folder and unzip again.
- Your own projects live beside it in the same `projects` folder, one folder
  each, plain JSON — copy or back them up like any other files.
