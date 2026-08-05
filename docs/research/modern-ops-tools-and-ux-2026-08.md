# Modern ops tools + modern UX — research synthesis, 2026-08-04

Two parallel sweeps run at Shawn's direction before build start: (A) what
LSS/CI tools operations practitioners actually use in 2025–2026, checked
against our tool list for gaps; (B) how modern software presents the
classics, spaghetti-diagram tech, and whether Streamlit can deliver "slick."
Full agent outputs with ~75 sources ran in-session; key findings below.

## A. What practitioners actually use (and don't)

**Most-used, by evidence:** process mapping (~91% in benchmark surveys),
check sheets (~94%), Pareto + fishbone (the preferred analytical pair),
5 Whys (the daily-driver RCA), run charts/histograms, control charts
(universal in manufacturing), 8D (the de facto container framework in
mfg/supplier contexts), FMEA and capability in manufacturing quality.

**Low real-world usage (validated):** Gage R&R/MSA, hypothesis testing, and
DOE — "few practitioners use" them per survey data. Charters: used by <25%.
Tollgate bureaucracy is the #1 practitioner complaint about DMAIC.
Implication: keep our rigor tools, but they must be fast and never feel like
ceremony — the MSA walkthrough is minutes not hours; tollgates stay
self-serve. The Improve phase is under-tooled in practice (77 Measure tool
mentions vs 29 for Improve in survey data) and Control is the most-abandoned
phase (6% of tool usage) — our improvement loop and a control-phase
follow-up mechanism attack real weaknesses, not imagined ones.

**Automation-era, mainstream vs not:** mobile audit/checklist apps
(SafetyCulture-class) are genuinely mainstream down to SMB; connected-worker
platforms are mid-market mfg mainstream; process mining ($300–500K/yr
Celonis TCO), computer-vision time studies, and RTLS/UWB digital spaghetti
are enterprise-only — worth explain-only mentions, not building. AI-copilot
DMAIC is the 2025–26 narrative and is exactly our thesis.

**Spreadsheet pain (what to attack):** manual follow-up chasing, data
fragmented across files, no audit trail, and silent inaccuracy (manual Excel
OEE runs 8–12 points optimistic vs measured reality). The failure mode isn't
math — it's that nobody chases the next step. Our pilot loop + scheduled
control check-ins are the answer spreadsheets can't give.

## B. Tool-list gaps found (Shawn's "another spaghetti diagram" check)

Recommend-add for v1: **check sheet / tally tool** (2nd most-used tool in
the field; feeds Pareto automatically), **COPQ / project-benefit
calculator** (dollars are the language leadership hears), **FPY/RTY yield
calculator** (alongside DPMO), **5S audit as a scored checklist** (promote
from explain-only; the most-digitized lean activity at SMB), **guided time
study / work sampling** (phone-as-stopwatch observation; warehouse-native),
**control-phase check-in scheduler** (extends OCAP with recurring
pass/fail check-ins — fixes the abandoned-Control problem), **PDCA
quick path** (lightweight track for small problems that don't warrant full
DMAIC — reduces abandonment). v1.1: 8D report as an export skin over
existing data, takt time + line balancing, guided OEE calculator, scatter
plot. Keep VSM explain-only (swimlane + wastes covers the need for this
audience).

## C. Modern UX of the classics — patterns to steal

From Minitab Workspace/Engage, eVSM, Miro/Lucidchart, Celonis, DMAIC.io:
1. canonical template pre-drawn, user fills slots (fishbone spine + 6M bones
already placed — instant Black Belt recognition); 2. **shapes carry data,
tools share one project data model** (the process map's Xs flow into
C&E/FMEA); 3. live recalculation on the diagram; 4. guidance docked beside
the tool; 5. metrics encoded visually (line thickness = frequency, color =
duration); 6. pan/zoom canvas with drag-drop and auto-routing connectors.
Whiteboard tools are dumb drawings (no math); purpose-built suites are
desktop-era. Linked-data + live-recalc + modern canvas is the open lane.

## D. Spaghetti diagram — the flagship modernization

State of the art is thin: the free tier (Kaizumi, eVSM module) traces paths
and computes distance; **nobody free does heatmaps or before/after
comparison** — open field. Enterprise RTLS/CV versions define what "modern"
output looks like: heatmaps, time-in-zone, playback.

Recommended feature set: upload a floor-plan image (or photo of a paper
sketch) → calibrate scale by drawing one known-length line → trace routes
per operator/trip (click-to-polyline or freehand) → live metrics panel
(distance per trip, trips, crossings, est. walk time, distance × frequency
= daily travel burden) → **heatmap toggle** → **before/after layout mode
with delta metrics** → animated playback for demos → PNG + CSV export.

**Tech verdict: 2D, not three.js.** A spaghetti diagram is intrinsically a
top-down plan view — that IS the recognizable artifact; 3D adds camera
controls and modeling cost while destroying recognition. Konva.js
(layered canvas: plan / objects / traces / heatmap, built-in drag-drop,
strong React binding, best-in-class performance) over Fabric.js. Heatmap is
~100 lines of canvas technique, no library. An optional 2.5D tilted view can
come later as a flourish. This satisfies "slick" without the three.js hill.

## E. Stack verdict — the big finding

Streamlit is fast and fine for guided forms + stats + Plotly (~80% of the
app) but has a hard interactivity ceiling for canvas/diagram tools: full
rerun on every interaction, iframe-sandboxed components that can't drive the
rest of the page, and the community drawing component is stalled/buggy.
Building the marquee tools (spaghetti tracer, process map, fishbone canvas)
means writing custom React components anyway — inside Streamlit's
constraints instead of free of them.

Recommendation (decision for Shawn): **Python stats engine (FastAPI,
scipy/statsmodels — unchanged) + a real web frontend (React + Konva +
Plotly.js), shipped as a single-installer desktop app (Tauri with a
packaged Python sidecar).** No interactivity ceiling, and a *better*
install story than pip (double-click installer, no Python on the user's
machine — strictly better against the clean-machine gate). Cost: a real
frontend codebase, medium-high build effort. Fallbacks if build budget
rules: stlite+Electron (best install in the Streamlit family, same
interactivity ceiling) or Streamlit v1 accepting clunkier diagrams.

## F. Chart modernization checklist (applies regardless of stack)

One-line plain-English verdict headline on every chart ("stable but not
capable: Cpk 0.87 vs target 1.33"); annotations anchored to the data
("point 14 broke Rule 1 — investigate this shift"); signals colored, noise
muted; σ-zones as soft shaded bands; hover tooltips carrying full context;
capability plots with shaded out-of-spec tails and % printed; Pareto with
vital-few highlighted to the 80% line; one design system across all tools
(one type scale, muted-plus-accent palette) so twenty tools read as one
product; light/dark; PNG export at tollgate-deck resolution.
