```yaml
scenario_id: S-1
persona: "Corey Lindqvist — IT operations coordinator, Harborview Mutual (fictional, invented for this run)"
simulated: true
label: "SCRIPTED UNTRAINED-PERSONA RUN, simulated by an AI agent per the 2026-08-07 owner ruling. Not a human result."
engine_version: "0.1.0"
date: "2026-08-08"
project_id: "persona-s1-corey"
engine_calls: 105
evidence: "engine project persona-s1-corey (artifact version history is the audit trail)"
```

# S-1 persona run — Corey Lindqvist (SIMULATED)

## The persona

Corey Lindqvist, IT operations coordinator. Community-college AA,
four years at Harborview doing asset tracking and vendor tickets. No
process-improvement training of any kind. Victor Braun handed him the
suite with: "make the ticket numbers stop embarrassing us, and use this
thing so it's written down." What Corey knows going in: the story facts
(the desk, the 8-hour promise, the June spot-pull of 15 tickets averaging
~26 hours with SD about 6.5, Naomi's morning triage routine, the fall
onboarding class), the four data files Naomi can pull, and whatever the
screens tell him. Nothing else.

Voice note: Corey reads helper panels when he's unsure, not before every
field. He trusts computed numbers over his own arithmetic until they
disagree with common sense.

## Intake — T-01 Project Picker

Corey almost skips to "the charter thing" but the rail starts at the
Picker and the helper opens with: *"Five questions that decide whether
the problem in front of you is a workable first improvement project."*
He answers all five Yes in his own words (scope = routine P3 only;
outcome = hours from the log; data = Naomi's CSV export; owner = Naomi;
impact = chase time and reopens, "~26 hours against an 8-hour promise").

He hesitates on Route — PDCA quick path sounds faster. The field guidance
settles it: *"All five Yes and the problem earns the rigor: full DMAIC.
Small single fix: PDCA quick path."* Nobody at Harborview agrees on a
single fix (queue? approvals? email?), so: **full-DMAIC**.

Engine: save v1; prescore `routing_consistency: pass`. Gates
`intake_picker_present` and `intake_picker_not_exit01` both `CLEAR`
(real responses).

## Define — T-02 COPQ (STALL 1: the units mistake, self-recovered)

The Q2 facts from Naomi: 1,463 status-chase contacts at ~6 minutes each,
74 reopened tickets at ~1.1 hours each, loaded tech rate $34/hour.

The form's fields are labeled just **Quantity** and **Rate** — no units.
Corey types `1463` (the contact count) against rate `34` and saves.

Engine (v1, real): row amount **$49,742.00**, total **$52,509.60**.

Corey stares at it: "Fifty grand a quarter for people asking 'any
update?' — that can't be right. Oh. 1,463 *contacts*, not 1,463 *hours*."
He does the arithmetic the basis note was already carrying — 1,463 × 6
min = 146.3 hours — and re-saves.

Engine (v2, real): chase row **$4,974.20**, rework row **$2,767.60**,
total **$7,741.80**. Prescore: `total_matches_rows: pass`,
`period_consistency: pass`.

- Classification: **usability** (unit-less Quantity/Rate labels), low —
  self-recovered because the computed Amount is echoed back and his basis
  note held the conversion facts. Failure log FL-01.

## Define — T-03 Charter (the 'because' catch, suite-recovered)

Corey's first problem statement writes itself the way he'd say it out
loud: *"Routine IT tickets sit around forever **because** triage only
happens once each morning, so anything after 9:30 waits a full day…"*
Goal: ≤ 8.0 business hours by 2026-10-31; guardrails reopens-per-100 and
overtime; risks include the onboarding class; impact $30,967/yr labeled
as the COPQ total ×4.

Engine prescore (v1, real): `problem_statement_solution_language:
flag` — detail: **"solution/cause language found: ['because']"**. The
other five checks pass (magnitude "number+unit+period all present",
owner named, guardrail present, 2 risk rows).

Corey reads the charter helper's whenNotTo: *"a problem statement with a
solution or cause hiding inside it … if the charter already knows the
answer, the Analyze phase becomes theater."* He grumbles ("but it IS the
triage batch") and rewrites to pain-only: tickets take far longer than
the 8-business-hour promise; staff open a ticket and then walk to the
desk anyway.

Engine (v2, real): all six prescore checks `pass`.

- Classification: **suite catch working as designed** — logged as an
  observation, not a failure. The screen text that did it is the flag
  detail plus the helper's theater line.

## Define — T-04 SIPOC and T-05 VoC → CTQ

SIPOC in ten minutes at the desk with Naomi: requester → shared queue →
triage → (manager approval on access grants) → tech work → requester
confirms. Boundaries: ticket opened → confirmation (or auto-confirm at
+2 business days). Prescore: `step_count_range: pass`.

VoC: the two things people actually say — the survey line *"I open a
ticket and just walk to the desk anyway — nothing happens otherwise"*
and the manager walk-up about new hires' access. One need, one CTQ: C1 =
business hours from open to confirmed resolution, lower is better,
target the 8.0 catalog promise. Corey answers the panel's
critical-vs-easy check honestly: both complaints are about the total
wait, not any single step. Prescore: `tree_completeness: pass`.

Gate `define_to_measure` (real): **CLEAR**.

## Measure — import + sample size (STALL 2: the copied margin, self-recovered)

Naomi's July extract (`tickets-baseline.csv`, every 2nd routine ticket,
20 business days) goes through T-11's Import tab. Preview (real): 127
rows, six columns, types inferred correctly, quality scan clean — 0
missing, 0 non-numeric, 0 duplicates. Saved with its SHA-256
fingerprint.

Sample-size panel, "sizing a mean." Planning SD: 6.5 (the June
spot-pull — the only spread number that exists in-story). Margin: the
helper's example says *"±0.5 minutes — precise enough to matter against
an 8.4 → 5.0 minute goal"*, so Corey copies the 0.5.

Engine (real): **n = 650**. Plain-English line: *"To estimate the
average within +/-0.5 (your data's units) at 95% confidence … collect at
least 650 data points."*

"Six hundred fifty? The whole month was 127." He re-reads the margin
guidance — *precise enough to matter against the goal* — and reasons his
gap is 26.7 → 8.0, a ~19-hour canyon, so ±1.25 h is plenty precise.

Engine (real): **n = 104**. The rule-of-thumb block also prints the
I-MR context: *"25-30 individual readings … a little above the 20-point
floor this suite's own baseline tool (T-13) requires before it will
freeze control limits."* 127 achieved ≥ 104 needed: fine.

- Classification: **usability**, low — the helper example anchored him to
  the Coffee Bar's scale; the plain-English echo plus the same panel's
  guidance got him out. Failure log FL-02.

## Measure — T-11 Collection Plan (STALL 3: the clock-stop rule, recovered via in-story ask)

The operational-definition panel's subtitle: *"Would two different people
measuring this get the same number?"* Corey's first draft writes **stops
when: tech marks the ticket resolved** — the obvious clock to a
coordinator. The two-people question doesn't stop him: two people reading
the close-click timestamp WOULD get the same number. What stops him is
having to describe the instrument ("How — instrument or method") next to
Naomi, who tells him the desk's open secret: techs batch-close tickets at
day's end, so the close-click clock would flatter every number. The
extract she pulls runs open → requester's confirmation reply (auto-confirm
at +2 business days), business-hours calendar, tenths.

He writes that rule in, checks the two-people box honestly, declares
`data_type: continuous`, strata `request_type` / `channel` / `tech`,
planned n 130 with the panel's n=104 as the rationale.

Engine prescore (real): all six checks pass, including
`two_people_confirmed` and `planned_n_with_rationale`.

- Classification: **usability**, medium — the screens never surfaced the
  flattering-clock hazard; recovery came from in-story knowledge, i.e.
  "what was asked" per PLAN §9's task-level failure logging. A tester
  without a Naomi keeps the close-click and the whole run measures the
  wrong thing. Failure log FL-03.

## Measure — T-12 Measurement Check

Corey's instinct is to skip it: "the computer stamps the times — what is
there to check?" The helper's first common mistake answers him by name:
*"Skipping the check because the numbers 'look fine.' Gauge noise is
invisible in the numbers it contaminates — that's the whole problem."*
And the extraction is not the computer — it's Naomi applying the written
rule to a messy event log.

The study (in-story): Naomi re-extracts 12 baseline tickets blind, five
days after the first pass. Corey enters the 12 pairs, operator "Naomi
Castillo", gauge "ticket-system event log, extracted by hand per the
written rule", increment 0.1, USL 8.0, LSL empty (the field guidance
warns against inventing a lower limit — "denominator shopping").

Engine (real): resolution pre-check **passed** (increment 0.1 vs
observed span 32.9 → ratio 0.3%, 18 distinct values). Repeatability
**1.66%**, denominator **"6 × study variation"** (no LSL, so no
tolerance width — exactly what the USL/LSL guidance said would happen).
Verdict **acceptable**. The caveat prints in full: *"Repeatability-only:
a full multi-operator gauge study was not done here. The 10% / 30% bands
above are borrowed from full-gauge-study convention, so passing them on
repeatability alone is the lenient side — a full study could only read
worse, not better."* Corey copies that caveat into his notes because the
checklist says the write-up must carry it in his own words.

Gate `measure_capability_language_requires_msa_pass` (real): **CLEAR**.

## Measure — T-08 Check Sheet → T-14 Pareto

Naomi's delay-reason tally (one mark per baseline ticket over the
promise, tagged with its largest wait) is an existing record, so Corey
uses the **"Transcribe a paper tally"** panel — its subtitle says exactly
what he's doing: *"Reading counts off an existing paper sheet after the
fact — honestly, not tapped live."* Five categories, counts 68 / 34 / 11
/ 8 / 6, as-of 7/31, source note filled (the panel makes it required:
*"this is what makes a transcription honest"*).

Engine prescore (real): `strata_declared: flag` — *"no stratification
fields declared — shift/station/operator splits won't be possible
downstream."* Corey reads it, decides the split he needs (request type,
channel, tech) already lives as columns in the imported dataset, and the
tally's job is only the delay-reason counts. He leaves the flag standing
with that reasoning. Export to dataset succeeds (real).

T-14 Pareto (real): **"Sat unassigned in triage queue > 4h" 68 (53.5%)
and "Waiting on manager approval" 34 (cumulative 80.3%) are marked
vital_few: true**; requester replies 11, reassignments 8, license waits 6
close it out; `flat: false`. Corey's read, logged in his notes: "Half
the pain is tickets nobody has even looked at. A quarter is waiting on a
manager to click approve."

- The standing T-08 flag: **usability**, low (transcribed mode cannot
  carry per-mark strata; the flag has no in-mode resolution). Failure
  log FL-04.

## Measure — T-06 Process Map + Waste Walk

Built from Naomi's event-log stage breakdown (story facts): queue sit
≈16.5 h, dispatch-to-first-action ≈2.8 h, approval wait ≈7.4 h (access
only), hands-on ≈1.9 h, confirmation ≈2.6 h. The time field is labeled
minutes, so Corey converts (16.5 h → 990) with a grumble but no error.
Five lanes, waits tagged `non_value_add` with waiting-waste notes, the
approval step marked a defect point.

Engine (real): `longest_step` = **s1 "Ticket sits unassigned in the
queue" (990 minutes)** — the engine names the queue the biggest block of
the cycle, matching the Pareto's top bar from the other direction.
`constraint_step` = s5 (confirmation, 156 min) with the method text
explaining why: *"a pure-wait non_value_add step cannot be the
constraint"* — only processing steps are eligible. Corey's read: "the
bottleneck among actual work steps is the confirmation lag, but the
elephant is still the unassigned queue." All nine prescore checks pass.

## Measure — T-13 Baseline (stability then capability)

Dataset: the fingerprinted import. Column `resolution_hours`. USL 8.0
(the catalog promise — entered before results, per the field guidance's
warning about reverse-engineered specs). LSL empty. The
operational-definition checkbox is true honestly — the T-11 rule exists
in writing now.

Engine (real): `stability_note` **"stable: 127 points, no default-rule
signal"** — I-MR center 26.714, limits 7.219 / 46.209, zero signals.
Normality: no concern (A-D 0.291, "p >= 0.15"). Capability: **Cpk
−0.96** (one-sided, Cp/Pp not available without both limits — the cells
say why), Ppk −1.01. Sigma block: **DPMO 998,786, sigma level −1.53,
labeled "with 1.5σ shift"**. `exits: []`, `measurement_check: null`.

Corey's reaction, in his notes: "Stable sounded like good news for about
five seconds." The helper's line lands — a stable process can be stably
too slow — and his baseline sentence writes both truths: *nothing weird
is happening day to day, and the process is built to miss the promise
every time — 127 of 127 sampled tickets over 8 hours, average 26.7.*
Charter said 26.71 from the June spot-pull scaling; measured 26.714 —
no reconciliation edit needed.

Gate `measure_to_analyze` (real): **NOT_YET_BUILT** — *"not-yet-built:
Measure math guards (stability/capability) ship across M2."* Corey reads
it as "no gate here yet" and moves on. (Logged: failure log FL-09 — the
stub text still names M2 while the suite is at M6.)

## Analyze — T-15 Fishbone (STALL 4: the engine refuses "everyone knows it")

Corey's first board marks the triage batch **verified** with no evidence
attached — "Naomi says so, everyone says so."

Engine (real, HTTP 422): *"cause 'c-batch': **evidence is required
(non-empty) when status='verified'**."*

The helper says the same thing in prose: *"'team consensus' moves
nothing past candidate, and the schema enforces it: the tool will not
save a verified cause without an evidence pointer."* Corey attaches what
he actually has — the check sheet (68/127 marks) for the batch, the
map's 990-minute queue step for the 5-Why root ("assignment is a
scheduled event, not a flow"), the check sheet again for the approval
wait. Email lag goes in as **investigating** (the stratified view shows
email ~+2.4 h — real but small); tech skill and form quality stay
**candidates** with empty evidence slots; extraction error and tech
capacity go in as **ruled_out** with the T-12 pass and the 1.9h-of-26.7h
map fact as the retained evidence.

Engine (v2, real): board saves; `verified_causes` computes 3 causes,
each with its evidence pointer. One flag: `branch_coverage_minimum` —
*"3/6 branches carry a cause — fewer than 4, a single pre-decided path
with decoration (rubric R-ANA-01 #4)."*

Corey adds the machine-branch idea he and Naomi had actually kicked
around — first phrased as *"one system email with no reminder — nothing
nudges anyone."* Engine (v3, real): new flag,
`absent_solution_language` — *"cause(s) phrased as a missing fix, not a
condition/mechanism."* He re-words to the mechanism: the approval email
lands in an ordinary inbox and competes with everything else there.
Engine (v4, real): **all five checks pass**.

- Classification: two **suite catches** (the 422 and the missing-fix
  flag) — both recovered via the on-screen text; logged as observations.
  The branch-coverage flag drove honest widening.

## Analyze — T-16 FMEA

Four rows off the mapped steps, rated with the anchor tables open
(`anchors_consulted: true` per row): mis-routed-and-forgotten ticket
(5/7/8), **access granted with wrong scope (severity 8** — "a security
hole: an over-privileged account nobody notices"), stale-manager routing
(6/4/5), auto-confirm hiding unfixed tickets (4/6/5). Every row gets an
action, owner, and date.

Engine (real): `sorted_view` = **["r-wrong-scope", "r-stale-mgr",
"r-misrouted", "r-autoclose"]** with the method text explaining
severity-first: *"a lower-severity row can never outrank a
higher-severity one here on RPN alone."* Corey notices the row with the
biggest RPN (mis-routed, 280) is NOT on top — the severity-8 security
row is — and the method line tells him why. `blocking_flags` empty (no
9/10 severity rows). All five prescore checks pass.

## Analyze — T-17 Hypothesis (the one declared comparison)

Question in Corey's words: "Do access-grant tickets take longer to
resolve than the other routine tickets?" Declared primary, one
comparison, one test. Two independent groups from the baseline by
request type (51 access vs 76 other).

Engine (real): routed to **welch_two_sample_t** via a printed decision
path Corey can actually follow (one declared primary → not count data →
one measurement per unit → two independent). Result: **t = 8.114, p =
8.3e-13, significant**; access mean **31.12** (SD 4.99, n=51) vs other
**23.76** (SD 5.04, n=76); effect size **Cohen's d = 1.467, CI [1.07,
1.87]**, with the CI method named.

Corey's honest two-way read, logged: access grants really are ~7.4 hours
slower — AND the non-access tickets still average 23.8 against an 8-hour
promise, so approvals are chapter two, not the story. Ranked hand-off to
Improve: (1) assignment-as-scheduled-event, (2) approval wait.

## Improve — T-18 Solution Matrix

Three real options, each linked to a verified (or honestly ruled-out)
cause; criteria and weights declared at 09:00 before any score exists at
11:00 (the timestamps carry the discipline): impact-on-#1-cause 0.5,
speed 0.25, cost 0.25.

Engine (real): ranked list — **1. assign-on-arrival dispatch (quick_win,
weighted 4.75), 2. pre-approved access matrix (major_project, 3.0),
3. hire a fourth tech (fill_in, 1.0)**; `unlinked: []`. The hire ranks
last on purpose: Corey scores it honestly against the map fact that
capacity was never the verified cause.

## Improve — T-19 Pilot (STALL 5: the bundle, refused by name)

Corey's first pilot draft adds a second change: *"Also pre-approve the
standard access matrix at the same time — two birds, one pilot."*

Engine (real, HTTP 422): *"**EXIT-10: more than one change described for
a single pilot** (matrix §4a trigger…). The Improve loop is
one-change-at-a-time by design (PLAN §4.1, rubric R-IMP-02 #1): run the
extra change as its own sequential pilot once this one is proven, declare
a genuinely inseparable PACKAGE explicitly if the components truly cannot
deploy apart … or route to the advisor / v1.1 Experiment Planner / a
human expert for a real multi-factor question. Remove the extra entry
from `changes` (got 2)…"*

Corey reads it twice and gets it: "if both go in and the number moves,
we'd never know which one did it." The access matrix goes back to rank 2
on the list. The clean pilot saves (real, prescore all pass): one change
(dispatch-on-arrival), threshold **after-window mean ≤ 12.0** declared
2026-09-03 — before the 09-07 go-live — falsification line ("two settled
weeks above 12.0 and we revert"), and the confounder checklist carrying
the onboarding class with its direction: *"more access grants can only
push our numbers UP — it can hide a win, it can't fake one."*

- Classification: **suite catch** (hard refusal), recovered via the
  refusal text itself. Logged as the run's best example of the engine
  teaching method mid-flow.

## Improve — T-20 Proof + the honest capability re-run

In-story the pilot runs from 09-07; the bedding-in week is excluded by
the declaration; the measured window is 09-14 → 10-09. Corey imports
`tickets-after.csv` (124 rows), marks the pilot complete, and runs the
proof: before = the frozen July extract, after = the after window, the
declared 12.0 threshold, the confounder checklist re-affirmed, guardrails
entered from Naomi's numbers (reopens 9.1 → 7.8 per 100; overtime 3.5 →
3.1 h/wk).

Engine (real): routed Welch again — **t = 33.696, p = 3.5e-73, d = 4.23
[3.79, 4.68]**; before 26.714 (n=127) vs after **7.217** (n=124).
Verdict headline, quoted: *"**Threshold met, as declared**: Average
resolution hours (charter C1) = 7.21694 vs 12 (lower_is_better).
Improvement shown, but a reported confounder **weakens** this proof:
season: Fall onboarding class started 9/21 inside the window — could
only push times up, so it can hide the win, not fake it."* Gap block:
original gap 18.71, recovered 19.49 = **104.2%, remaining −0.78,
goal_met: true**, next-cause pointer to the access matrix. Guardrails:
both `moved: "improved"`, no material worsening.

Then the honest part Corey almost skipped: T-13 on the after window
(same USL 8.0). Engine (real): **stable** (124 points, no signals,
limits 0.607 / 13.827) but **Cpk 0.12**, DPMO **353,260** (σ 1.88, shift
convention labeled). His note: "We fixed the average, not every ticket —
about a third still individually run past 8 hours, mostly access
grants. That's the next loop, not a victory lap."

## Control — T-21, T-22 (flag round), T-24

**T-21 I-MR freeze.** Corey wants to draw the 8-hour line as a limit;
the helper is blunt — *"The customer's 5.0-minute line stays a SPEC
limit — it never gets drawn as a control limit … 'out of control' and
'out of spec' are different sentences."* He freezes on the 124
after-window points instead. Engine (real): frozen center **7.2169**,
limits **0.6069 / 13.827**, zero signals in the window, armed with a
weekly cadence note. All six prescore checks pass.

**T-22 Control Plan.** Three monitored items (C1 weekly; the reopen
guardrail; and the method itself — dispatch-within-the-hour compliance,
"if the method lapses, the chart finds out late — this finds out
first"), one OCAP, a training row verified 10/13, weekly check-in
schedule seeded with the REAL frozen limits, first check-in entered.
Engine prescore (real): seven pass, one flag — `ocap_coverage`:
*"monitored item(s) with no OCAP entry yet: ['mi-reopen',
'mi-method']"*. Corey writes the two missing response paths (v2, real):
**all eight checks pass**. Plan health (real): no ownerless items, no
unaccepted owners, not theater. Owner: Naomi accepted 2026-10-12
(recorded on the plan — ground-truth fact that happened to them).

**T-24 SOP.** The dispatch rule as standard work — four steps, three
marked changed-from-prior, the wrong-scope FMEA action folded into step
3. Prescore: all pass.

Gates `improve_to_control` / `control_to_wrap` (real): NOT_YET_BUILT
stubs, same M-milestone wording as before (failure log FL-09).

## Wrap — T-25 A3 (the flag round that finished the project)

Corey fills the eight panels (background, current condition, goal,
analysis, countermeasures, results, follow-up, lessons) — annualization
labeled as a ×4 projection, the 35.5% tail named in results, the EXIT-10
story told in countermeasures. Saves v1.

Engine prescore (real): three flags, each with an address —
`realized_benefits_present` (*"missing its COPQ re-run reference or
stated window"*), `tollgates_answered` (*"phase(s) with an unanswered
tollgate question: ['Define', 'Measure', 'Analyze', 'Improve',
'Control', 'Wrap']"*), `lessons_substantive` (*"0 lesson(s) recorded, a
went-wrong lesson present=False — a lessons panel of only wins is not
lessons"*).

He hadn't known those blocks existed (they sit below the panels). The
fixes, all real calls:

1. **COPQ re-run** (`cl-copq-after`, new T-02 artifact): the after
   window re-counted from the same logs — chase 8.4 h, reopens ~21.5 h
   (marked estimate) → total **$1,016.60**, vs his stated Q2-rate
   4-week equivalent $2,380.85, both bases written out.
2. **Realized benefits block**: window stated, before/after amounts,
   fix cost $0 → engine computes **realized-to-date $1,364.25** (net
   the same). No annual projection claimed.
3. **All 18 tollgate questions answered** in his own words with
   evidence refs — including Wrap-2's "at least one thing that didn't
   work."
4. **Lessons** with two went-wrong entries (the hire instinct; the
   refused two-change pilot) and one win (the clock-stop rule).
   **Open items** with owners (the 35% tail → Naomi; the November
   access-matrix policy work → Victor, written as a plan).
5. `project_status: closed` — close check (real): *"No unaddressed
   severity-9/10 safety/regulatory row on the linked FMEA — this check
   does not block closure."*

Engine (v2, real): **all six prescore checks pass.** Objectives
verdict (real): recovered 104.2%, remaining −0.78, *"Goal met — route to
Control."*

- Classification of the flag round: **usability**, low — the blocks were
  invisible until post-save flags named them; the details were precise
  enough to fix everything without outside help. Failure log FL-10.

## Stalls and catches — the full list

| # | Where | What happened | Resolution | Class |
|---|---|---|---|---|
| 1 | T-02 COPQ | Typed contact count as hours-quantity → $49,742 row | Self-recovered: computed Amount echo + own arithmetic | usability (FL-01) |
| 2 | T-11 sample size | Copied the helper example's ±0.5 margin → n=650 | Self-recovered: plain-English echo + margin guidance re-read | usability (FL-02) |
| 3 | T-11 op-def | First clock-stop rule (tech close-click) would flatter the number | Recovered via in-story ask (Naomi) — nothing on-screen catches it | usability, medium (FL-03) |
| 4 | T-15 fishbone | "Verified" with no evidence | Engine 422 + helper text; evidence attached | suite catch |
| 5 | T-15 v3 | New cause phrased as a missing fix | Prescore flag text; re-worded to mechanism | suite catch |
| 6 | T-19 pilot | Bundled two changes | Engine 422 EXIT-10; split, second change stays ranked | suite catch |
| 7 | T-08 tally | strata flag on transcribed counts | Accepted with reasoning (splits live in the dataset) | usability, low (FL-04) |
| 8 | T-22 plan | Two monitored items had no OCAP | Flag detail named them; both written | suite catch |
| 9 | T-25 A3 | Tollgates/lessons/realized-benefits blocks unknown to him | Three flag details; all fixed in v2 | usability, low (FL-10) |

Hard stalls: **none**. Engine numbers wrong for their inputs: **none
observed**.

## Phase-by-phase honest outcome (facts for the graders)

- **Define:** charter magnitude-only after one prescore round; COPQ
  $7,741.80/quarter computed by the engine; SIPOC boundaries =
  open-to-confirmation; one CTQ carried unchanged into everything
  downstream. Business impact annualized only as a labeled ×4.
- **Measure:** measurement check ran **before** the baseline was
  trusted (1.66% repeatability, acceptable, caveat carried); baseline
  **stable then not capable** — 26.714 mean, zero signals, one-sided
  Cpk −0.96, DPMO 998,786 with the shift convention labeled; vital few
  80.3% (queue + approval).
- **Analyze:** three verified causes each carrying evidence the engine
  enforced; capacity and extraction error ruled out with the evidence
  retained; Welch t = 8.11, d = 1.47 [1.07, 1.87] read both ways.
- **Improve:** one change piloted (EXIT-10 refused the bundle);
  threshold declared before the window; verdict **met-but-weakened**
  with the confound's direction stated; gap 104.2% recovered; the
  after-window capability run kept the close honest (Cpk 0.12, ~35.5%
  of tickets still over).
- **Control:** limits frozen from the demonstrated-stable after window
  (7.217, 0.607/13.827); spec line never a control limit; the plan
  monitors the method itself; owner acceptance recorded 2026-10-12.
- **Wrap:** realized benefits from the COPQ re-run over the stated
  4-week window ($1,364.25, engine-computed), no annual claim; 18/18
  tollgates answered; two went-wrong lessons; open items owned; close
  unblocked and taken.
