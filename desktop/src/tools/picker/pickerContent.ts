import type { HelperFrameContent } from "../helperFrameTypes";

/** T-01 Project Picker helper content. "What good looks like" is drawn from
 * rubric R-DEF-01 (docs/green-belt-rubric.md) -- one source of truth, no
 * parallel checklist (tier-a-done-means §2). Routing rule: matrix §4a,
 * EXIT-01. */
export const pickerHelperContent: HelperFrameContent = {
  toolId: "T-01",
  isPlaceholder: false,
  whatThisIs:
    "Five questions that decide whether the problem in front of you is a workable first improvement project. " +
    "Based on your answers it routes you: full DMAIC for a problem that earns the rigor, the lighter PDCA " +
    "quick path for a small single fix, or a rescope (EXIT-01) when a criterion fails.",
  whenToUse:
    "First, every time, on any new problem -- before the charter, before any data collection. Come back and " +
    "re-run it if the problem changes shape mid-project.",
  whenNotTo:
    "Don't use it to rubber-stamp a project you've already committed to -- answering Yes five times just to " +
    "reach the next screen defeats the tool. The classic misuse is skipping it because the problem feels " +
    "important. \"Important\" and \"workable first project\" are different questions, and the pet project that " +
    "boils the ocean is the number-one way first projects die.",
  fieldGuidance: [
    {
      field: "Is the scope narrow enough to actually finish?",
      good: "Only line-2 scrap, not plant-wide quality. One line, one shift, one product family.",
      bad: "Improve quality across all lines. (too broad to finish -- nothing would ever count as done)",
    },
    {
      field: "Is there a measurable outcome?",
      good: "Scrap % per shift, already tracked in the QC log. A number that goes up or down.",
      bad: "People will feel less rushed. (no number means no baseline and no proof it worked)",
    },
    {
      field: "Can you actually get the data?",
      good: "QC log exports to CSV; the supervisor pulls it weekly. A named, real source.",
      bad: "Someone probably has that somewhere. (no named source means no data in practice)",
    },
    {
      field: "Does a process owner care about this?",
      good: "Maria Ortiz, line-2 supervisor -- she runs the process and asked for the project.",
      bad: "Management supports quality. (nobody named means nobody accepts the control plan later)",
    },
    {
      field: "Is the business impact plausible?",
      good: "Scrap ran ~$40k in Q2 per the scrap log. Rough dollars or hours is enough at intake.",
      bad: "Huge savings, guaranteed. (asserted with no basis -- not even a rough source)",
    },
    {
      field: "Route",
      good: "All five Yes and the problem earns the rigor: full DMAIC. Small single fix: PDCA quick path.",
      bad: "Full DMAIC with a criterion answered No. (that's EXIT-01 -- rescope or route out instead)",
    },
  ],
  whatGoodLooksLike: [
    "All five intake criteria are answered with project-specific content: scope narrow enough, a measurable " +
      "outcome, obtainable data, a named process owner who cares, and plausible business impact.",
    "The route matches the answers -- full DMAIC for a problem that warrants the rigor, the PDCA quick path " +
      "for a small single-fix problem, and EXIT-01 (rescope or route out) when a criterion fails.",
    "The outcome measure named here is the metric the charter and baseline actually carry -- or a logged " +
      "re-charter explains the change.",
    "Answers describe the real situation, not phrasing chosen to pass. Generic lines like \"we'll get data " +
      "somehow\" are the thin-answer pattern a grader marks Needs-work.",
  ],
  commonMistakes: [
    "Answering Yes across the board to reach the next screen -- launching full DMAIC with an EXIT-01 " +
      "condition present is the failure that voids everything built downstream.",
    "Boiling the ocean: scoping to the whole department because narrowing feels like giving something up.",
    "Impact asserted with no basis (\"huge savings\") instead of a rough number with a named source.",
    "Forcing full-DMAIC ceremony onto a small fix that belongs on the PDCA quick path.",
    "Naming one metric at intake, then chartering a different one with no logged explanation.",
  ],
  source:
    "Method source (traceability matrix II.A.1, V.C.3, VI.B.5): field-research intake criteria + standard " +
    "LSS curriculum; PDCA quick path per the Deming/Shewhart plan-do-check-act cycle. Routing rule frozen at " +
    "matrix §4a (EXIT-01: any criterion answered No). Acceptance checklist: rubric R-DEF-01.",
};
