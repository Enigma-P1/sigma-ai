import type { HelperFrameContent } from "../helperFrameTypes";

/** T-15 Fishbone (6M) + 5 Whys helper content. "What good looks like" is
 * drawn from the rubric items that grade this tool -- R-ANA-01 (cause
 * exploration), R-ANA-02 (evidence discipline, the item Improve stands
 * on), and R-ANA-06 (the verified-cause hand-off) -- one source of truth,
 * no parallel checklist (tier-a-done-means §2). */
export const fishboneHelperContent: HelperFrameContent = {
  toolId: "T-15",
  isPlaceholder: false,
  whatThisIs:
    "A structured hunt for what causes your measured problem: six branches (People, Method, Machine, " +
    "Material, Measurement, Environment) force you to look wider than your first suspect, and \"ask why " +
    "again\" chains dig each promising cause down toward something you could actually fix. Every cause " +
    "carries a status that says how much you actually know: a *candidate* is a proposal with an empty " +
    "evidence field; once evidence shows the condition exists (a dated observation, a check-sheet split) " +
    "it is *investigating* -- supported, but not yet proven to drive the gap; it becomes *verified* only " +
    "when evidence ties it to the measured gap itself. That three-step ladder -- proposed, supported, " +
    "confirmed for action -- is the tool's spine, because Improve is allowed to act only on verified causes.",
  whenToUse:
    "Right after Measure hands you a baselined gap, before anyone proposes a fix. The effect at the head " +
    "of the fish is that measured gap: at the Coffee Bar, \"espresso orders take a measured 8.4 minutes " +
    "register-to-handoff against the customer's 5-minute line\" -- not \"customers are unhappy\" (a " +
    "symptom) and not \"the espresso station is slow\" (a pre-decided answer). Then go wide before you go " +
    "deep: the Coffee Bar board carries eleven causes across all six branches before its 5-Why chain digs " +
    "the drink-queue pileup down to \"one machine head, batch sizes locked to one drink at a time.\"",
  whenNotTo:
    "Not a voting board. The classic misuse is marking a cause verified because everyone in the room " +
    "nodded -- \"team consensus\" moves nothing past candidate, and the schema enforces it: the tool will " +
    "not save a verified cause without an evidence pointer. The bar for evidence is not a formal test " +
    "every time; it is data or observation a reasonable person would accept as showing the cause operates " +
    "-- a dated gemba note, a check-sheet split, a stratified Pareto. \"We all agree the grinder is the " +
    "problem\" clears no bar at all; \"10 of the 40 tallied delays are grinder re-pulls (check sheet, " +
    "Jul 20-31)\" clears it. Also not for exploring causes of a problem you haven't measured yet -- an " +
    "effect with no baseline number is a brainstorm, not an analysis.",
  fieldGuidance: [
    {
      field: "Effect statement",
      good: "The baselined problem in its measured form: \"Espresso orders average 8.4 minutes register-to-handoff against the 5.0-minute customer line (n=120, stable, Cpk -1.14).\"",
      bad: "\"Slow service\" or \"the espresso station can't keep up.\" (the first is a symptom with no number; the second smuggles the answer into the question)",
    },
    {
      field: "Charter link",
      good: "Linked to the project charter, so the effect is checkably the charter's problem, not a drifted restatement.",
      bad: "Left unlinked on a project that has a charter. (nothing then ties this diagram to the problem the project promised to solve)",
    },
    {
      field: "Cause",
      good: "A condition or mechanism that exists in the world: \"grind setting drifts after mid-peak hopper refills.\"",
      bad: "\"No second espresso machine.\" (an absent solution wearing a cause costume -- it names the fix you already want, not what is happening; the prescore flags 'no X' / 'lack of X' phrasing)",
    },
    {
      field: "Branch",
      good: "The 6M category the mechanism genuinely lives in -- and at least four branches carrying project-specific causes before any chain goes deep.",
      bad: "Every cause piled on one branch. (a single pre-decided path with decoration, which is the thing the six branches exist to prevent)",
    },
    {
      field: "Status",
      good: "Moved up only as evidence arrives: candidate (proposed, nothing yet) -> investigating (evidence shows the condition exists) -> verified (evidence ties it to the gap). Ruled out when evidence argues against -- status changed, cause kept on the board.",
      bad: "Verified because the team agrees, or a dead candidate quietly deleted. (an assumption wearing a verification badge is the rubric's named invalidator; a deleted dead end gets re-argued next month)",
    },
    {
      field: "Evidence",
      good: "A pointer to the thing that shows this cause operating: the check sheet (22 of 40 delay tallies are drink-queue backlog), a T-17 test result, a dataset, or a dated observation note naming where and when.",
      bad: "\"Everyone knows this\" or a restatement of the cause in different words. (evidence must pertain to *that* cause's mechanism -- one strong verification does not wave through its neighbors)",
    },
    {
      field: "Ask why again (5 Whys)",
      good: "A chain at least three deep on the leading candidates, each answer actually explaining the level above, ending at something actionable: cups pile up -> the single station drains one drink at a time -> one brew head, batch sizes locked.",
      bad: "A chain that jumps tracks (\"why late? -> because morale\") or stops at the first comfortable answer.",
    },
  ],
  whatGoodLooksLike: [
    "The effect is the baselined problem -- the measured gap in its own units, matching the charter, not a " +
      "convenient symptom of it.",
    "At least four of the six branches carry project-specific candidate causes, phrased as conditions or " +
      "mechanisms -- textbook generics (\"training,\" \"communication\") name nothing anyone can verify.",
    "5 Whys runs on the leading candidates: each chain at least three levels deep or ending at a named " +
      "actionable cause, with every \"why\" actually explaining the level above it.",
    "Every cause's status matches its evidence: verified means the attached evidence ties this cause to the " +
      "gap; investigating means the condition is shown to exist but not yet tied; candidate means proposed, " +
      "and the \"no evidence yet\" chip stays visible until that changes.",
    "Evidence meets the reasonable-person bar: a dated observation with place and time, a check-sheet " +
      "split, a stratified view, or a T-17 result -- and causes claiming a measured difference cite the " +
      "test or chart that shows it, never an eyeballed pair of averages.",
    "Ruled-out causes stay on the board with the evidence that ruled them out -- the Coffee Bar keeps " +
      "\"register hardware lag\" visible with its 0.8-minute step read, so nobody re-litigates it.",
    "The exit hand-off is honest: the verified-causes summary lists only verified causes with their " +
      "evidence pointers, and your ranking of them against the gap states its rationale (Pareto share, " +
      "effect size, frequency) -- Improve consumes that list and nothing else.",
  ],
  commonMistakes: [
    "Marking a cause verified on team consensus -- the rubric's defining invalidator for this phase; " +
      "Improve then builds on an assumption wearing a verification badge.",
    "Causes phrased as absent solutions (\"no barcode scanner,\" \"lack of staff\") -- name the mechanism " +
      "instead, or you have written your fix wishlist twice.",
    "One branch explored deeply, five left empty -- the diagram becomes decoration around the answer you " +
      "walked in with.",
    "Evidence fields that restate the cause in different words, or observation notes with no date and " +
      "place -- neither survives a reasonable person asking \"how do you know?\"",
    "Deleting a dead-end cause instead of marking it ruled out -- the board should show what was " +
      "considered and rejected, or the same idea returns in a month.",
  ],
  source:
    "Method source: standard Ishikawa 6M fishbone and 5-Why practice (traceability matrix IV.C.2); the " +
    "candidate -> supported -> confirmed-for-action evidence ladder is rubric R-ANA-02's three-state " +
    "vocabulary (this tool's status words: candidate, investigating, verified, ruled out), with " +
    "verified-requires-evidence enforced at schema level, never by honor system. Acceptance checklist: " +
    "rubric R-ANA-01, R-ANA-02, R-ANA-06 (the verified-cause hand-off Improve consumes).",
};
