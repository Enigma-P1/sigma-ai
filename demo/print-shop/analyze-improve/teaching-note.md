# The refused drafts, and what the refusals teach

Two drafts in this folder were refused by the engine, kept on purpose —
seeing the mistake is half the teaching (PLAN §4.4). This demo carries two
flawed-then-fixed pairs: the defect-marks chart on the chart selector
(`chart-flawed.json`, below) and the consensus fishbone on Analyze's
evidence discipline (`fishbone-flawed.json`, the pair the locked matrix's
flawed-example registry assigns to T-15 and this demo — last section),
the way the coffee bar's pair lives on the charter. First the chart. At
the 2026-09-06 wrap-up, with the recalculation of the monitoring chart on
the table, the proposal was to make the new chart richer: plot each
day's **total failed-check marks**
across the four checks — "the chart should show how many things went
wrong, not just how many orders" — through the same p-chart route. The
draft answers the selector's printed question honestly
(`defectives_or_defects: "defects"`) and the engine refuses at
validation, before touching a single data point: HTTP 422 from
`POST /artifacts/T-21/validate`.

## The refusal, verbatim

The 422 body's error, exactly as the live engine returned it (location:
`selector`):

> Value error, EXIT-11: This is counts-per-unit/area (defects), not
> pass/fail units (defectives) -- a p-chart is barred for it by name
> (defectives != defects, matrix VI.A.3 / §4a). Routes to: c/u chart
> family (T-29, v1.1) for monitoring; DPMO/yield (T-10) remains available
> as a descriptive summary.

Named exit, named rule, named route out — a refusal, not an error message:
the engine knows exactly what this data is and where it belongs, and says
so instead of computing something shaped like a chart.

## Why the engine is right

A p-chart's whole mathematical apparatus — p̄ as a binomial proportion, the
√(p̄(1−p̄)/n) limits that breathe with each day's n — assumes each of the n
units contributes exactly one pass/fail outcome. Defect *marks* break that
assumption quietly: one order can carry several, so the "proportion" can
be pushed by a few multi-defect orders without one extra order failing,
and the binomial variance under the limits is no longer the variance of
anything real. The baseline window shows the gap concretely: **139 marks
on 135 rejected orders** — four orders failed two checks each. Marks per
order is Poisson-family territory (c/u charts, v1.1), and the honest v1
homes for count data already exist: T-10's DPMO block is exactly this
window's 139 marks against 6,264 opportunities, and the check sheet +
Pareto re-runs carry the per-type trending the proposal actually wanted.
The refusal routes to all of them by name. The trap is real precisely
because it usually computes: feed marks through the p route and nothing
crashes — every limit is just wrong, and every signal read off it is a
guess wearing arithmetic.

## The same guard on the test selector

The bar is not chart-specific, and the demo shows it: the routing-only
endpoint (`POST /stats/hypothesis/route`, safe to call speculatively) was
given the same framing as a before/after question — total marks declared
as what they are, `declared_data_type: "count_rate"` — and the printed
decision path stops at the same name before any route is chosen:

> Is the outcome a rate-with-exposure or a defect count per unit/area? →
> declared_data_type='count_rate' → **EXIT-11 — no v1 route carries
> count/rate data honestly.**

with `route: null` and the registry message ("defectives are pass/fail
units, defects are counts on units…"). One rule, two doors, same
refusal — proportions machinery is barred for counts everywhere, not
wherever someone remembers.

## The corrected chart

The corrected version is `../control/control-chart.json`: same monitoring
intent, charting **defective orders** — pass/fail units, the thing a
p-chart's math actually describes — recalculated from the 24-day
post-change window through the logged recalculation path. Nothing the
refused draft wanted was lost: order-level pass/fail drives the chart,
the check sheet keeps tallying marks by type for the Pareto re-runs, and
T-10's DPMO stays the descriptive summary for counts. The teaching in one
sentence: when a tool refuses your data by name, the fix is to bring the
right data, not to rename the data until the tool goes quiet.

## The refused fishbone — the same discipline at Analyze's door

The suite's flawed-example registry assigns T-15's pair to this demo, and
it ran live 2026-07-28, five weeks before the chart's. The draft
(`fishbone-flawed.json`) is the huddle board from the morning the Pareto
ranking landed: the unsigned-imposition mechanism and the unlabeled trays
marked **verified** with their evidence fields empty — the room was
unanimous, and the ranking was right there on the table. The engine's
answer, verbatim (HTTP 422 from `POST /artifacts/T-15/validate`, one
value error per consensus-verified cause, before any prescore ran):

> Value error, cause 'c-imposition': evidence is required (non-empty)
> when status='verified'
>
> Value error, cause 'c-trays': evidence is required (non-empty) when
> status='verified'

Where EXIT-11 is a routing guard, this bar is the schema itself: a cause
with `status: "verified"` and nothing in `evidence` cannot be constructed
at all (rubric R-ANA-02's anchor line — team consensus is not evidence).
That shape is worth staring at: the engine makes the classic flawed
fishbone — verified causes with zero evidence sitting on a saved board —
literally impossible to ship, so the honest nearby failure is this draft,
statuses claimed on confidence and refused at the door. The fix was one
afternoon of actual verification, not a softer word: the corrected board
(`fishbone-corrected.json`, saved as `print-fishbone`) attaches the
pointers the huddle already had — the check sheet's 67-of-139 trim tally,
the Pareto's own dataset export for wrong paper — and then does the work
the draft's statuses were only claiming: the prepress walk and the
40-traveler audit that turn "everyone agrees" into a 5-Why chain (proof
approval → imposition set from memory → an unwritten pre-flight step),
ending at the root the 2026-08-01 rollout memo's checklist targets, with
the labeled trays as its materials half. Ink and quantity stay candidates
in the tail; the shift split and rater drift leave as ruled-out with
their evidence retained on the board. One more honesty note the pair
makes visible: the Pareto share verifies that trim and wrong paper are
where the marks concentrate — the *categories* — while verifying the
*mechanisms* took the walk and the audit; the corrected board carries
both layers, each with its own pointer. The teaching in one sentence:
verified is a claim about evidence, not about agreement — when the
schema refuses the status, go get the evidence instead of softening
the word.
