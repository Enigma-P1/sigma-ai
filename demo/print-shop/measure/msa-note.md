# Measurement check — two raters, two rounds, one definition fix

The metric is a judgment call: a person decides whether an order passes four
named checks. Before a judgment-call metric earns a baseline, the check that
matches it is two-rater attribute agreement — kappa with % agreement, the
engine's T-12 attribute path — not a gauge study, because there is no gauge.
`msa-round1.json` and `msa-round2.json` are versions 1 and 2 of the same
artifact (`print-msa`), both engine echoes: the `result` block (kappa, %
agreement, verdict) is server-recomputed from the stored judgments on every
validate, so a hand-edited verdict has nothing to overwrite. The study ran
on the June 19–26 pre-study set — 50 held orders, salted with the week's
known rejects and borderline cases (15 of 50 questionable: 8 clear rejects,
7 boundary calls) so the judgment actually gets exercised; 50 random orders
at a ~9% reject rate would agree by boredom. Tessa Nguyen (rater A) and Omar Haddad (rater B) judged every
order independently at the same desk under the same lamp, sheets swapped so
neither saw the other's calls. Both rounds ran before the baseline window
opened — the point of the check is that the 21-day census is collected under
a measurement system already shown to work.

## Round 1 — marginal, and named as such

Engine verdict (2026-06-25, pasted from the echo): **% agreement 86.0, kappa
0.6067** (p_observed 0.86, p_expected 0.644), **verdict: marginal** — the
0.40–0.75 band of the frozen thresholds (matrix §4a), printed by the engine,
not read off a chart by hand. Marginal does not license proceeding as if
nothing happened: the disagreements have an address. Of the seven split
calls, five were rater A rejecting what rater B passed — all borderline ink
(faint streaks, single-pass banding you have to hunt for) — and two were
rater B failing a trim that measured right at 2 mm. The operational
definition, as first drafted, said "no visible smudge" and "trim within
2 mm" and left "visible to whom, from where" and "is exactly 2 mm in or
out" to the rater. Kappa found the softness in an afternoon; a baseline
built on it would have carried that noise as if it were process.

## The fix — written into the definition, not into anyone's memory

The fix went into `collection-plan.json`'s operational definition, where the
next rater can read it: ink fails on any smudge, streak, or banding **visible
at arm's length (~60 cm)** under the QC desk lamp on the top sheet or either
pull sheet — closer-than-arm's-length flaws are press notes, not rejects;
trim fails at **greater than** 2 mm from ticket dimensions, desk steel rule,
top/middle/bottom — exactly 2 mm passes. Nothing about the raters changed;
the instrument (the written test) did. That is the whole EXIT-02 route in
miniature: fix the measurement first, then re-run the check — and it is why
the plan's `two_people_confirmed` box is checked on the strength of round 2,
not on goodwill.

## Round 2 — acceptable, and what it licenses

Same 50 orders, re-presented two days later in a fresh shuffled order,
round-1 sheets sealed — both raters blind to their own first calls as well
as each other's. Engine verdict (2026-06-27): **% agreement 96.0, kappa
0.8645** (p_expected 0.7048), **verdict: acceptable** (≥ 0.75). The eight
clear rejects stayed both-fail in both rounds — the definition change moved
the boundary calls, not the obvious ones. Two splits remain, and they are
left as splits: one faint corner scuff, one single-pass gray band — logged
for the next definition review, not argued into agreement, because a 1.0
kappa produced by hallway consensus would be the measurement lying about
itself. Prescore on both versions: verdict recorded, result matches a fresh
recompute from the stored judgments, 50 items ≥ the 10-item guidance — all
pass, both rounds. What the acceptable verdict licenses: the baseline
window opens 2026-06-29, and every reject call in `orders.csv` is made
under the round-2 definition by the two raters who passed it.

## Why kappa and not just % agreement (in our own words)

Round 1's 86% agreement sounds fine; its kappa (0.61) does not, and the
kappa is the honest one. Two raters who both pass almost everything will
agree most of the time by chance alone — on this fixture, chance predicts
64.4% agreement (the engine's p_expected) before anyone exercises judgment.
Kappa scores only the agreement beyond that chance floor, which is why a
low-defect process can fake a high % agreement but cannot fake a kappa.
The engine prints both, always, and the demo quotes both, always — the pair
is the teaching. The single-operator caveat from the continuous path has an
attribute cousin worth stating too: this is two raters, one definition, one
week — it says nothing about how a third rater or a six-month drift would
score, which is what the periodic re-run in the control phase's cadence is
for.
