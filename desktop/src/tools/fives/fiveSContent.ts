import type { HelperFrameContent } from "../helperFrameTypes";

/** T-23 5S Audit helper content. "What good looks like" restates the
 * rubric item that grades this tool -- R-CTL-05 (5S audit) -- one source
 * of truth, no parallel checklist (tier-a-done-means §2). */
export const fiveSHelperContent: HelperFrameContent = {
  toolId: "T-23",
  isPlaceholder: false,
  whatThisIs:
    "A scored workplace-organization audit. The five S's are Sort (remove what isn't needed), Set in Order " +
    "(a place for everything), Shine (clean enough that problems show), Standardize (make the first three " +
    "the normal state), and Sustain (keep it up without being chased). Each scores 0-5 per round, photos " +
    "carry the evidence, and the line that matters is the trend across rounds -- not any single score. The " +
    "lowest-scoring category gets an action with an owner, every round.",
  whenToUse:
    "When the project has a workplace-organization component. The Coffee Bar has one: the barista walks " +
    "~796 m per peak in the current layout, and the espresso station's physical state is part of how the " +
    "morning runs -- so the station gets audited on a recurring cadence alongside the control plan. The " +
    "honest starting picture is a mediocre score with photos that agree, improving round over round. Trend " +
    "over perfection: a 14/25 rising to 18 is a better artifact than a flat 25.",
  whenNotTo:
    "When the project has no workplace-organization component -- then this tool is N/A with the reason " +
    "recorded, not padding for the binder. The classic misuse is audit theater: straight fives across the " +
    "board, no photos, one round and never again. Straight fives across the board is a smell, and the " +
    "prescore flags uniform rounds -- not as an accusation, but as a question: do the photos really show a " +
    "5 in all five categories?",
  fieldGuidance: [
    {
      field: "Date / Area",
      good: "The actual area walked, named tightly: \"espresso station + under-counter storage.\"",
      bad: "\"The cafe.\" (an area too big to photograph honestly is an area too big to audit)",
    },
    {
      field: "Category scores (0-5) + notes",
      good: "Scored against the checklist anchors, so a 4 looks like the checklist's 4 -- and the note says why: \"Set in Order 2: syrup bottles unlabeled, backup pitchers stored across the walkway.\"",
      bad: "The same number in all five boxes by reflex. (uniform scores get flagged; five categories measuring different things rarely agree exactly)",
    },
    {
      field: "Photo",
      good: "One or more photos per round, taken wherever physical state carries the score -- the photo is the evidence the score is checked against.",
      bad: "No photos, scores from memory. (an unphotographed 4 is an opinion; spot-checking scores against photos is how this item is graded)",
    },
    {
      field: "Action for the lowest category + owner",
      good: "\"Label the syrup rail and move backup pitchers under the counter -- Marcus Webb, by Friday.\" The lowest score is where the next point comes from.",
      bad: "An action with no owner or date. (unowned actions are wishes)",
    },
    {
      field: "Recurrence (cadence note / next round due)",
      good: "A schedule (\"monthly, first Monday\") -- or 2+ completed rounds already making the trend real.",
      bad: "One audit at project close, never repeated. (a single point has no trend, and Sustain -- the fifth S -- is the one being tested)",
    },
  ],
  whatGoodLooksLike: [
    "A baseline audit is scored against the checklist, with photos wherever physical state carries the " +
      "score.",
    "Scores track the checklist's anchors -- spot-checked against the photos, a 4 looks like the " +
      "checklist's 4 -- and they are not uniform by reflex.",
    "Recurrence is real: a schedule exists, or the trend already has 2+ points.",
    "The lowest-scoring category carries an action with an owner and a date, every round.",
    "The trend line moves for honest reasons -- scores rise because the photos changed, not because the " +
      "scoring relaxed.",
  ],
  commonMistakes: [
    "Straight fives (or any identical score) across the board -- honest scoring is the whole value; five " +
      "different questions rarely have one answer, and the prescore says so.",
    "Scores without photos -- the evidence is the physical state, and the grader checks scores against " +
      "the pictures.",
    "One audit, no recurrence -- 5S is a habit being measured, not a certificate being earned.",
    "Actions with no owner or date on the lowest category -- the audit found the problem and then " +
      "shrugged.",
    "Chasing a perfect total instead of a rising trend -- a plateau at 25 teaches nothing; a climb from " +
      "14 shows the habit forming.",
  ],
  source:
    "Method source: standard 5S practice (Sort / Set in Order / Shine / Standardize / Sustain), this " +
    "engine's own checklist wording -- traceability matrix V.C.1 (T-23 as the scored audit; VI.B.4 notes " +
    "it is a live first-party audit); golden G-5s-01. Totals, lowest category, and the trend are computed " +
    "by artifacts/five_s.py; the uniform-scores flag is prescore/five_s.py's honesty check. Acceptance " +
    "checklist: rubric R-CTL-05 -- graded when the project has a workplace-organization component, " +
    "otherwise N/A with reason; 5S theater caps at Needs-work because it fakes no project number, but it " +
    "degrades the sustainment story.",
};
