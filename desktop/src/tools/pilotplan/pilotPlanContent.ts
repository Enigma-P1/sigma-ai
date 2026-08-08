import type { HelperFrameContent } from "../helperFrameTypes";

/** T-19 Pilot Plan helper content. "What good looks like" restates the
 * rubric item that grades this tool -- R-IMP-02 (pilot design, owner of
 * EXIT-10) -- plus rubric §8's exit grading, one source of truth, no
 * parallel checklist (tier-a-done-means §2). */
export const pilotPlanHelperContent: HelperFrameContent = {
  toolId: "T-19",
  isPlaceholder: false,
  whatThisIs:
    "A small-study designer that enforces this product's method: one change at a time. The Improve loop is " +
    "rank the verified causes, fix the top one, prove it, check the remaining gap, take the next. That loop " +
    "is cheap -- every fix proves itself on real work, no test schedules. It is self-correcting -- the gap " +
    "tells you if your ranking was wrong. And every step yields a clean before/after story. Changing " +
    "several things at once -- throwing everything at the wall -- is exactly what this flow is built to " +
    "prevent, because you never learn what actually stuck. The plan you write here is the contract the " +
    "proof (T-20) is checked against.",
  whenToUse:
    "When T-18's ranked fix list has a #1 and you are about to touch the process. At the Coffee Bar: the " +
    "top-ranked fix addresses the drink-queue pileup's root (one machine head, batch sizes locked to one " +
    "drink at a time) -- say, pulling espresso shots in pairs for back-to-back milk drinks. The pilot is " +
    "designed before the first pilot morning: compared against the frozen 10-morning baseline (n=120, mean " +
    "8.41), threshold declared now, falsification line written now. Grinder rework (the #2 cause) waits its " +
    "turn -- that is the loop working, not slowness.",
  whenNotTo:
    "The classic misuse is the bundle: several fixes run as one pilot, then the result claimed for a " +
    "specific one. The tool refuses it by name -- EXIT-10 -- because nothing in a bundle is attributable. " +
    "Multiple candidate fixes become sequential pilots through the loop; a genuinely combined question goes " +
    "to the advisor, the v1.1 Experiment Planner, or a human expert. One honest carve-out: a declared " +
    "inseparable package (components that cannot be deployed apart) may run as one pilot, declared up front, " +
    "with attribution to the package only and every component listed -- an undeclared bundle, or component " +
    "credit claimed from a package pilot, stays EXIT-10's failure. Also not for changes already made: a " +
    "pilot designed after the change ran is a story, not a study.",
  fieldGuidance: [
    {
      field: "What are you changing? (one sentence)",
      good: "\"Pull espresso shots in pairs for back-to-back milk drinks\" -- one change, traceable to the #1 ranked fix.",
      bad: "\"Pair the shots, recalibrate the grinder, and re-lay the counter.\" (three changes -- EXIT-10 refuses the save, because no result could ever be attributed to any of them)",
    },
    {
      field: "+ Describe another change",
      good: "Used to see the refusal, then removed -- the affordance exists so you watch the engine say no by name instead of silently accepting a bundle.",
      bad: "A second change left in with the plan forced through elsewhere. (the exit is the method, not an obstacle)",
    },
    {
      field: "Comparison design + description",
      good: "Before period: the frozen baseline window, named exactly -- \"10 mornings, 2026-07-20 to 2026-07-31, n=120.\" Or a parallel unchanged group, named just as exactly.",
      bad: "\"We'll see how it compares.\" (a comparison chosen after results is a comparison chosen to flatter them)",
    },
    {
      field: "Who/what is included + how selected + honesty note",
      good: "\"All espresso orders, weekday 7:00-10:00 peak, both baristas\" -- and the honesty note says the quiet part: this is the morning crew we have, convenience, not randomization.",
      bad: "Inclusion left vague, selection unstated. (unit-selection bias is graded at 'stated honestly' -- hiding it is the failure, having it usually isn't)",
    },
    {
      field: "Success threshold + direction",
      good: "\"Mean handoff <= 7.0 min over the 5-morning pilot window, lower is better\" -- declared before data. A partial-gap target is honest: most single fixes recover part of the gap, and the loop handles the rest.",
      bad: "A threshold set -- or moved -- after seeing results. (declare the finish line before you run; moving it after is how teams lie to themselves, and it is the invalidating line)",
    },
    {
      field: "Expected analysis route + why",
      good: "Welch two-sample t: two independent windows of continuous handoff minutes. A forecast, not a lock -- T-20 routes the real data itself.",
      bad: "A route picked to guarantee a computable answer regardless of what the data turns out to be.",
    },
    {
      field: "Falsification line",
      good: "\"If mean handoff stays above 8.0 min across the 5 pilot mornings, pairing did not move the queue.\" Metric, threshold, window -- written while you still want to be wrong.",
      bad: "\"If it doesn't work.\" (no teeth -- nothing a reviewer could check; the prescore flags it)",
    },
    {
      field: "Confounder checklist (staffing, season, demand, measurement, other)",
      good: "All five answered now, with notes -- \"no staffing changes planned; fall semester starts mid-pilot, demand may rise.\" Cheap insurance: a confound named up front costs a sentence; discovered after, it costs the claim.",
      bad: "Reflex \"no\" on every row to keep the plan clean. (T-20 re-asks against what actually happened, and a contradicted 'no' reads worse than an honest 'yes')",
    },
  ],
  whatGoodLooksLike: [
    "One change per pilot, stated in one sentence -- multiple candidate fixes become sequential pilots " +
      "through the loop, or the named exit (EXIT-10), never a bundle claimed as attributable. A declared " +
      "inseparable package is the one carve-out: declared up front, components listed, attribution to the " +
      "package only, no component-level claim ever.",
    "The comparison is defined before running -- baseline period or parallel group, stated, with who/what " +
      "is included and how selected.",
    "Success threshold AND analysis plan are declared before data collection -- the engine stamps " +
      "declared_at at save; the stamp shows entry order, not observation order, so it supports the honesty " +
      "claim rather than proving it.",
    "The falsification line is filled in and substantive: what would prove this DIDN'T work, checkable by " +
      "a stranger.",
    "The confounder checklist is answered up front, to be re-answered at proof.",
    "The pilot is big and long enough to assess the declared threshold -- or the plan says plainly that it " +
      "isn't and treats the result accordingly.",
  ],
  commonMistakes: [
    "Running more than one change as one pilot and claiming the result for a specific fix -- EXIT-10 " +
      "ignored, and the phase conclusion built on it is void.",
    "Setting or moving the threshold after seeing results -- pre-declaration is the entire point.",
    "A falsification line that is a bare negation (\"if it doesn't improve\") -- if failure has no " +
      "recognizable shape, no result can ever count against the idea.",
    "Convenience selection left unstated -- say it, don't hide it; the grading line is honesty, not " +
      "sampling-theory rigor.",
    "Starting the second pilot while the first is unproven -- loop discipline slipping; the gap check " +
      "hasn't told you anything yet.",
    "Treating the declared_at stamp as proof of pre-declaration -- a spreadsheet defeats a timestamp; " +
      "credibility is a judgment the stamp merely informs.",
  ],
  source:
    "Method source: pilot discipline per PLAN §4.1 -- one change at a time as the product's method (rank, " +
    "fix one, prove, check gap, next), pre-declared threshold, falsification line, confounder checklist " +
    "(traceability matrix V.B; golden G-pilot-01). Exit registry §4/§4a: EXIT-10 declared at pilot, " +
    "enforced again at T-20's proof. Acceptance checklist: rubric R-IMP-02; per rubric §8, naming EXIT-10 " +
    "and splitting into sequential pilots is pass-level work -- pushing a bundle through is the failure.",
};
