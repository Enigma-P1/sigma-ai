import type { HelperFrameContent } from "../helperFrameTypes";

/** T-11 Data Collection Plan helper content -- one frame covering both
 * halves of the screen: the dataset import (upload, column types, quality
 * scan) and the sample-size guidance panel. "What good looks like" is
 * drawn from rubric R-MEA-05 (the plan) and the execution criteria of
 * R-MEA-06 this screen enforces -- one source of truth, no parallel
 * checklist (tier-a-done-means §2). */
export const dataImportHelperContent: HelperFrameContent = {
  toolId: "T-11",
  isPlaceholder: false,
  whatThisIs:
    "Where your data arrives and gets checked before anything is computed from it: upload a CSV or Excel " +
    "file, confirm what each column actually is (numeric or text), read the quality scan, and save -- the " +
    "saved dataset carries a fingerprint (SHA-256) every later result links back to. The sample-size panel " +
    "answers \"how much data is enough?\" before you collect: a rule of thumb for a stable baseline, a " +
    "calculator for a target precision, and a bias self-check.",
  whenToUse:
    "Before collecting: size the sample and declare your stratification factors as columns. After " +
    "collecting: import the raw export -- at the Coffee Bar, the POS order log, one row per order with " +
    "order-to-handoff minutes, shift, and order type -- and deal with what the quality scan finds before any " +
    "baseline runs on it.",
  whenNotTo:
    "This is not a data-cleaning tool: the scan finds problems, it never silently fixes them -- what you do " +
    "about a finding is recorded work, and edits made to the file before import are invisible to the suite, " +
    "so fix at the source and say what you fixed. The classic misuse is collecting whatever data is easiest " +
    "-- one friendly shift, one quiet afternoon -- and calling it the process. The bias checkboxes exist " +
    "because a convenience sample must say so.",
  fieldGuidance: [
    {
      field: "Upload a CSV or XLSX file",
      good: "The raw export itself -- one row per order, with the strata as columns (shift, register vs mobile).",
      bad: "A hand-built sheet of weekly averages. (averages hide the spread, and spread is what stability, capability, and every chart downstream need)",
    },
    {
      field: "Confirmed type (per column)",
      good: "handoff_minutes -> numeric, shift -> text -- checked against the sample values shown, not rubber-stamped.",
      bad: "Confirming \"numeric\" on a column whose samples read \"5 min\". (the continuous-vs-attribute call drives every downstream chart and test route -- get it wrong and everything after it is wrong by inheritance)",
    },
    {
      field: "Quality scan -- missing values",
      good: "\"handoff_minutes: 3 missing values\" -> find out why before analyzing. Missing rows are often the interesting ones -- the order so slow nobody logged it.",
      bad: "Analyzing anyway and letting the holes vanish silently. (a baseline computed on quietly-shrunk data is a claim about data you don't have)",
    },
    {
      field: "Quality scan -- non-numeric in a numeric column",
      good: "\"4 min\" or \"N/A\" sitting where a number should be: fix it at the source and note the fix, or re-type the column as text if it really is text.",
      bad: "Leaving it -- those cells can't be computed, so they become invisible holes wearing a number-column's name.",
    },
    {
      field: "Quality scan -- duplicate rows",
      good: "Find out whether the event really happened twice or the export doubled -- then keep or remove, with a note either way.",
      bad: "Ignoring duplicates. (double-counted evidence inflates n and every count built on it)",
    },
    {
      field: "Save dataset to project",
      good: "Save once the types are confirmed and the findings are dealt with -- the SHA-256 shown is the provenance anchor later results cite.",
      bad: "Re-importing a hand-edited copy mid-project with no note about what changed between versions.",
    },
    {
      field: "What are you sizing? (mean / proportion)",
      good: "\"A mean\" for a continuous metric like average order-to-handoff minutes; \"a proportion\" for a rate like % of orders remade.",
      bad: "Sizing a proportion for a time metric because rates feel simpler. (match the calculator to your metric's actual data type)",
    },
    {
      field: "Confidence level",
      good: "95% -- the default; state it with the answer.",
      bad: "Dropping to 90% purely to shrink the n the calculator asks of you.",
    },
    {
      field: "Planning estimate of spread (SD)",
      good: "2.1 minutes, from a 15-order pilot sample -- a stated basis, even if rough.",
      bad: "A number typed to make n come out small. (the answer inherits the guess -- label a guess as a guess)",
    },
    {
      field: "Planning estimate (%)",
      good: "50% if you have no prior estimate -- the conservative default that can only oversize, never undersize.",
      bad: "A hopeful low defect rate with no basis, which undersizes the sample exactly when you know least.",
    },
    {
      field: "Margin of error",
      good: "±0.5 minutes -- precise enough to matter against an 8.4 -> 5.0 minute goal.",
      bad: "±3 minutes on a 3.4-minute gap. (the answer then can't see the question)",
    },
    {
      field: "Bias self-check (convenience / one shift / one operator / short window)",
      good: "Ticked honestly -- each tick prints a plain warning that travels with the plan, and a labeled convenience sample is still usable, carefully.",
      bad: "Left unticked because ticking looks bad. (an unlabeled convenience sample presented as the process is how projects fool their own authors)",
    },
  ],
  whatGoodLooksLike: [
    "The operational definition passes the two-people test as written -- unit, boundaries, the exact moment " +
      "measurement happens, and the gauge named -- so two people following it would record the same value. " +
      "(Write it down with the plan; the baseline makes you confirm it before running.)",
    "The data type is identified correctly -- continuous vs attribute/count -- and each imported column's " +
      "confirmed type matches its real contents. This one call drives every downstream chart and test route.",
    "Stratification factors (shift, machine, operator, day...) are chosen for suspected sources of " +
      "difference and captured AS COLUMNS in the data, so later tools can split on them.",
    "The sample-size guidance was consulted: planned n stated with its rationale (rule of thumb or " +
      "calculator), and achieved n is compared against it later, shortfalls named.",
    "Who collects, where, when, and how is stated -- including the bias check: if it is a convenience " +
      "sample, the plan says so.",
    "Quality-scan findings -- missing, non-numeric, duplicates -- are addressed with a note saying what was " +
      "done, never silently fixed or silently ignored.",
  ],
  commonMistakes: [
    "Importing a pre-summarized sheet (averages per day) instead of raw rows -- the spread every later tool " +
      "needs is already gone.",
    "Rubber-stamping the inferred column types without reading the sample values next to them.",
    "Treating the quality scan as a formality and analyzing over the holes.",
    "No planned n -- collecting until the chart \"looks stable,\" which is how bias picks your sample size.",
    "An unlabeled convenience sample: one easy shift, one friendly operator, presented as the whole process.",
  ],
  source:
    "Method source (traceability matrix III.D.1, III.D.2): standard data-type and sampling-plan practice per " +
    "the LSS curriculum; sample-size rules of thumb with plain-English framing; margin-of-error formulas are " +
    "the standard normal-approximation results, computed by the engine. The 20-point stable-baseline floor " +
    "is the matrix §4a EXIT-04 companion value. Acceptance checklist: rubric R-MEA-05, R-MEA-06.",
};
