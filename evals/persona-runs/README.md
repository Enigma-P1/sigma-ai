# Persona runs — SCRIPTED, SIMULATED, NEVER HUMAN RESULTS

> **THESE ARE SCRIPTED UNTRAINED-PERSONA RUNS, SIMULATED BY AN AI AGENT**
> per the 2026-08-07 owner ruling amending PLAN §9. They are **never to be
> presented as human results.** The personas are fictional characters
> constrained to an untrained user's knowledge; an AI agent scripted their
> choices and drove every form entry against the live engine.

## What this is

The M6 simulated untrained-persona evaluations of the two held-out
scenarios (S-1 Harborview help desk, S-2 Ashford library), per PLAN §9's
high-schooler test as amended by the owner ruling of 2026-08-07: "no
external humans will be sourced — the human bench is Shawn plus anyone he
chooses to involve," with the second leg being "scripted untrained-persona
runs — an agent constrained to an untrained user's knowledge, choices
logged — **always labeled as simulated, never presented as human
results**."

Each run invents one fictional character inside the scenario's story org,
gives them only (a) the scenario's story-facing facts, (b) what the app's
screens actually say, and (c) general high-school-graduate knowledge — no
Six Sigma training, no sight of the rubric, the traceability matrix, the
spec frontmatter, or the ground-truth section beyond what happens to them
in-story. The agent then plays that person through every in-scope tool
against the **live engine** (v0.1.0, run date 2026-08-08): real POSTs,
real refusals, real prescore flags. Mistakes an untrained person would
plausibly make are made, and recover only through what is on screen (or
through an in-story ask, which is logged as such).

## Method

- **Personas:** S-1 — Corey Lindqvist, IT operations coordinator at
  Harborview Mutual. S-2 — Becca Lin, part-time circulation assistant at
  the Marion Street branch. Both invented for these runs (the M2-era
  persona name was deliberately not reused).
- **Simulation discipline:** motivated, careful non-experts — not
  omniscient, not idiots. Where a step invited a plausible untrained
  mistake, the persona made it, and got out only via on-screen guidance
  (helper panels, prescore strip details, refusal texts, the Stuck
  button's decision tree) or a logged in-story ask.
- **Every number is real.** Every engine response quoted in the
  transcripts came back from a live call during these runs. Evidence
  projects on the engine: `persona-s1-corey` and `persona-s2-becca`
  (under the engine's projects root); the artifact version history in
  those projects is the audit trail of every draft, refusal, and fix.
- **Call volume:** 217 live engine calls total — S-1: 105 (87 main + 18
  continuation), S-2: 112. Four of those are deliberate 422 probes the
  personas triggered (S-1: fishbone verified-without-evidence, pilot
  bundle EXIT-10; S-2: bait-chart freeze below the floor, pilot bundle
  EXIT-10). Everything else returned 200.
- **What the agent did NOT do:** grade the runs (that is the external
  Belt panel's job, run by the director after these transcripts), touch
  the scenario specs, harness, or goldens, or let the personas see any
  answer-key material.

## Pass bar (PLAN §9, quoted)

"Pass bar: every phase scores 'acceptable Green Belt work' or better, with
**usability failures and validity failures logged separately** — a
confusing screen and a wrong analysis are different bugs." And: "a stall
inside the suite's guidance is a v1 bug, a stall outside its stated scope
goes to the failure log for a scope ruling." S-2 additionally carries the
named-exit requirement: "one held-out scenario deliberately requires a
named exit … recognizing the exit is part of the pass bar, so honesty
paths get graded, not just the happy path." Scoring is by the shipped
Green Belt rubric, applied by the external-model Belt panel plus the
in-app grader — **not by this simulation**. These transcripts end at
faithful runs plus the failure log.

## The two runs at a glance

Run-level outcome facts only — rubric grading belongs to the Belt panel.

| | S-1 (Corey Lindqvist) | S-2 (Becca Lin) |
|---|---|---|
| Project id on engine | `persona-s1-corey` | `persona-s2-becca` |
| In-scope tools completed | 21 of 21 | 22 of 22 |
| Phases completed | Intake through Wrap, project closed | Intake through Wrap, project closed |
| Live engine calls | 105 | 112 |
| Engine refusals (422) hit | 2 (T-15 no-evidence, T-19 EXIT-10) | 2 (T-21 freeze floor, T-19 EXIT-10) |
| Hard blocks hit | none (T-12 passed first try) | 1 — EXIT-02 gate HARD_BLOCK after T-12 round 1 |
| Stalls, self-recovered via on-screen guidance | 4 | 3 |
| Stalls recovered via in-story ask | 1 (clock-stop rule, asked Naomi) | 0 |
| Hard stalls (unrecovered) | 0 | 0 |
| Named exit | n/a (`named_exit: null`) | **EXIT-02 fired, recovery executed, baseline on audit data** — the honest path |
| Final honest close | Goal met (104.2% of gap), 35.5% per-ticket tail named open | Goal met (121.7% of gap), after-Pareto remainder named open |

**S-2's trap, in one line:** Becca tried the bait first — imported it,
ran it at T-13, tried to freeze a p-chart on it — and the suite caught
her in three real layers (the 20-point freeze floor's 422, the Stuck
button's "has the measurement system itself been checked?" leaf, and
EXIT-02 + the hard gate once T-12 ran). The chain's one soft link —
nothing forces a user who never stalls into T-12 at all — is failure-log
entry FL-07.

## Files

- `s1-corey.md` — S-1 run transcript (per-phase, choices logged, engine
  responses quoted, stalls classified).
- `s2-becca.md` — S-2 run transcript, with the trap sequence documented
  step by step.
- `failure-log.md` — the consolidated task-level failure log: usability
  vs validity vs scope-ruling, severity, the screen text involved, and a
  fix direction per entry.

Machine-readable YAML header at the top of each transcript carries
`scenario_id`, `persona`, `simulated: true`, `engine_version`, `date`,
and `project_id`.
