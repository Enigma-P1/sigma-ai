import type { HelperFrameContent } from "../helperFrameTypes";

/** T-17 guided hypothesis testing helper content. "What good looks like"
 * restates the rubric items that grade this tool -- R-ANA-04 (right test,
 * right route; exits taken when tripped) and R-ANA-05 (interpretation
 * discipline) -- plus rubric §8's honesty-exit grading rule, one source of
 * truth, no parallel checklist (tier-a-done-means §2). */
export const hypothesisHelperContent: HelperFrameContent = {
  toolId: "T-17",
  isPlaceholder: false,
  whatThisIs:
    "A guided selector that routes your comparison question to the right statistical test by rule -- what " +
    "are you comparing, paired or independent, continuous or count -- and shows the decision path it took. " +
    "The result is never a bare p-value: it always carries the effect size (how big the difference is), a " +
    "confidence interval (the plausible range for it), and a plain-English read. About that p-value: it is " +
    "the probability of seeing a difference at least this large *if there were truly none* -- nothing " +
    "more. It is NOT the probability your hypothesis is true, NOT the probability the result happened by " +
    "chance, and it says nothing about whether the difference is big enough to matter. A tiny p with a " +
    "trivial effect is a precisely measured shrug.",
  whenToUse:
    "When a cause or comparison claims a measured difference and you have the data to check it -- the " +
    "question stated first, in plain words, traceable to a verified cause or the goal. The Coffee Bar's " +
    "real question: \"are early-morning (7:00-8:30) and late-morning (8:30-10:00) wait times different?\" " +
    "-- two independent groups from the wait-times dataset's daypart column, one pre-declared primary " +
    "comparison. The engine routed it to Welch's t (its default for two independent samples -- no " +
    "equal-variance assumption to trip on) and found late mornings 0.45 minutes slower (p = 0.0165, " +
    "Cohen's d = -0.44, small). The effect-size-vs-goal read is the part that matters: the gap to close is " +
    "3.4 minutes, and even the early window runs 3.2 past the promise -- daypart is real but not the " +
    "driver; the causes operate all morning.",
  whenNotTo:
    "The tool itself declines nine named cases rather than compute an untrustworthy number -- and taking " +
    "the exit is doing it RIGHT, graded as pass-level work, never as an incomplete analysis. In plain " +
    "words: EXIT-06, your sample is below the routed test's floor (the refusal names the floor -- collect " +
    "more); EXIT-07, your chi-square table is too sparse to trust (collect more or honestly merge " +
    "categories); EXIT-08, three-plus measurements on the same unit is repeated-measures territory beyond " +
    "the paired design (human expert); EXIT-09, time-ordered values echo their neighbors " +
    "(autocorrelation), which breaks the independence every routed test assumes; EXIT-11, rates with " +
    "exposure or defects-counted-per-unit are Poisson-family data no v1 route carries honestly; EXIT-12, " +
    "more than one comparison in play -- declare one primary; EXIT-13 (an annotation, not a refusal), " +
    "ANOVA says the groups differ overall but fair pairwise comparison needs a correction that ships in " +
    "v1.1 -- you get the honest interim read; EXIT-14, three-plus markedly non-normal groups is " +
    "Kruskal-Wallis territory (v1.1); EXIT-15, a relationship between two continuous variables is " +
    "correlation/regression, deferred by name. Pushing past a raised exit -- an n-floor overridden, a " +
    "sparse chi-square computed elsewhere and pasted in -- is the failure, and it invalidates the phase " +
    "conclusion built on it.",
  fieldGuidance: [
    {
      field: "What are you asking, in your own words?",
      good: "\"Are early-morning and late-morning wait times different?\" -- the real project question, written before the data is touched, traceable to a cause on the fishbone or to the goal.",
      bad: "\"Run a t-test on the wait data.\" (a test name is not a question -- and a question written after seeing the result is test-shopping)",
    },
    {
      field: "What are you comparing? / Data type",
      good: "The honest structure: two independent groups of continuous measurements; paired only when the same units were measured twice; count/rate declared as count/rate even though that routes to an exit.",
      bad: "Declaring defect counts \"continuous\" to dodge EXIT-11. (the route computes, and the answer is wrong -- defects are counts on units, not measurements)",
    },
    {
      field: "Data (groups, pairs, or sample)",
      good: "Pulled from a saved dataset column so provenance rides along -- the Coffee Bar splits wait_minutes by the daypart stratification column the collection plan captured for exactly this moment.",
      bad: "Hand-typed summary averages. (the tests need the raw values, and a re-typed number has no chain back to the data)",
    },
    {
      field: "\"My data looks skewed or has outliers\" / \"collected in time order\"",
      good: "Checked when true: shape concern feeds the visible parametric-to-rank switch rule on small samples; time order lets the engine check autocorrelation (EXIT-09) -- the Coffee Bar's groups pass with r1 = 0.100 and -0.013 printed on the path.",
      bad: "Left unchecked to keep the route \"clean.\" (hiding structure from the selector doesn't remove it from the data -- it just makes the answer quietly wrong)",
    },
    {
      field: "Comparisons pre-declared / tests run",
      good: "1 and 1: one primary comparison, decided before looking, tested once. This is the discipline that keeps p meaningful -- run twenty comparisons and one lands under 0.05 by luck alone.",
      bad: "Testing every stratification column, then narrating the one that hit. (shotgun p-values -- EXIT-12 refuses the multiplicity, and the rubric calls the narrated winner an invalidator)",
    },
    {
      field: "\"This is my one pre-declared primary comparison\"",
      good: "Checked because it is true and stays on record in the saved artifact -- the declared-primary flag is what the grader reads.",
      bad: "Checked retroactively on the comparison that happened to come out significant. (that is the shotgun with paperwork)",
    },
  ],
  whatGoodLooksLike: [
    "The comparison question is stated first, in plain words -- what vs what, paired or independent, " +
      "continuous or count -- and it is the question the project needs answered, not one retrofitted to a " +
      "route.",
    "You can explain in your own words why the routed test fits -- what is compared, why " +
      "paired/independent, what the test can and cannot say -- and the explanation survives with the " +
      "tool's headline covered up. Restating the output is not an explanation.",
    "A tripped exit is taken: named (which EXIT, why the standard result would mislead), routed (collect " +
      "more, fix the design, or hand to a human expert), and honored downstream -- no later write-up " +
      "quietly claims what the exit declined to compute.",
    "One pre-declared primary comparison, visible in the saved artifact -- the declared-primary flag and " +
      "the tests-run count agree.",
    "Conclusions quote the effect size and confidence interval, not just p, and state practical " +
      "significance against the goal: \"late runs 0.45 min slower (d = -0.44, CI -0.81 to -0.08); the " +
      "gap is 3.4 min -- real, but not the driver.\"",
    "A non-significant result is narrated as \"no difference shown at this sample size\" -- never \"no " +
      "difference,\" which is a claim the test cannot make.",
    "Claims stay inside what was tested: a daypart difference is not proof of the mechanism you suspect " +
      "behind the dayparts.",
  ],
  commonMistakes: [
    "P-value theater: \"highly significant!\" over an effect too small to matter -- significance measures " +
      "detectability, the effect size measures importance, and the goal decides sufficiency.",
    "Reading p = 0.0165 as \"98.35% chance the difference is real.\" (p is computed assuming there is no " +
      "difference; it cannot tell you the probability there is one)",
    "Running several tests and narrating only the winner -- the question must come before the data, and " +
      "EXIT-12 exists because twenty shots at alpha = 0.05 land one hit by luck.",
    "Forcing a route past a triggered exit -- overriding an n-floor, or computing the refused test in a " +
      "spreadsheet and pasting it in. The rubric voids the phase conclusion that rests on it.",
    "The confidence interval printed by the tool but absent from your reasoning -- the CI is the honest " +
      "range of what the data supports, and a CI spanning \"trivial\" changes the conclusion.",
    "Treating \"not significant\" as \"proved equal\" -- a smaller true difference, or the same difference " +
      "with more data, could still turn up significant.",
  ],
  source:
    "Method source: NIST/SEMATECH e-Handbook ch. 7 (comparisons); scipy implementations; Welch's t as the " +
    "two-sample default (no equal-variance pretest), rank-route fallbacks with their own effect sizes " +
    "(rank-biserial, Hodges-Lehmann); traceability matrix §4/§4a frozen exit triggers (EXIT-06..09, " +
    "EXIT-11..15) with every routing decision printed, never hidden. Acceptance checklist: rubric " +
    "R-ANA-04, R-ANA-05; exit grading per rubric §8 -- recognizing a named exit is pass-level work.",
};
