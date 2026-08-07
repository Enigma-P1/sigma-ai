import type { HelperFrameContent } from "../helperFrameTypes";

/** T-03 Project Charter helper content. "What good looks like" is drawn from
 * the rubric items that grade this tool -- R-DEF-02 (problem statement,
 * anchor item), R-DEF-03 (goal + metrics), R-DEF-04 (scope/team/risks),
 * R-DEF-05 #3-4 (business-impact field), R-DEF-08 #1 (timeline) -- one
 * source of truth, no parallel checklist (tier-a-done-means §2). */
export const charterHelperContent: HelperFrameContent = {
  toolId: "T-03",
  isPlaceholder: false,
  whatThisIs:
    "The charter turns a picked project into a written commitment: what hurts and by how much, the target and " +
    "the date, who owns the process, what is in and out of scope, and what fixing it is worth. Every later " +
    "artifact -- baseline, causes, proof, control plan -- points back to this document.",
  whenToUse:
    "Right after the Project Picker clears, before any process mapping or data collection. Revisit it when " +
    "Measure contradicts it -- updating the charter with a logged edit is normal project work, not failure.",
  whenNotTo:
    "It is not the place to record the fix you already believe in. The classic misuse is a problem statement " +
    "with a solution or cause hiding inside it (\"operators need retraining\") -- if the charter already knows " +
    "the answer, the Analyze phase becomes theater and the project proves nothing.",
  fieldGuidance: [
    {
      field: "What",
      good: "Line 2 scrap rate averaged 6.2% in Q2, costing ~$40k. (states what hurts -- no cause, no fix)",
      bad: "Operators need retraining. (that's a solution, not a problem -- it presumes the cause before any analysis)",
    },
    {
      field: "Where",
      good: "Line 2, final assembly, building A. Specific enough to stand next to and watch.",
      bad: "The plant. (too broad to point at -- where would measurement even start?)",
    },
    {
      field: "When",
      good: "Throughout Q2 2026; worst on second shift.",
      bad: "Lately. (no period means no window to compare against later)",
    },
    {
      field: "Magnitude",
      good: "6.2 + \"% of units scrapped\" + \"Q2 2026\" -- a number, a unit, and a period, traceable to a record.",
      bad: "\"Way too high.\" (an adjective is not a magnitude -- nobody can tell later whether it improved)",
    },
    {
      field: "Goal statement",
      good: "Reduce line-2 scrap from 6.2% to 3% by Nov 30. (improvement-sized, dated, in the metric's terms)",
      bad: "Install the new labeler by Q3. (a goal that is itself a solution fails outright -- R-DEF-03)",
    },
    {
      field: "Metric name",
      good: "Line-2 scrap rate, % of units scrapped per the QC-log definition -- the measure the baseline will compute.",
      bad: "Quality. (not operationally defined -- no tool downstream can measure \"quality\")",
    },
    {
      field: "Baseline / Target / Unit",
      good: "Baseline 6.2, target 3, unit \"% of units\" -- the target sized against the problem's magnitude.",
      bad: "Target 0. (perfection-sized targets stall projects; improvement-sized targets finish them)",
    },
    {
      field: "Target date",
      good: "2026-11-30 -- a real date the timeline's phase milestones actually add up to.",
      bad: "ASAP. (not a date; nothing downstream can be planned or judged against it)",
    },
    {
      field: "Consequential (guardrail) metrics",
      good: "Line-2 throughput (units/shift) -- what must not get worse; it gets re-checked at the before/after proof.",
      bad: "(left empty -- a fix could quietly break something else and the proof would never catch it)",
    },
    {
      field: "In scope",
      good: "Line 2, day and second shift, product family A -- a named process segment.",
      bad: "The warehouse. (a building is not a scope; name the segment, line, or product family)",
    },
    {
      field: "Out of scope",
      good: "Supplier defects, line 1, packaging -- named so the project can't quietly grow.",
      bad: "(left empty -- if nothing is out, everything is implicitly in, and the project never ends)",
    },
    {
      field: "Process owner",
      good: "Maria Ortiz, line-2 supervisor -- the person who runs the process and can accept the control plan.",
      bad: "TBD / management / the team. (no owner means nobody can hold the gains -- the one gap R-DEF-04 fails outright)",
    },
    {
      field: "Team",
      good: "The people who touch the work, each with a role: operator, QC tech, supervisor.",
      bad: "A list of managers and sponsors who never touch the process.",
    },
    {
      field: "Timeline",
      good: "Phase-level milestones with dates that add up to the target date: Define 8/15, Measure 9/5, and so on.",
      bad: "One milestone: \"finish project.\" (a wish, not a plan -- R-DEF-08)",
    },
    {
      field: "Business impact",
      good: "$16k/year, basis \"Q2 COPQ total x 4\" -- the calculator's own number with the annualization basis stated.",
      bad: "A hand-typed figure that differs from the COPQ calculator. (a wrong number in the money story the sponsor will quote)",
    },
    {
      field: "Risks",
      good: "\"Key operator on leave during pilot\" -- likelihood and impact rated, a mitigation an owner could act on, owner named.",
      bad: "\"Lack of time.\" (generic, no mitigation, no owner -- and process failure modes belong in the FMEA, not here)",
    },
  ],
  whatGoodLooksLike: [
    "The problem statement states what, where, when, and magnitude -- and the magnitude is a number with a " +
      "unit and a time period, not an adjective.",
    "No cause language and no solution language anywhere in the problem statement or the goal -- nothing that " +
      "presumes why it happens or prescribes a fix.",
    "The stated magnitude is traceable to data the project holds. A labeled estimate is acceptable; a guess " +
      "presented as measurement is not.",
    "A reader outside the team could tell, from the statement alone, what hurts and by how much.",
    "The goal is SMART in substance: a target value for a named metric with a date, sized against the " +
      "problem's magnitude -- and the metric is the same measure the baseline will compute.",
    "At least one consequential (guardrail) metric is named -- what must not get worse while the primary " +
      "improves -- and it is checked again at the before/after proof.",
    "Scope-in and scope-out are both specific, and the team includes a named process owner -- the person who " +
      "runs the process, not a placeholder or a title-only sponsor.",
    "The risk block holds at least one real project risk with a likelihood/impact rating, a mitigation, and " +
      "an owner -- project risks like data access or seasonality, not process failure modes (FMEA's job).",
    "The business-impact field equals the COPQ calculator's output -- one number, one source -- and any " +
      "annualization states its basis (\"Q2 actuals x 4\").",
    "The timeline names phase-level milestones with dates consistent with the goal date -- a plan, not a wish.",
  ],
  commonMistakes: [
    "A solution or cause smuggled into the problem statement (\"need training,\" \"because of the old " +
      "fixture\") -- the single most common first-charter mistake, and the one the prescore flags.",
    "An adjective where the magnitude belongs (\"way too slow\"), or a number missing its unit or period.",
    "A goal that is itself a solution (\"install the new labeler by Q3\"), or a target with no date.",
    "A placeholder owner (\"TBD,\" \"management\") because the real owner hasn't been asked yet -- without an " +
      "owner the project cannot finish honestly.",
    "Empty scope-out and no guardrail metric, so the project quietly grows and a fix can break something " +
      "nobody is watching.",
  ],
  source:
    "Method source (traceability matrix I.A.2, II.C.2-II.C.7): standard LSS curriculum -- problem statement, " +
    "SMART goal, scope, owners and stakeholders, project risk; key-risks block per matrix correction A-4. " +
    "Solution-language and placeholder-owner checks are the rule-based heuristics PLAN §4.1 names. Acceptance " +
    "checklist: rubric R-DEF-02, R-DEF-03, R-DEF-04, R-DEF-05, R-DEF-08.",
};
