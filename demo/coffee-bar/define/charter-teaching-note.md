# The flawed charter, and what fixing it teaches

`charter-flawed.json` is version 1 of the Coffee Bar charter, written the way
most first charters actually get written. `charter.json` is version 2, fixed.
Seeing the mistake is half the teaching (PLAN §4.4), so the flawed version
ships first and on purpose. Every flaw below trips a real engine prescore
flag; run both files through `POST /prescore/T-03` and compare.

## The six flaws, flag by flag

**1. The problem statement is a solution wearing a problem costume.**
"...because we only have one espresso machine, so baristas need training and
we should install a second machine." Flag: `problem_statement_solution_language`
(hits: because, training, install). Why it matters: the charter has already
decided the cause (one machine) and two fixes (training, a second machine)
before any data exists. If the real driver is pileup at handoff, the project
buys a $12k machine and changes nothing. The fix states only what hurts:
orders take too long from register to handoff, and what it produces.

**2. The goal is itself a solution.** "Install a second espresso machine and
train all baristas..." Flag: `goal_solution_language` (hits: install, train).
Why it matters: a goal names a target state for the metric, not a purchase
order. "Install the machine" can succeed while the wait gets worse. The fix:
reduce average order-to-handoff time from 8.4 to 5.0 minutes by October 31.

**3. The magnitude is vague.** "10" of nothing -- no unit, no period. Flag:
`magnitude_pattern` (missing unit and period). Why it matters: "about 10" is
an impression; 8.4 minutes average, Q2 2026 weekday peak, n = 412 orders, is
a baseline someone can later beat or fail to beat. The corrected number also
came out different from the guess -- that is why you measure.

**4. No consequential (guardrail) metric.** `consequential_metrics` is empty.
Flag: `consequential_metric_present`. Why it matters: the fastest way to cut
handoff time is to rush drinks and let quality slide -- and nothing in this
charter would notice. The fix names two guardrails: remake rate and barista
labor hours, both re-checked at the before/after proof (rubric R-DEF-03).

**5. The process owner is "TBD."** Flag: `owner_not_placeholder`. Why it
matters: this is the one gap rubric R-DEF-04 fails outright -- with no named
owner, nobody can accept the control plan, so the project cannot finish
honestly. The fix names Priya Shah, the shift lead who actually runs the
process, not the sponsor with the biggest title.

**6. The risk block is empty.** Flag: `risk_block_present` (matrix correction
A-4). Why it matters: this project has a known, dated threat -- fall semester
starts in late August and shifts morning demand, which could fake or mask an
improvement. Naming it up front (with a mitigation: record daily order counts,
compare like-for-like weeks) is what keeps the before/after proof honest.

## What the flags don't catch

The prescore is the floor, not the whole rubric. Version 1 also carries flaws
only judgment sees: a business impact of $50,000 that "feels like a lot"
(version 2 carries the COPQ calculator's $4,021 x 4 = $16,084/yr, one number,
one source -- rubric R-DEF-05), scope so vague the project could swallow the
whole cafe ("make mornings faster" vs. a named process segment with an
explicit out-of-scope list), and a one-milestone timeline ("finish project")
that is a wish, not a plan (R-DEF-08). Clean flags mean the obvious mistakes
are gone -- the "what good looks like" checklist still has to be read.
