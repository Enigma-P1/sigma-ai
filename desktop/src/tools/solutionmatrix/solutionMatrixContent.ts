import type { HelperFrameContent } from "../helperFrameTypes";

/** T-18 Solution Selection Matrix helper content. "What good looks like"
 * restates the rubric item that grades this tool -- R-IMP-01 (solution
 * selection) -- one source of truth, no parallel checklist
 * (tier-a-done-means §2). */
export const solutionMatrixHelperContent: HelperFrameContent = {
  toolId: "T-18",
  isPlaceholder: false,
  whatThisIs:
    "The tool that turns candidate fixes into a ranked fix list -- the queue the Improve loop works " +
    "through, one change at a time. Every solution must link to a verified cause from Analyze; impact and " +
    "effort ratings (1-5 each) place it on a live quadrant (quick win, major project, fill-in, thankless " +
    "task), and an optional weighted-criteria matrix adds a more precise ranking on top. The ranking " +
    "arithmetic is the engine's, never yours: linked solutions ordered by weighted total when scored, " +
    "impact and effort otherwise.",
  whenToUse:
    "When Analyze has handed over verified causes and you have real candidate fixes for the top one -- at " +
    "least two, so the matrix is a comparison, not a rubber stamp. At the Coffee Bar the ranked causes are " +
    "the drink-queue pileup ahead of the single espresso station (55% of the 40 delay tallies, and the 5-Why " +
    "root behind it: one machine head, batch sizes locked to one drink at a time) and grinder rework " +
    "re-pulls (25%). Candidates for the top cause might be a second machine head (major project) versus " +
    "re-sequencing to pull paired shots for back-to-back milk drinks on the head that exists (quick win) -- " +
    "the matrix is where those compete on stated ratings instead of in someone's gut.",
  whenNotTo:
    "The classic misuse is the solution-first project: a great idea with no verified cause behind it is a " +
    "guess wearing a plan's clothes, and piloting it anyway voids the Improve logic -- the rubric's " +
    "invalidating line. The tool flags unlinked solutions and keeps them out of the ranked list; the flag is " +
    "the method talking, not a formality to dismiss. Also not a menu: the output is a queue. Working item " +
    "#3 first because it looks easier, without a logged reason, is the ranking overruled by mood.",
  fieldGuidance: [
    {
      field: "Solution name + description",
      good: "\"Pull espresso shots in pairs for back-to-back milk drinks\" -- a concrete change someone could start Monday.",
      bad: "\"Improve espresso workflow.\" (a direction, not a change -- nothing here can be piloted, proven, or ranked)",
    },
    {
      field: "Linked verified cause(s)",
      good: "Checked against T-15's verified list -- the pairing change links to the drink-queue pileup and its one-head batching root.",
      bad: "Left unlinked because \"everyone knows it would help.\" (the flag fires, the solution never ranks -- a fix with no verified cause is a guess wearing a plan's clothes)",
    },
    {
      field: "Impact (1-5)",
      good: "5, with the basis stated in the description: it attacks the 4.5-minute drink-queue wait -- the biggest block of the 8.41-minute baseline.",
      bad: "A number with no stated basis. (unexplained ratings are the Needs-work line -- the grader can't tell scoring from wishing)",
    },
    {
      field: "Effort (1-5)",
      good: "2 for a sequencing change (training and a laminated card); 5 for the second machine head (capital, install, counter re-layout).",
      bad: "Effort rated low because you want the idea to win. (the quadrant is only as honest as its axes)",
    },
    {
      field: "Weighted criteria (optional)",
      good: "Criteria and weights declared before any scoring -- cost, speed-to-implement, disruption -- then every solution scored against all of them.",
      bad: "Weights adjusted after seeing the scores so the favorite lands #1. (the tool timestamps weights before scores; unusual, unexplained weights are the shape of a post-hoc rescue)",
    },
    {
      field: "Criteria scores (1-5 each)",
      good: "All criteria scored for a solution, or none -- a partial set never produces a trustworthy total, and the engine refuses to compute one.",
      bad: "Scoring only the criteria where the favorite shines.",
    },
  ],
  whatGoodLooksLike: [
    "At least two candidate solutions were considered for the top-ranked verified cause -- the matrix is a " +
      "comparison, not a rubber stamp for a pre-decided fix.",
    "Every solution links to a verified cause; the tool flags unlinked ones, and none survive to the " +
      "ranked list unresolved.",
    "Criteria and weights were set before scoring (impact/effort at minimum), and the scoring arithmetic " +
      "is the tool's -- no hand-computed totals.",
    "The output is a ranked fix list, and the #1 pick is the top scorer -- or the deviation carries a " +
      "logged reason.",
    "The list is treated as a queue: the top-ranked fix goes to the Pilot Plan (T-19) first, one change at " +
      "a time; the rest wait their turn through the loop.",
  ],
  commonMistakes: [
    "Piloting a solution unlinked to any verified cause -- the solution-first project this whole flow " +
      "exists to prevent, and the invalidator that voids the Improve logic.",
    "One candidate, rubber-stamped -- a matrix with nothing to compare decided nothing.",
    "Impact/effort ratings with no stated basis, so the quadrant is opinion wearing coordinates.",
    "Tuning weights after seeing the scores until the favorite wins -- the timestamps record the order, " +
      "and unusual unexplained weights read as a post-hoc rescue.",
    "Treating the ranked list as a menu -- skipping to a lower-ranked fix without a logged reason, which " +
      "quietly replaces the ranking with preference.",
    "Pasting remedy-advisor suggestions in wholesale without your own pruning -- the matrix ranks your " +
      "judgment, not a bot's brainstorm.",
  ],
  source:
    "Method source: standard impact/effort prioritization plus a weighted-criteria (prioritization) matrix, " +
    "this engine's own wording (traceability matrix V.B -- T-18 as the ranked implementation queue; II.D " +
    "names it the live prioritization matrix; golden G-solmatrix-01). Ranking computed by " +
    "artifacts/solution_matrix.py: linked solutions ordered weighted-total desc when fully scored, then " +
    "impact desc, effort asc; unlinked solutions listed separately, flagged, never ranked. Acceptance " +
    "checklist: rubric R-IMP-01.",
};
