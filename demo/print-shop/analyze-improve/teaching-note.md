# The refused chart, and what the refusal teaches

`chart-flawed.json` is the draft the engine refused, kept on purpose —
seeing the mistake is half the teaching (PLAN §4.4), and this demo's
flawed-then-fixed pair lives here, on the chart selector, the way the
coffee bar's lives on the charter. At the 2026-09-06 wrap-up, with the
recalculation of the monitoring chart on the table, the proposal was to
make the new chart richer: plot each day's **total failed-check marks**
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
