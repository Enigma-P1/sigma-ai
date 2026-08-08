# Held-out golden scenarios (M6 eval gate)

## What "held-out" means

These are the two held-out golden scenarios PLAN §9 requires ("the Coffee
Bar demo plus two held-out scenarios — one attribute-data/defects, one
continuous-data/cycle-time"). **They are eval reference material, never
shipped as in-app examples.** The shipped demos (`demo/coffee-bar/`,
`demo/print-shop/`) teach by showing the answer; a held-out scenario
measures by withholding it — a scripted walkthrough or a human runner
gets the story, the pre-collected data, and the suite, and must produce
the project. If either scenario ever ships inside the app, its runs stop
measuring the suite and start measuring recall, so the wall between
`demo/` and `evals/scenarios/` is load-bearing: nothing in `demo/` may
reference these files, and nothing here ships to users.

Datasets are pre-collected and realistic on purpose (PLAN §9: "the test
measures the suite, not the tester's ability to gather data"). Untrained-
persona runs are scripted agents constrained to an untrained user's
knowledge — always labeled simulated, never presented as human results
(owner ruling 2026-08-07). The scoring instruments are the shipped rubric
(`docs/green-belt-rubric.md`) and the M0 matrix (`docs/traceability-
matrix.md`), both locked and externally AI-reviewed.

## The two scenarios

- **S-1 — `s1-helpdesk/`** (continuous / cycle time): Harborview Mutual's
  internal IT help desk, routine-ticket resolution time in business hours
  against an 8-business-hour promise. Baseline engine-verified **stable
  but not capable** (mean 26.71 h, one-sided Cpk −0.96, 127/127 over the
  promise); one dispatch-rule change recovers 104.2% of the charter gap
  (after mean 7.22 h, Cpk 0.12 — the mean promise kept, the every-ticket
  promise honestly not). No deliberate trap (`named_exit: null`); the
  continuous path's ordinary honesty gates all still apply. 21 tools in
  scope, 4 honest N/As.
- **S-2 — `s2-library/`** (attribute / defectives): the Ashford Public
  Library's Marion Street branch, re-shelving accuracy. **Carries the
  named-exit trap**: a plausible pre-existing misshelve log invites a
  straight-to-p-chart run, but the two log-keepers never shared a
  definition — the T-12 two-rater check fails at **kappa 0.336 (< 0.40,
  EXIT-02)**, and the honest run stops, fixes the definition per ground
  truth, passes round 2 at **kappa 0.878**, and only then baselines
  (p̄ 6.53%, stable) — discovering the broken log had under-counted the
  problem by roughly two-fifths. One pre-sort change then cuts the rate
  to 2.56% (121.7% of the halving gap). 22 tools in scope, 3 honest N/As.

Each scenario's `spec.md` carries machine-readable YAML frontmatter
(`scenario_id`, `data_type`, `in_scope_tools`, `na_tools` with reasons,
`eval_mode`, `named_exit`, `ground_truth`) and its own coverage table;
each `data/data-note.md` embeds the seeded generator verbatim (S-1 seed
32, S-2 seed 120) with the live-engine verification transcript.

## Collective coverage — all 25 Tier-A tools

PLAN §9 requires the scenario set to collectively exercise all 25 Tier-A
tools, with the matrix §1 inventory as the one authoritative count. The
shipped demos' coverage below is counted honestly from their READMEs: the
Coffee Bar threads 24 of 25 (everything except T-10 — a continuous
project with no yield counts); the Print Shop deliberately ships only the
tools whose attribute path differs (14), naming the rest as
not-duplicated. ✓ = in the scenario's declared scope; — = declared N/A
(reason in that spec) or, for the demos, not shipped in that thread.

| Tool | Coffee Bar | Print Shop | S-1 | S-2 | Covered by |
|---|---|---|---|---|---|
| T-01 Picker | ✓ | ✓ | ✓ | ✓ | 4 |
| T-02 COPQ | ✓ | ✓ | ✓ | ✓ | 4 |
| T-03 Charter | ✓ | ✓ | ✓ | ✓ | 4 |
| T-04 SIPOC | ✓ | — | ✓ | ✓ | 3 |
| T-05 VoC → CTQ | ✓ | ✓ | ✓ | ✓ | 4 |
| T-06 Process Map + Waste Walk | ✓ | — | ✓ | ✓ | 3 |
| T-07 Spaghetti | ✓ | — | — | — | 1 |
| T-08 Check Sheet | ✓ | ✓ | ✓ | ✓ | 4 |
| T-09 Time Study / Work Sampling | ✓ | — | — | — | 1 |
| T-10 Yield (FPY/RTY + DPMO) | — | ✓ | — | ✓ | 2 |
| T-11 Data Collection Plan | ✓ | ✓ | ✓ | ✓ | 4 |
| T-12 Measurement Check | ✓ | ✓ | ✓ | ✓ | 4 |
| T-13 Baseline | ✓ | ✓ | ✓ | ✓ | 4 |
| T-14 Pareto / Histogram / Run | ✓ | ✓ | ✓ | ✓ | 4 |
| T-15 Fishbone + 5 Whys | ✓ | ✓ | ✓ | ✓ | 4 |
| T-16 FMEA | ✓ | — | ✓ | — | 2 |
| T-17 Hypothesis | ✓ | ✓ | ✓ | ✓ | 4 |
| T-18 Solution Matrix | ✓ | — | ✓ | ✓ | 3 |
| T-19 Pilot Plan | ✓ | — | ✓ | ✓ | 3 |
| T-20 Proof + Gap | ✓ | ✓ | ✓ | ✓ | 4 |
| T-21 Control Charts | ✓ | ✓ | ✓ | ✓ | 4 |
| T-22 Control Plan + OCAP | ✓ | — | ✓ | ✓ | 3 |
| T-23 5S | ✓ | — | — | ✓ | 2 |
| T-24 Standard Work / SOP | ✓ | — | ✓ | ✓ | 3 |
| T-25 A3 + Tollgates | ✓ | — | ✓ | ✓ | 3 |

**Every tool is covered by at least one scenario — no hole to close.**
The claim also holds under the strict PLAN §9 trio (Coffee Bar + S-1 +
S-2, without the Print Shop): the Coffee Bar's only miss, T-10, is in
S-2's scope. T-07 and T-09 are exercised by the Coffee Bar alone — both
held-out scenarios N/A them honestly (queue-and-keyboard work has no
movement to trace; both metrics have no manual timing question), which is
itself part of what the evals grade: the rubric's N/A discipline requires
declared, reasoned exclusions, not padded scope.

## The named-exit requirement

PLAN §9: "**one held-out scenario deliberately requires a named exit** (a
measurement check that should fail, or a question needing a Black Belt) —
recognizing the exit is part of the pass bar, so honesty paths get graded,
not just the happy path." S-2 carries it as a measurement check that
should fail: the trap data (`prelog-daily.csv`) is schema-clean and
plausible, the T-12 round-1 kappa lands in the frozen fail band (matrix
§4a EXIT-02 attribute: < 0.40), and the pass bar is stopping, executing
the ground-truth definition fix, re-passing T-12, and baselining only on
the written-definition audit. The full trap design, what springs it, and
the exact engine verdicts are in `s2-library/spec.md` ("The trap, stated
plainly") — which is precisely why that spec must stay held out.

## The eval-mode wall

Some rubric items rest on organizational facts a time-boxed scenario
cannot supply — implementation beyond the pilot (R-IMP-05), an owner who
accepted the role (R-CTL-03), post-improvement actuals (R-WRAP-02). Each
spec supplies those facts as **scenario ground truth** (the named owner,
the window, the after-data), so those items grade consistency with that
truth, never invented fiction. PLAN §9, quoted, on why this never leaks
into real use:

> The wall is machine-readable and one-directional: scenario specs carry
> `eval_mode: plan_quality_only`, and **real-project grading reverts to
> organizational reality** — implementation must be real, the owner must
> be real, actuals must be actuals (Belt-panel round 2).

Both specs carry the `eval_mode: plan_quality_only` marker in
frontmatter; it applies to exactly the three items rubric §10.7a names
and nothing else.

## File shape and verification standard

```
evals/scenarios/
  README.md                      # this file
  s1-helpdesk/
    spec.md                      # story, arc, ground truth, coverage, frontmatter
    data/
      tickets-baseline.csv       # 127 rows, 20 business days
      tickets-after.csv          # 124 rows, the measured after window
      msa-repeats.csv            # T-12 test/retest pairs (12 items)
      delay-tallies.csv          # T-08 check-sheet marks (127)
      data-note.md               # generator (seed 32) + engine transcript
  s2-library/
    spec.md
    data/
      prelog-daily.csv           # the bait (15 days, two private definitions)
      msa-round1.csv             # T-12 round 1 -> kappa 0.336, FAIL
      msa-round2.csv             # T-12 round 2 -> kappa 0.878, acceptable
      baseline-audit.csv         # 21 days x 3 sections, written definition
      baseline-defect-marks.csv  # 90 marks
      after-audit.csv            # 24 days x 3 sections
      after-defect-marks.csv     # 39 marks
      data-note.md               # generator (seed 120) + engine transcript
```

Verification standard (same craft bar as the demo datasets): generators
are seeded and embedded verbatim in the data-notes; every statistic a
spec or note claims was run through the live engine after generation and
pasted from the response — stability and freeze verdicts, kappa bands
(including the deliberate failure), capability indices, Pareto vital-few
calls, test statistics, sample-size floors. The generators only mirror
engine rules to search seeds; **the binding verdicts are the engine's**.
When a future engine change shifts any of these numbers, the walkthrough
goldens built on these scenarios are the diff that catches it.
