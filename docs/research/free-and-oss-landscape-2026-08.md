# Free / open-source LSS landscape check — 2026-08-04

Follow-up to the April commercial research, aimed at the new question: Green
Belt in a Box ships as a **free open-source showpiece** — what free/OSS
neighbors exist, and what should we learn from them?

## Nearest neighbors

**DMAIC.io** — the closest thing to our Layer 1 that exists. Open source
(AGPL-3.0), free forever, browser-based with downloadable offline HTML,
built by a German Black Belt (Dr.-Ing. Tobias Meisch). Real deterministic
stats, not templates: capability (Cp/Cpk/Pp/Ppk), Gage R&R, hypothesis
tests, normality, DOE/factorials, full SPC family with rule detection, plus
8D and TRIZ. What it is NOT: a coach. It's a toolbox for people who already
know the tools — its own positioning is "Green Belt to Master Black Belt."
No guided project flow, no teaching layer, no worked examples, no rubric or
tollgates, no AI.

**lean-ai-ops (GitHub, simaba)** — a 2-star MIT prototype of almost exactly
our concept: Claude-powered DMAIC assistant + stats workbench (capability,
MSA, hypothesis tests, SPC, FMEA, regression, DOE guidance), with a
deterministic no-API-key fallback. Self-described "working prototype, not a
finished product." Proof the idea is in the air; nobody has executed it at
showpiece quality.

**BlueSky Statistics** — free OSS statistics app with Six Sigma + DOE
modules. A Minitab substitute for people who know statistics; no guidance.

**Template packs** — GoLeanSixSigma, Smartsheet, Qualica (Excel stats
templates: normality, MSA, capability), CSSC's free full Green Belt manual
PDF. The incumbent "free LSS" world: disconnected files. You assemble your
own project; nothing connects charter → data → analysis → control.

**Free AI coaches** — custom GPTs (Lean Six Sigma Coach GPT, Green Belt
Prep GPT), Six Sigma Institute's AI assistant. Generic chat: no data
access, no artifacts, no grounding — the "ton of output to sort through"
failure mode our structured-context advisor exists to avoid. Visual
Paradigm's free AI charter generator (April research) is the same category.

## Read on the market

Every free neighbor has exactly one of the three pieces — stats toolbox
(DMAIC.io, BlueSky), templates (GLSS/Smartsheet/Qualica), or chat (GPTs).
Nobody connects them into a guided project with a teaching layer, graded
artifacts, and a grounded advisor, and nobody aims at the untrained user.
The differentiation sentence for the README: *toolboxes exist for people
who already know Six Sigma; this carries someone who doesn't through a
whole real project.*

## What we adopt from this

1. **License: Apache 2.0 — ruled by Shawn 2026-08-04** (chosen over the
   MIT recommendation and over AGPL). Permissive with explicit patent
   language; DMAIC.io's AGPL scares off exactly the evaluator audience a
   portfolio piece wants reading the code.
2. **DMAIC.io validates the offline-HTML distribution path** — de-risks the
   stlite fallback in PLAN.md §7 if the clean-machine gate fails.
3. **Extra cheap cross-check:** benchmark our stats outputs against
   DMAIC.io and the Qualica Excel templates alongside the NIST reference
   values in M2 goldens.
4. **README comparison table** (us vs. toolbox vs. templates vs. chat) —
   honest, names the neighbors, states what each is good at. Confidence,
   not marketing.

Sources: dmaic.io · github.com/topics/lean-six-sigma ·
github.com/simaba/lean-ai-ops · airacad.com free tools · goleansixsigma.com
· smartsheet.com LSS templates · qualica.net Excel templates ·
sixsigma-institute.org AI assistant · blueskystatistics.com
