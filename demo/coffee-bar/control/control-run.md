# Control run — the recorded engine verdicts, through the clean close

Not an artifact: the recorded engine runs of the Control phase and the
wrap, continuing `improve-run.md` in the same project
(`coffee-bar-demo-ic`). Every artifact in this folder was POSTed to the
live engine and accepted (200); `control-chart.json`, `control-plan.json`,
`five-s.json`, and `a3.json` are the engine's own echoes (frozen limits,
check-in verdicts, trend, tollgate stamps, close check — all
server-computed), `standard-work.json` validates with nothing computed to
echo, and `copq-wrap.json` ships input-side like `define/copq.json`, its
engine totals recorded here.

## T-21 — the freeze, and what stayed a spec line

`POST /artifacts/T-21/validate` with `freeze_requested: true`, then saved
v1; the stored artifact was loaded back and its frozen numbers match the
validate echo bit for bit. The selector routed continuous data to I-MR;
the freeze window is the round-2 dataset itself (120 points, already
engine-verified signal-free in `improve-run.md`, so the ≥20-point
no-signal freeze floor clears six times over). The engine's frozen
baseline, pasted:

- **center (x̄) 4.8992**, MR-bar 0.7034, **σ_within 0.6235**
- **individuals limits 3.0285 / 6.7698**, MR chart 0 / 0.7034 / 2.2979
- signals against the frozen limits over the current data: **0**
- recalculation log: one entry — `initial freeze, 2026-09-22T09:00:00Z`
- armed: `monitoring_started: true`, daily peak entry cadence

The one-shot triggers came back consumed (`freeze_requested: false`,
`action_at: null`) — from here, new points are judged against these
limits and never reshape them; the only path to new limits is a logged
`recalculate_reason`. The customer's 5.0 is nowhere in the artifact's
limit fields, deliberately: it is a spec line, the chart's band is what
the process is doing, and the two sentences stay different — this process
is in control and ~44% of its orders are out of spec, both true at once.
Prescore: all five checks pass (`family_matches_data`,
`frozen_limits_present_before_signals`, `never_armed` pass-as-armed,
`signal_acknowledgment_completeness` with no signals yet,
`recalculation_log_has_reasons`).

## T-22 — the control plan, check-ins scored against the frozen band

`POST /artifacts/T-22/validate`, saved v1. Three monitored items — the
primary CTQ (daily, against the frozen chart), the remake-rate guardrail
(weekly roll-up), and the changed method itself (twice-weekly unannounced
spot-check) — each with a stated frequency reason and a named owner who
accepted on the 2026-09-22 handoff walk. Every OCAP's first response is
investigate-the-method before touching anything, and the steps name the
two changed methods (batch-steam/sequencing, grinder dial-in/swap) because
those are what can silently lapse. Four training rows point at the T-24
SOP by artifact id, all verified by observed demonstration and signed off
2026-09-24 → 2026-10-01. The engine's computed readouts, pasted:

- `plan_health`: ownerless items **[]**, unaccepted owners **[]**,
  `is_theater: false`, check-in not overdue ("next check-in due
  2026-10-12, not yet due as of 2026-10-09T17:00:00Z")
- `next_due`: **2026-10-12** — start date advanced by exactly two
  completed weekly steps, computed, never typed
- check-in `ci-1` (due 2026-09-28, answered same day): **pass** — "all 8
  entered value(s) hold inside the frozen band [3.029, 6.77]"
- check-in `ci-2` (due 2026-10-05, answered same day): **pass** — "all 10
  entered value(s) hold inside the frozen band [3.029, 6.77]"

Prescore: all nine checks pass — `owner_named`, `owner_accepted`,
`owner_not_placeholder` (every owner is a named person, not a "TBD"/"the
team" placeholder — the M6 fidelity-panel addition),
`frequency_reason_present`, `ctq_and_fix_coverage` (the plan covers the
CTQ and what Improve changed), `ocap_coverage`, `ocap_elements_complete`,
`training_verification_present`, `check_in_overdue`.

## T-23 — the 5S rounds and their photos

The three photos were uploaded through the floor-plan image store
(`POST /project/{id}/floorplans`, the same route and PhotoRef shape the
spaghetti diagram uses) and the returned image ids / sha256 hashes are the
ones `five-s.json` carries; the PNG files sit in this folder
(`five-s-round1.png` … `round3.png`), stdlib-rendered stand-ins in the
`measure/floorplan.png` convention — plain zlib/struct PNG writing, clutter
placement seeded with `random.Random(23)`. Then
`POST /artifacts/T-23/validate` and saved — v2 in the store, the original
save plus one notes-wording revision, every save versioned. The engine's
trend, pasted:

- 2026-09-23 — total **10**/25, lowest `set_in_order` (1: pitchers across
  the walkway, tools scattered, cups behind the barista)
- 2026-10-07 — total **15**/25, lowest `sustain` (2: round 2 happened
  only after a calendar chase)
- 2026-10-21 — total **18**/25, lowest `standardize` (3: the dial-in log
  still migrates)

Improving and honest — nothing is a 5, every round's lowest category
carries an owned action, and the set-in-order moves land on the spaghetti
finding (~796 m walked per peak; R2's 52 grinder trips; the crossing
where the July 28 pileup happened). Prescore: all five checks pass,
including `uniform_scores_honesty` (no reflex rows) and
`recurrence_present` (schedule + 3 trend points).

## T-24 — the improved method written down

`POST /artifacts/T-24/validate`, saved v1. Seven steps seeded from the
process map's walk (s1–s5), each an action plus an observable standard;
the four steps the pilots changed are marked `changed_from_prior` — the
sequencing rail (st-2), the pair scan (st-3), the batched build (st-4),
and the grinder dial-in/swap (st-5) — so a trainer can find exactly what
is new. Unchanged step standards thread to the time study's element
medians (order 0.8, finish 0.6, handoff 0.5) and the 2.0-minute prepare
standard; the FMEA's severity-8 steam-scald action lives in st-4's
standard as purge-and-park outboard, not in a memo. v1, owner Priya Shah,
effective 2026-09-22, supersedes the 2024 laminated card (taken down the
same day — one method, one source), linked to the control plan whose
training rows point back at it. Prescore: all four checks pass
(`step_schema_present`, `metadata_present`, `changed_steps_marked`,
`steps_read_as_actions`).

## T-02 re-run — money over a stated window

`copq-wrap.json` (`coffee-copq-wrap`) validated and saved v1 — the wrap
COPQ re-run rubric R-WRAP-02 asks for, same four categories and rates as
the Q2 baseline run so money compares to money, quantities from the
window's actual logs. Window: 2026-09-22 → 2026-10-16, the first 4 weeks
after the round-2 rollout, 19 weekday service mornings. The engine's row
amounts and total, pasted:

- rework: 70 × $1.10 = **$77.00** (waste-sheet remakes, ~2.3/100 at
  semester volume)
- comped drinks (long-wait apologies): 9 × $4.80 = **$43.20** (POS comp
  log, reason "wait" — down from ~65 per equivalent 4 weeks in Q2)
- lost business: 19 × $5.25 = **$99.75** (walk-away tally ~1/morning vs
  Q2's 6 — still the one honest estimate row)
- overtime: 2.0 × $16.50 = **$33.00** (time clock, ~0.1 h/morning vs
  Q2's 0.65)
- **engine total: $252.95** against the Q2 baseline pro-rated to an equal
  4 weeks: $4,021 × 4/13 = **$1,237.23**

The pro-rating is named as an assumption wherever the delta is used (Q2
was summer; this window is semester, ~15% busier — a bias that
understates the recovery, not one that inflates it).

## T-25 — the A3, the tollgates, and the live close check

`POST /artifacts/T-25/validate`, saved (`a3.json` is the echo, with
the engine-stamped tollgate questions and all computed closure blocks).
Eight panels, each seeded from its source artifact and rewritten as
sponsor prose with the numbers untouched — the results panel keeps both
riders (the semester confound sentence and the Cpk 0.054 capability
caveat) exactly as the round-2 proof printed them. The engine's computed
blocks, pasted:

- **Realized benefits** (from `coffee-copq-wrap`, window stated):
  realized_to_date = 1,237.23 − 252.95 = **$984.28**; net of the $360
  fix cost (round-1 pitcher/labels $40 + refurb grinder $300 + cards
  $20) = **$624.28**. The $12,795.64 annualized figure is entered as
  `annualized_projection` with its schema-required
  `annualized_projection_basis` stating the method on the artifact
  itself: the window's realized recovery ($984.28 per 4 weeks) × 13
  four-week windows/yr — equivalently the quarter's proportional
  recovery ($3,198.91) × 4 — assuming semester demand and the improved
  rates hold, the before side itself the Q2 baseline pro-rated 4/13. A
  bare projection with no stated basis cannot save (the engine refuses
  it, rubric R-WRAP-02's "projection presented without its basis"), and
  the charter's original $16,084 is never claimed as realized.
- **Objectives vs charter** (proof.compute_gap, reused verbatim):
  original gap 3.4083, recovered 3.5092, remaining **−0.1008**,
  `goal_met: true` — "Goal met — route to Control." Consistent with the
  Improve conclusion by construction, not by cross-check.
- **Tollgates:** all six phases stamped with the engine's questions, all
  eighteen answered with evidence refs — including the honest ones
  (Define-1 names the failed first charter draft; Improve-3 states the
  43.9% still over the line).
- **The close check, run live:** the linked FMEA's computed
  `blocking_flags` came back **empty** — the severity-8 steam-scald row
  carries its action (now st-4's purge-and-park standard in the SOP),
  and no severity-9/10 row exists — and the server-side sweep of the
  project's saved artifacts found **no standing prescore hard_flag**
  (`standing_hard_flags: []`, the M6 fidelity-panel addition: an
  unresolved deterministic finding anywhere in the project blocks
  closure the same way a sev-9 row does), so `close_blocked: false`:
  "No unaddressed severity-9/10 safety/regulatory row on the linked
  FMEA, and no standing prescore hard_flag on the project's saved
  artifacts — this check does not block closure." With the check clean,
  `project_status: "closed"` validated instead of raising — the same
  validator that would have refused to close past a live safety block.

Prescore: **all six checks pass** — `panels_seeded_or_narrated`,
`realized_benefits_present`, `tollgates_answered`, `lessons_substantive`
(three lessons, two genuine went-wrongs), `open_items_have_owners` (four
items, four named owners), and `close_blocked_surfaced` reporting the
clean close. Closed 2026-10-28, three days ahead of the charter's
control-plan milestone.

## Teaching read

Control is where real projects go to die — the research this product is
built on puts control-phase tools at ~6% of real-world usage — and this
phase is built as a set of mechanisms that outlive enthusiasm. The limits
froze once, from a window the engine verified, and the freeze is the
alarm: drift now has something fixed to drift away from. The plan monitors
the fix, not just the number, so a lapsed method gets caught before the
chart has to catch it. The check-ins are scheduled and scored by the
engine against the frozen band, so "is it holding?" has a computed answer
on a calendar instead of a feeling. The SOP is the one source the training
rows point at, with the changed steps marked. And the close is honest in
both directions at once: the project may close — the safety row carries
its action, the goal is met on the mean, the money is stated on a window
with its assumptions named — and what is not finished (the every-order
promise, Cpk 0.054) leaves in writing, with owners, instead of leaving
quietly.
