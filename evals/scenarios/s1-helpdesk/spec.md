---
scenario_id: S-1
title: "Harborview Mutual — routine-ticket resolution time at the internal IT help desk"
data_type: continuous
eval_mode: plan_quality_only
named_exit: null
in_scope_tools: [T-01, T-02, T-03, T-04, T-05, T-06, T-08, T-11, T-12, T-13, T-14,
                 T-15, T-16, T-17, T-18, T-19, T-20, T-21, T-22, T-24, T-25]
na_tools:
  T-07: "No movement component: the work is queue-and-keyboard; no verified or candidate cause involves physical travel, so a spaghetti diagram would map nothing."
  T-09: "The ticket system timestamps every stage of every ticket; the baseline extract already carries the element times a stopwatch or work-sampling study would re-collect."
  T-10: "Continuous-metric project: T-13's baseline already reports the model-based DPMO/sigma readout; there are no per-step pass/fail counts or opportunity structure for T-10 to tally."
  T-23: "No workplace-organization component: the queue is digital, and no cause pointed at physical clutter or layout."
datasets:
  baseline: data/tickets-baseline.csv
  after: data/tickets-after.csv
  measurement_check: data/msa-repeats.csv
  delay_tallies: data/delay-tallies.csv
ground_truth:
  sponsor: {name: "Victor Braun", role: "IT manager (sponsor)"}
  owner: {name: "Naomi Castillo", role: "help desk lead", accepted_control_plan_on: "2026-10-12"}
  spec_limit: {usl: 8.0, lsl: null, basis: "IT service-catalog promise: routine requests resolved within one business day (8 business hours)"}
  goal: {metric: "mean resolution time, routine (P3) tickets", unit: "business hours", baseline_mean: 26.71, target_mean: 8.0, deadline: "2026-10-31"}
  change:
    what: "Assign-on-arrival dispatch rule (one change): kill the once-a-day triage batch; each new routine ticket is assigned within the hour by a rotating dispatcher-of-the-day"
    live_on: "2026-09-07"
    threshold: {value: "after-window mean <= 12.0 business hours", declared_on: "2026-09-03"}
    falsification: "two settled weeks above 12.0 -> revert to batch triage and take the next-ranked cause"
  confound_declared: {what: "fall onboarding class of 14 new hires starts 2026-09-21, inside the after window", direction: "adds access-grant volume; can only push resolution times up — it can mask the win, never manufacture it"}
  implementation_window: {bedding_in: "2026-09-07 to 2026-09-11, excluded by declaration", measured_after_window: "2026-09-14 to 2026-10-09"}
  after_data: "data/tickets-after.csv — 124 tickets, the full measured after window, same operational definition and extraction procedure as baseline"
  beyond_pilot: "dispatch rule made standing practice 2026-10-12; pre-approved access matrix for standard roles scheduled November 2026 (graded as plan quality per rubric §10.7a, never as accomplished fact)"
  benefits_basis: "realized-to-date over the 4-week after window; any annual figure must be labeled projection with its basis stated"
---

# S-1 — Harborview Mutual: routine-ticket resolution time (continuous / cycle time)

## What this scenario is

One of the two held-out golden scenarios PLAN §9 names: a complete DMAIC
project **in spec form** — the story, the problem, the pre-collected data,
and the scenario ground truth — that an eval run drives through the suite
with no other inputs. It is eval reference material, not a shipped demo: it
must never appear as an in-app example, because the moment a runner has
seen the answer key the run measures memory, not the suite. The continuous
data path is the point here (I-MR, one-sided capability, Welch t): a
different domain from the Coffee Bar demo so a runner cannot pass by
imitating the demo's shape. This scenario contains **no deliberate trap**
(`named_exit: null`) — the honesty trap belongs to S-2 — but every honesty
rule still applies: the measurement check runs before the baseline, the
stability verdict gates the capability language, and the declared confound
rides the proof.

## The story

Harborview Mutual is a ~380-person regional insurance office. Its internal
IT help desk — lead **Naomi Castillo**, techs **Ben Okafor**, **Lena
Fischer**, and **Marco Diaz** — handles routine "P3" requests: password
resets, software installs, and access grants. The published IT service
catalog promises routine requests resolved **within one business day (8
business hours)**. Nobody believes the promise anymore: staff open a ticket
and then walk to the desk anyway, managers email Naomi directly to jump the
queue, and a June spot-pull of 15 closed routine tickets averaged about 26
business hours (SD ≈ 6.5). IT manager **Victor Braun** sponsors the
project after the Q2 employee survey names "IT turnaround" its top
irritant.

How the desk actually works at baseline: new tickets land in one shared
queue. Naomi triages the queue **once each morning** — anything arriving
after ~9:30 waits until the next morning to be assigned at all. Access
grants additionally need a manager's approval, which is requested only when
a tech first touches the ticket. The techs are not idle and they are not
the problem; the queue discipline is. HR coordinator **Hannah Voss**
matters to the timeline for one reason: a fall onboarding class of 14 new
hires starts 2026-09-21, which raises access-grant volume inside the
after window (the declared confound).

## The problem and the goal

- **Problem (charter-grade, no solution language):** routine (P3) tickets at
  the Harborview internal help desk averaged ~26 business hours from open to
  confirmed resolution in June 2026, against the service catalog's
  8-business-hour promise; the July baseline window measured **26.71**
  business hours (n = 127), with **127 of 127** sampled tickets over the
  promise.
- **Goal (SMART):** cut mean routine-ticket resolution time to **≤ 8.0
  business hours** by **2026-10-31**, without degrading the reopen-rate or
  tech-overtime guardrails.
- **Spec limit for capability:** USL = 8.0 business hours (the catalog
  promise — a customer line, never a control limit). No LSL: a fast ticket
  has no lower bound, so capability is one-sided (Cpk on the upper side
  only; no Cp/Pp without both limits).
- **Define-phase cost ingredients** (Q2 facts, for T-02 — the runner does
  the arithmetic in-tool): 812 routine tickets; 1,463 logged status-chase
  contacts averaging 6 minutes of tech time each; 74 reopened tickets
  averaging 1.1 hours of rework; loaded tech rate $34/hour. Late system
  access for 9 new hires (average 2.6 business days) is **counted but not
  priced** — an honest named-not-priced line, since idle-capability dollars
  could not be defended. Expected order of magnitude: ≈ $7,742/quarter
  (chase $4,974.20 + rework $2,767.60), ≈ $30,967/yr only if labeled
  projection with the ×4 basis stated.
- **Consequential metrics (guardrails), declared at Define:** reopened
  tickets per 100 (baseline 9.1), tech overtime hours/week (baseline 3.5).

## The data (pre-collected)

Per PLAN §9, scenario datasets are pre-collected and realistic — the eval
measures the suite, not the runner's ability to gather data. All four files
are seeded-generator outputs whose every claimed statistic was run through
the live engine after generation; `data/data-note.md` embeds the generator
verbatim (seed 32) and records the engine transcripts.

- `data/tickets-baseline.csv` — 127 routine tickets, every 2nd routine
  ticket over 20 business days 2026-07-06 → 2026-07-31. Columns:
  `ticket_id`, `date`, `request_type` (password_reset / software_install /
  access_grant), `channel` (portal / email), `tech` (initials),
  `resolution_hours` (business hours, tenths, open → user-confirmed
  resolution). Rows are in true time order — what an I-MR chart requires.
- `data/tickets-after.csv` — 124 tickets, same columns, same operational
  definition and extraction, the measured after window 2026-09-14 →
  2026-10-09 (the 09-07..09-11 bedding-in week excluded by declaration).
- `data/msa-repeats.csv` — the T-12 test/retest pairs: 12 baseline tickets
  spanning the observed range, each duration re-extracted blind from the
  event log by the same person five days after the first pass (columns:
  `ticket_id`, `first_extract_hours`, `second_extract_hours`).
- `data/delay-tallies.csv` — the T-08 check-sheet marks: one mark per
  baseline ticket that blew the 8-hour promise (all 127), tagged with the
  largest wait segment in its event log (`primary_delay_reason`).

Story facts the runner needs that live in prose, not CSV: the stage means
from the event-log decomposition (for T-06's map and its readout) —
unassigned queue wait ≈ 16.5 h, dispatch-to-first-action ≈ 2.8 h, hands-on
work ≈ 1.9 h, confirmation lag ≈ 2.6 h, plus ≈ 7.4 h manager-approval wait
on access grants only. These reconcile with the engine's group means
(non-access 23.76, access 31.12).

## The expected arc, phase by phase

What follows is the scenario's reference arc with the engine-verified
numbers a correct run reproduces. It says what the phases should conclude,
not the words the runner must use — grading is by the shipped rubric
against these facts.

### Define

Picker (T-01): five intake criteria answered Yes — measurable outcome
(hours from the log), obtainable data (the log), named owner-in-waiting
(Naomi), bounded scope (routine P3 only; P1/P2 incidents and project work
out of scope), no single obvious fix (queue discipline, approvals, and
channels all suspect) — route: full DMAIC, not the PDCA quick path.
Charter (T-03): the problem and goal above, stated without solution
language; risks block includes the fall onboarding surge and approval-
policy pushback; timeline lands the 2026-10-31 milestone. COPQ (T-02) from
the ingredients above. SIPOC (T-04): requester → help desk → resolved
request, boundaries open-to-confirmed-resolution — the same boundaries
every later tool must respect. VoC → CTQ (T-05): the survey verbatims and
walk-up complaints land on one CTQ — C1, elapsed business hours from open
to confirmed resolution, lower is better, promise line 8.0 — with
turnaround-of-incident-tickets explicitly out of scope.

### Measure

Collection plan (T-11): operational definition pins the clock — **start** =
ticket-created timestamp, **stop** = the requester's confirmation reply (or
auto-confirm at +2 business days), business-hours calendar 8:00–17:00
Mon–Fri, tenths of an hour — chosen precisely because techs batch-close
tickets at day's end, so the tech's close-click would flatter the number.
Sampling scheme (feeds T-21's rational-subgrouping read): every 2nd routine
ticket, all three techs, both channels, 20 consecutive business days — one
stream, no gaps. Sample-size panel: planning SD 6.5 (June spot-pull),
margin ±1.25 h, 95% → **n = 104** (engine); plan ~130, achieved 127.
Measurement check (T-12, continuous, run before the baseline verdict):
12 tickets re-extracted blind → resolution pre-check passes (0.1-h
increment = 0.30% of the 32.9-h observed span, 18 distinct values),
**repeatability 1.66%**, denominator study-variation, verdict
**acceptable** — with the repeatability-only caveat printed. The check
validates the *extraction*; the clock-stop rule it rides on is the
operational definition above.
Check sheet (T-08) → Pareto (T-14): 127 delay marks — **sat unassigned in
triage queue 68 (53.5%) + waiting on manager approval 34 (26.8%) =
80.3%, the engine-verified vital few**; requester replies 11, reassignments
8, license waits 6. Process map (T-06): five swimlanes (requester, queue,
dispatcher, tech, approver), the stage means above on the map; the
readout names the **unassigned queue (16.5 h mean sit)** as the dominant
stage — waste-walk tags it waiting, with approval wait second.
Baseline (T-13, the engine's enforced order): **stable, then not capable**
— n = 127, zero rule-1/rule-4 signals (I-MR limits 7.219 / 46.209, x̄
26.714, MR-bar 7.330, σ-within 6.498); normality no-concern (A-D 0.291,
p ≥ 0.15); one-sided **Cpk −0.96** (Ppk −1.01), model DPMO 998,786 (σ
−1.53, shift convention labeled), **127/127 observed over the USL**. The
baseline statement writes both claims together: nothing special is
happening day to day, and the process is built to miss the promise every
time. That hands Analyze its exact question: which common causes make a
*stable* process run at 26.7 against 8.

### Analyze

Fishbone + 5 Whys (T-15): causes with evidence pointers, three states used
honestly — **verified:** the once-a-day triage batch (check sheet 68/127 =
53.5%; the map's 16.5-h queue stage) and the approval wait on access grants
(34/127 marks; the stratified test below); 5-Why chain on the batch:
tickets sit → triage runs once daily → "triage is the lead's 8:30 block" →
root: **assignment is a scheduled event, not a flow**. **Investigating:**
email-channel triage lag (email +2.4 h in the plan's strata — real but
minor). **Candidates (no-evidence chip):** tech skill mix, ticket-form
quality. **Ruled out with evidence kept:** extraction/clock error (T-12
passed at 1.66%); tech capacity (hands-on work is 1.9 h of a 26.7-h
cycle).
FMEA (T-16): process FMEA on the request flow; highest-severity row is
**access granted with wrong scope** (severity 8, security exposure) — low
RPN by frequency, surfaced by the severity-first view, actioned with an
approver checklist + quarterly access review so no security row sits
unaddressed; highest-RPN row is the mis-routed-then-forgotten ticket.
Hypothesis (T-17, one pre-declared primary): access grants vs other
routine tickets, Welch t — **access n = 51, mean 31.12, SD 4.99 vs rest
n = 76, mean 23.76, SD 5.04; t = 8.11, p = 8.3e-13, d = 1.47 (CI 1.07 to
1.87)**. Read honestly both ways: the approval wait is real and large *and*
even non-access tickets average 23.8 against an 8-hour promise — so the
queue batch is the primary cause, approvals the second. Ranked hand-off to
Improve: (1) assignment-as-scheduled-event, (2) approval wait on access
grants — together the engine-verified 80.3% vital few.

### Improve

Solution matrix (T-18), weights declared before scores: (a) assign-on-
arrival dispatch rule ($0, method change), (b) pre-approved access matrix
for standard roles (policy change, needs Braun + department sign-offs),
(c) hire a fourth tech (~$68k/yr). Expected ranking: the dispatch rule
first (highest impact-per-effort on the #1 cause), the access matrix
second (queued, not rejected), the hire last — capacity was never the
verified cause.
Pilot plan (T-19): **one change** — the dispatch rule (ground truth block:
live 2026-09-07, threshold **after-window mean ≤ 12.0 business hours**
declared 2026-09-03, falsification line "two settled weeks above 12.0 →
revert and take the next-ranked cause"), confounder checklist carrying the
onboarding class (2026-09-21, direction: can only mask the win). A draft
bundling the access matrix into the same pilot must be split: EXIT-10 —
more than one change declared — is the engine's named refusal, and the
scenario expects the runner to keep the pilot to one change (the matrix
stays ranked for the next loop).
Proof + gap (T-20) on the measured after window (2026-09-14 → 2026-10-09,
n = 124): after mean **7.217** (SD 2.080), Welch t vs baseline **t = 33.70,
p = 3.5e-73, d = 4.23 (CI 3.79 to 4.68)** — threshold met (7.22 vs 12.0),
verdict **weakened** by the declared onboarding confound (direction
stated: it could only have hidden improvement), guardrails improved
(reopens 9.1 → 7.8 per 100; overtime 3.5 → 3.1 h/wk). Gap block: goal
8.0, baseline 26.714 → gap 18.714; recovered 19.497 = **104.2%, remaining
−0.78** → goal met — route to Control. The capability run at the moment of
best news keeps the close honest: after window is **stable** (zero
signals, limits 0.607 / 13.827) with **Cpk 0.12** (Ppk 0.13, A-D 0.318
no-concern), **44 of 124 tickets (35.5%) still over 8.0** — the mean
promise is kept, the every-ticket promise is not, and the access-grant
tail is where it lives (model DPMO 353,260, σ 1.88, convention labeled).

### Control and wrap

Control chart (T-21): I-MR frozen from the after window — 124 points the
engine verified signal-free before freezing (≥ 20-point floor met), center
7.217, limits 0.607 / 13.827; the catalog's 8.0 stays a drawn spec line,
never a control limit. Control plan (T-22): monitors C1 weekly, the reopen
guardrail, **and the method itself** (dispatch-within-the-hour compliance
from the log — a lapsed method gets caught before the chart must catch
it); every line owned by a named person; OCAP first steps investigate the
dispatch rule before anything else; training & handoff block covers the
dispatcher-of-the-day rotation; scheduled check-ins weekly through
November. Owner: **Naomi Castillo accepted 2026-10-12** (ground truth —
grading is consistency with that fact). SOP (T-24): the dispatch rule as
standard work — queue watched, assign within the hour, approval request
fired at assignment, steps marked changed-from-prior. A3 (T-25): panels
roll up with no claim upgraded in transit — realized benefits recomputed
over the 4-week after window only, annualization labeled projection with
its basis; objectives reconciled by the gap arithmetic (met, remaining
−0.78); lessons include the genuine dead end (capacity was not the cause);
open items with owners: the 35.5% over-promise tail and the November
access-matrix work (a plan, stated as a plan).

## Scenario ground truth (the eval-mode facts)

A time-boxed scenario cannot supply organizational outcomes, so the three
rubric items that rest on them grade **plan-and-record quality against the
facts this spec declares** (rubric §10.7a; frontmatter `ground_truth` is
the machine-readable copy):

- **R-CTL-03 (owner):** Naomi Castillo, help desk lead, accepted the
  control-plan owner role on 2026-10-12. A run that names a different
  owner, or leaves acceptance unrecorded, is graded against this fact.
- **R-IMP-05 (implementation beyond the pilot):** the dispatch rule became
  standing practice 2026-10-12; the access-matrix rollout is scheduled for
  November 2026 and is graded **as a plan** — written as if real, with
  owner and dates — never as an accomplished result.
- **R-WRAP-02 (post-improvement actuals):** benefits are realized-to-date
  over the four-week after window (chase contacts and reopens recomputed
  from the same logs as the Q2 COPQ); the annual number exists only as a
  labeled projection with its ×-basis stated.

Everything else in the arc — every statistic — is not "ground truth by
declaration" but engine output: a correct run reproduces it from the data
files through the live engine.

## In-scope tools and the N/A set

Per rubric §1 (Applicability): in eval runs the scenario spec — not the
runner — owns the N/A set, declared here at authoring time. A runner who
skips an in-scope tool scores **Fail** on that tool's rubric item, not
N/A. The frontmatter `in_scope_tools` / `na_tools` is the machine-readable
copy; the one-line reasons:

**In scope (21):** T-01, T-02, T-03, T-04, T-05, T-06, T-08, T-11, T-12,
T-13, T-14, T-15, T-16, T-17, T-18, T-19, T-20, T-21, T-22, T-24, T-25.

**Honestly N/A (4):**

- **T-07 Spaghetti** — no movement component: queue-and-keyboard work; no
  verified or candidate cause involves physical travel. (The rubric's own
  example of a legitimate N/A.)
- **T-09 Time Study / Work Sampling** — the ticket system timestamps every
  stage of every ticket; the extract already carries the element times a
  stopwatch study would re-collect. Don't stopwatch what the system logs.
- **T-10 Yield / DPMO** — continuous-metric project: no per-step pass/fail
  counts or opportunity structure to tally; T-13's baseline already
  reports the model-based DPMO/sigma readout with its convention labeled.
- **T-23 5S** — no workplace-organization component: the queue is digital
  and no cause pointed at physical clutter or layout.

## Coverage table

Which of the 25 Tier-A tools (matrix §1 — the one authoritative count)
this scenario's declared scope covers, and who else covers each. The
collective claim for all four scenarios lives in `evals/scenarios/README.md`.

| Tool | S-1 | Also covered by |
|---|---|---|
| T-01 Project Picker | in scope | Coffee, Print, S-2 |
| T-02 COPQ | in scope | Coffee, Print, S-2 |
| T-03 Charter | in scope | Coffee, Print, S-2 |
| T-04 SIPOC | in scope | Coffee, S-2 |
| T-05 VoC → CTQ | in scope | Coffee, Print, S-2 |
| T-06 Process Map + Waste Walk | in scope | Coffee, S-2 |
| T-07 Spaghetti | **N/A** (no movement) | Coffee |
| T-08 Check Sheet | in scope | Coffee, Print, S-2 |
| T-09 Time Study / Work Sampling | **N/A** (system timestamps) | Coffee |
| T-10 Yield (FPY/RTY + DPMO) | **N/A** (continuous metric) | Print, S-2 |
| T-11 Data Collection Plan | in scope | Coffee, Print, S-2 |
| T-12 Measurement Check | in scope (continuous path) | Coffee, Print, S-2 |
| T-13 Baseline: Stability→Capability | in scope (I-MR path) | Coffee, Print, S-2 |
| T-14 Pareto / Histogram / Run | in scope | Coffee, Print, S-2 |
| T-15 Fishbone + 5 Whys | in scope | Coffee, Print, S-2 |
| T-16 FMEA | in scope | Coffee |
| T-17 Hypothesis (guided) | in scope (Welch t) | Coffee, Print, S-2 |
| T-18 Solution Matrix | in scope | Coffee, S-2 |
| T-19 Pilot Plan | in scope | Coffee, S-2 |
| T-20 Before/After Proof + Gap | in scope | Coffee, Print, S-2 |
| T-21 Control Charts (I-MR, p) | in scope (I-MR) | Coffee, Print, S-2 |
| T-22 Control Plan + OCAP | in scope | Coffee, S-2 |
| T-23 5S Audit | **N/A** (no physical workplace) | Coffee, S-2 |
| T-24 Standard Work / SOP | in scope | Coffee, S-2 |
| T-25 A3 + Tollgates | in scope | Coffee, S-2 |

21 in scope + 4 honest N/A = 25 accounted for; every N/A here is covered
by at least one other scenario, so the four-scenario set (and even the
strict PLAN §9 trio of Coffee Bar + S-1 + S-2) exercises all 25.

## Grading notes

- `eval_mode: plan_quality_only` applies exactly to the three §10.7a items
  named above and nowhere else; the wall is one-directional — real-project
  grading reverts to organizational reality (PLAN §9).
- The statistics in this spec are the reference outputs of the live engine
  on the shipped data (transcripts in `data/data-note.md`). A run whose
  numbers differ has either mis-fed the tools or found a real engine
  regression — both are findings; neither is graded as style.
- Skipping an in-scope tool = Fail on its item (rubric §1); using an N/A'd
  tool anyway is not penalized by itself but cannot substitute for an
  in-scope one.
- Phase pass bar: "acceptable Green Belt work" per the rubric anchors —
  usability failures and validity failures are logged separately (PLAN §9).
- Honesty beats in this arc that graders should expect even without a
  named exit: capability language only after the T-12 pass and the
  stability verdict; the one-sided Cpk labeled one-sided; the σ-level
  carrying its shift convention; EXIT-10 if a runner bundles the access
  matrix into the pilot; the confound declared before the window and
  riding the proof verdict; the A3 upgrading no claim in transit.
