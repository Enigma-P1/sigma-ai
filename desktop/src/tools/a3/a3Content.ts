import type { HelperFrameContent } from "../helperFrameTypes";

/** T-25 A3 Final Report + Tollgate Checklists helper content. "What good
 * looks like" restates the rubric items that grade this tool -- R-WRAP-01
 * (A3 final report), R-WRAP-02 (realized benefits, anchor), R-WRAP-03
 * (closure and lessons) -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). */
export const a3HelperContent: HelperFrameContent = {
  toolId: "T-25",
  isPlaceholder: false,
  whatThisIs:
    "A guided narrative builder for the one-page story of the whole project -- problem, baseline, causes, " +
    "countermeasures, proof, control -- told panel by panel as one argument, not fields stapled together. " +
    "Each panel pre-seeds from its source artifact; the seed is a starting point to edit into your own " +
    "words, with one hard rule: every number stays identical to its computed source, and no claim gets " +
    "upgraded in transit. Around the story sit the per-phase tollgate checklists and the closure block -- " +
    "objectives vs charter, lessons, open-item handoff, and the close check.",
  whenToUse:
    "At wrap, when the record exists to roll up. The Coffee Bar's story reads in six breaths: espresso " +
    "orders measured at 8.41 minutes against the customer's 5-minute line; stable but not capable (Cpk " +
    "-1.14) -- the wait is built in, not a bad day; two verified causes (drink-queue pileup, 55% of delay " +
    "tallies, dug to its root -- one machine head, batch sizes locked to one drink at a time -- and " +
    "grinder rework, 25%); one change piloted at a time through the ranked queue; the proof's own verdict " +
    "with its confounds attached; and the control plan holding the gains with a named owner. A sponsor who " +
    "saw none of the working artifacts should finish it convinced by the argument, not by the formatting.",
  whenNotTo:
    "Not before the artifacts exist -- the A3 rolls up the record; it cannot replace it. The classic " +
    "misuse is the upgrade in transit: \"proved\" where the proof said \"weakened,\" \"capable\" where the " +
    "baseline said \"performance,\" the failed first pilot quietly missing from the story. The deliverable " +
    "is where honesty pays or dies -- any A3 number that differs from its computed source invalidates the " +
    "report. And it is not a close-out formality: the closure block enforces real rules, including the " +
    "FMEA safety block below.",
  fieldGuidance: [
    {
      field: "Panel narrative (+ re-seed)",
      good: "The seed rewritten as prose for a sponsor -- numbers untouched, caveats kept: the baseline panel keeps \"stable, Cpk -1.14,\" the proof panel keeps its confound sentence.",
      bad: "The seed left verbatim, or panels pasted from the artifacts. (a field dump with punctuation is still a field dump -- the seed is a starting point, the narrative is your job)",
    },
    {
      field: "Realized benefits (COPQ re-run id, window, before/after, fix cost)",
      good: "The Wrap COPQ re-run over a stated window -- \"6 weeks post-rollout\" -- with realized-to-date computed from its before/after money, net of fix cost, and any annualized projection labeled separately as projection.",
      bad: "The Define-phase COPQ ($4,021/quarter at the Coffee Bar) claimed as realized. (that was the pain priced, not the money recovered -- benefits tie to the delta the proof measured, and claiming the whole gap when the fix recovered part of it is the wrong number leadership will repeat)",
    },
    {
      field: "Tollgate checklists",
      good: "Each phase's three questions answered honestly at wrap -- they are the phase reviews, and a \"no\" with a note beats a hollow \"yes.\"",
      bad: "All-yes by reflex on questions the record contradicts.",
    },
    {
      field: "Objectives vs charter",
      good: "Goal, achieved, remainder in numbers, consistent with the Improve conclusion -- partial met stated as partial is pass-side.",
      bad: "\"Goal essentially met\" over a computed remainder that says otherwise.",
    },
    {
      field: "Lessons",
      good: "Two or more with substance, at least one a genuine went-wrong or dead end -- documenting failures is this suite's brief, and a lessons panel of only wins is not lessons.",
      bad: "\"Communicate more.\" (generic enough to predate the project)",
    },
    {
      field: "Open items + owners",
      good: "The remaining gap, pending check-ins, and causes left on the table -- at the Coffee Bar, staffing shape stayed honestly investigating -- each handed to a named owner.",
      bad: "Open items listed with no owner. (unhanded is unowned, and unowned items fall through exactly as the project ends)",
    },
    {
      field: "Load latest FMEA / Mark project closed",
      good: "The close check run against the FMEA's own blocking flags before closing -- the Coffee Bar's severity-8 steam-scald row carries an action with an owner, so no block fires.",
      bad: "Closing past a live severity-9/10 safety row. (the engine refuses -- a project may not close on an unaddressed safety risk, and that block is correct, not bureaucratic)",
    },
  ],
  whatGoodLooksLike: [
    "The A3 reads as one argument -- problem, baseline, causes, countermeasures, proof, control -- with " +
      "every panel consistent with its source artifact: numbers identical, claims not upgraded in " +
      "transit.",
    "It works as narrative for a sponsor who saw none of the working artifacts -- prose telling the " +
      "story, not field dumps, no jargon the sponsor can't parse.",
    "Every quantitative claim traces to a provenance object carried in the export.",
    "The COPQ is re-run with post-improvement actuals over a stated window; realized-to-date is separated " +
      "from annualized projection, each labeled as what it is -- weeks of after-data with the window named " +
      "is the passing form for a first project.",
    "The benefit arithmetic ties to the measured improvement -- the delta the proof showed -- with the " +
      "costs of the fix netted, or at least named beside the benefit.",
    "Objectives-vs-charter reconciliation in numbers -- goal, achieved, remainder -- consistent with the " +
      "Improve conclusion.",
    "Lessons with substance: at least two, including at least one thing that went wrong or a dead end.",
    "Open items handed off with owners, and the project record complete -- every artifact the A3 cites " +
      "resolves in the project folder, loadable.",
  ],
  commonMistakes: [
    "The upgrade in transit: \"proved\" where the proof said \"weakened,\" \"capable\" where the baseline " +
      "said \"performance\" -- any A3 number differing from its computed source invalidates the report.",
    "Claiming the original COPQ as realized when the proof recovered part of the gap -- the wrong number " +
      "in the sentence leadership will repeat.",
    "The story skipping the failed first pilot the record shows -- the record is the story; edits to " +
      "history read as concealment.",
    "A lessons panel containing only wins.",
    "Marking the project closed against a live severity-9/10 safety block -- the refusal is the method " +
      "protecting someone, honor it.",
    "Panels as concatenated fields, or sponsor-facing prose written in tool jargon.",
  ],
  source:
    "Method source: A3 practice per traceability matrix II.C.6 (project documentation; goldens G-a3-01, " +
    "G-tollgate-01) and II.C.8 (closure: objectives vs charter, lessons learned). Panel seeds are " +
    "deterministic string composition from source artifacts (a3Seeding.ts) -- no invented numbers; " +
    "realized_to_date = the COPQ re-run's before - after, net of fix cost, computed by artifacts/a3.py " +
    "with provenance (rubric R-WRAP-02's arithmetic); close_blocked echoes the linked FMEA's own " +
    "severity-9/10 blocking flags (R-ANA-03's line, enforced at R-WRAP-03). Acceptance checklist: rubric " +
    "R-WRAP-01, R-WRAP-02 (anchor), R-WRAP-03.",
};
