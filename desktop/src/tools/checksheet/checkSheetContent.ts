import type { HelperFrameContent } from "../helperFrameTypes";

/** T-08 Check Sheet / Tally helper content. "What good looks like" is
 * drawn from rubric R-MEA-06 (data collection execution) plus the strata
 * half of R-MEA-05 this tool physically captures -- one source of truth,
 * no parallel checklist (tier-a-done-means §2). */
export const checkSheetHelperContent: HelperFrameContent = {
  toolId: "T-08",
  isPlaceholder: false,
  whatThisIs:
    "A tap-to-count tally for failures as they happen: define the categories and stratification fields once, " +
    "then tap a category each time the event occurs. Every tap is stamped with the time and the strata " +
    "toggles active at that moment, and the saved sheet exports straight to Pareto -- the tally IS the " +
    "dataset, nothing gets re-typed.",
  whenToUse:
    "During data collection, at the process, while it runs -- it works on a phone at the line. At the Coffee " +
    "Bar: one tap per remake as it happens (\"wrong milk,\" \"wrong size,\" \"order misheard\"), with shift " +
    "and register-vs-mobile as strata, through the same peaks the plan named.",
  whenNotTo:
    "Not for reconstructing counts from memory at the end of the week -- recalled tallies are guesses wearing " +
    "timestamps. And not for continuous measurements: a 7.9-minute handoff time belongs in the time study or " +
    "an imported dataset, not squashed into count buckets. The classic misuse is retro-tallying, then " +
    "re-typing the totals into a fresh spreadsheet -- both break the chain that makes the data believable.",
  fieldGuidance: [
    {
      field: "Category label",
      good: "\"Wrong milk used\" -- one specific, observable failure a tapper can recognize in the moment, categories that don't overlap.",
      bad: "\"Other / misc\" as a main category. (if \"other\" wins the Pareto, the categories were never really defined -- you learn nothing)",
    },
    {
      field: "Stratification field label",
      good: "\"Shift\" and \"Register vs mobile\" -- the suspected sources of difference, declared before tallying starts so later tools can split on them.",
      bad: "None declared. (after collection it is too late -- you cannot ask \"was it worse on mobile orders?\" of data that never recorded it)",
    },
    {
      field: "Strata toggles (active value)",
      good: "Set \"Station: espresso\" before you start tapping, and change it the moment you move -- each tap is stamped with what's active right now.",
      bad: "Toggles left on yesterday's value all morning. (every entry silently mislabeled -- the split you run later will lie)",
    },
    {
      field: "Tally tap",
      good: "One tap at the moment the failure happens -- the timestamp is the tool's, honest by construction.",
      bad: "Batch-tapping 11 remakes from memory at shift end. (the timestamps then say 10:58, the reality was spread across the peak, and the run chart inherits the lie)",
    },
    {
      field: "Entry note",
      good: "\"9:12 remake -- oat-milk order got 2%\" on the entry it explains; also the place to note why an entry was corrected.",
      bad: "Deleting an entry that \"looks wrong\" with no note anywhere. (untraceable edits are the one thing that makes a dataset unusable -- R-MEA-06's fail line)",
    },
    {
      field: "Send to Pareto",
      good: "Export once tallying is done -- Pareto reads the same dataset's category column directly.",
      bad: "Re-typing the counts into a spreadsheet to \"clean them up\" first. (a re-typed intermediate copy is exactly the break in the chain the rubric checks for)",
    },
  ],
  whatGoodLooksLike: [
    "Data was collected per the plan: same operational definition throughout, strata recorded on the rows, " +
      "timestamps present -- the tool stamps both; your job is to keep them honest by tapping in the moment.",
    "Achieved n is stated against planned n -- \"planned 15 mornings, got 11\" -- with any shortfall named, " +
      "not smoothed over.",
    "The collection artifact IS the dataset the Pareto and baseline run on -- exported, never re-typed.",
    "Anything corrected or removed carries a note saying what and why -- no silent edits, no vanished rows.",
    "Every declared category was actually exercised, or its zero count is real (you watched and it didn't " +
      "happen), not a category nobody remembered to use.",
  ],
  commonMistakes: [
    "Tallying from memory at the end of the day -- recalled counts with invented timestamps.",
    "\"Other\" as the biggest bucket, because the categories weren't built from what actually fails.",
    "Strata toggles left stale while the situation changed -- a whole morning logged to the wrong shift.",
    "Deleting entries that look wrong instead of noting what happened.",
    "Re-typing the tally into a fresh sheet before analysis, breaking the tally-to-dataset chain the tool " +
      "exists to protect.",
  ],
  source:
    "Method source (traceability matrix III.D.2): standard LSS check-sheet practice -- categories defined up " +
    "front, events recorded at occurrence, stratification captured with each mark. Timestamps and strata are " +
    "stamped by the tool; the export feeds T-14's Pareto with zero re-entry. Acceptance checklist: rubric " +
    "R-MEA-06, plus the stratification-as-columns requirement of R-MEA-05.",
};
