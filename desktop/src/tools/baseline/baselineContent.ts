import type { HelperFrameContent } from "../helperFrameTypes";

/** T-13 Baseline helper content. "What good looks like" is drawn from the
 * rubric items that grade this tool -- R-MEA-08 (stability before
 * capability, anchor), R-MEA-09 (capability/sigma reported honestly), and
 * R-MEA-11 (baseline statement + charter reconciliation, anchor) -- one
 * source of truth, no parallel checklist (tier-a-done-means §2). */
export const baselineHelperContent: HelperFrameContent = {
  toolId: "T-13",
  isPlaceholder: false,
  whatThisIs:
    "The tool that turns your collected data into the project's baseline, in an order the math requires: " +
    "spec limits and the operational definition first, then stability (an I-MR chart), then capability. " +
    "Stability comes first because capability math assumes one steady process produced the data -- if the " +
    "chart shows signals, your data mixes two or more behaviors, and an average over them describes " +
    "neither. Cp/Cpk and Pp/Ppk answer different questions: Cp/Cpk use short-term (within) variation -- " +
    "what the process could do at its steady best; Pp/Ppk use overall variation -- everything that actually " +
    "happened, drift included. And Cp only asks whether the spread fits the specs; Cpk also asks whether " +
    "the process is centered -- so Cpk is the honest one to lead with.",
  whenToUse:
    "Once the measurement check (T-12) has passed and real data exists in true collection order -- 20+ " +
    "points before control limits can be frozen. At the Coffee Bar: 25 peak orders' handoff minutes from " +
    "the time-study export, USL 5.0 from the customer's own words (\"if it's more than five minutes I just " +
    "go to the vending machine\"). The result is the measured baseline the charter's claimed 8.4 gets " +
    "reconciled against. This screen is for continuous measurements; if your data is pass/fail counts " +
    "(attribute data), the baseline lives on the p-chart (T-21, run diagnostically -- no freeze needed) " +
    "plus DPMO/sigma from the Yield Calculator (T-10) -- the matrix's own attribute pairing (§3a row 2.4.3).",
  whenNotTo:
    "The classic misuse is capability on an unstable process -- the defining invalidator of the whole " +
    "rubric. If the chart shows signals, EXIT-04 fires: \"you don't have a baseline yet.\" That is not a " +
    "punishment; it means the process changed while you watched, so no single number describes it yet. " +
    "Find what was different about the flagged points (the special causes), address that, collect again, " +
    "re-run. Until then the tool shows Pp/Ppk only, labeled performance-not-capability, and no Cp/Cpk claim " +
    "belongs anywhere -- including in your own write-up. Also not for shuffled data (stability needs true " +
    "time order), never before a passing measurement check, and not for pass/fail counts -- attribute data " +
    "baselines on the p-chart (T-21) with T-10 for DPMO/sigma, not on this screen's I-MR math.",
  fieldGuidance: [
    {
      field: "Dataset",
      good: "The time-study export or the POS import itself -- the same fingerprinted dataset the collection produced.",
      bad: "A re-typed summary file. (the provenance chain breaks, and nobody can verify the baseline came from the collected data)",
    },
    {
      field: "Column (numeric)",
      good: "handoff_minutes -- the charter metric's own measure in its own unit, so the baseline is the number the goal is written in.",
      bad: "A different measure than the charter's metric. (the project then proves something it never promised -- the mismatch the Measure tollgate exists to catch)",
    },
    {
      field: "USL (upper spec limit)",
      good: "5.0, with its source: the customer requirement from the VoC -- \"if it's more than five minutes I just go to the vending machine.\" Customer requirement, standard, or stated internal target; entered before results exist.",
      bad: "A limit picked after looking at the data so the process scores well. (reverse-engineered specs are the defining fake -- the baseline becomes fiction)",
    },
    {
      field: "LSL (lower spec limit)",
      good: "Left empty -- no customer minimum exists for handoff time. One-sided is honest: Cpk/Ppk compute on the bounded side and say so; Cp/Pp need both limits.",
      bad: "Inventing a lower limit for symmetry. (a fake spec changes every index computed against it)",
    },
    {
      field: "Operational definition confirmed",
      good: "Checked only after it's true as written: unit, boundaries, the moment measurement happens, the gauge -- two people following it would record the same value.",
      bad: "Checked as a formality to unlock the run button. (the check exists because a baseline of ambiguously-measured numbers is a baseline of noise)",
    },
    {
      field: "Rule 2 / Rule 3 (advanced, opt-in)",
      good: "Left off unless you accept the cost: the defaults are rule 1 (a point beyond 3 sigma) and rule 4 (8 in a row one side); each added zone rule raises the false-alarm rate.",
      bad: "Everything switched on \"to be thorough,\" then a week spent chasing signals that were noise.",
    },
    {
      field: "Apply the 1.5-sigma shift convention (advanced)",
      good: "Left at the convention default -- the printed sigma level always names which convention produced it. The shift is a reporting convention (it's how \"six sigma = 3.4 DPMO\" is defined), not physics.",
      bad: "Comparing your sigma level against a number computed under the other convention without checking the label. (same process, different-looking sigma, purely from the convention)",
    },
  ],
  whatGoodLooksLike: [
    "Spec limits are entered before capability, each with a source -- customer requirement, standard, or a " +
      "stated internal target -- never reverse-engineered from the data to flatter the result.",
    "The stability read is correct: signals identified, and your stable/not-stable call matches what the " +
      "chart shows.",
    "Not stable -> EXIT-04 honored: \"you don't have a baseline yet\" -- special causes investigated, " +
      "Pp/Ppk only, labeled performance-not-capability, and no Cp/Cpk claim anywhere, including in your own " +
      "prose.",
    "The data entered in true collection order -- stability analysis on shuffled data is meaningless.",
    "The within-vs-overall distinction (Cp/Cpk vs Pp/Ppk) is stated in your own summary, and Cpk is quoted " +
      "with Cp -- centering never ignored.",
    "Non-normal data -> the EXIT-05 caveat stays attached in your narrative, not just on the auto-printed " +
      "export. The normal-theory numbers still render -- the percentile supplement (n>=100) or observed " +
      "yield/DPMO rides alongside, labeled.",
    "The sigma level is reported with the 1.5-sigma shift convention named, exactly as the tool prints it.",
    "Measure exits with one baseline sentence -- metric, value, period, n, stability status, and the " +
      "capability-or-performance label, every element matching the computed results -- reconciled with the " +
      "charter: 8.4 claimed, X measured, and if they differ materially (>10%, or enough to change the " +
      "goal), the charter is revised by logged edit, never both numbers left standing.",
  ],
  commonMistakes: [
    "Claiming Cp/Cpk on an unstable process -- the rubric's defining invalidator; the tool blocks it, and " +
      "writing it into your own prose anyway is the same failure by hand.",
    "Setting spec limits after seeing the data so the process looks capable.",
    "Quoting Cp without Cpk -- a perfectly-wide but off-center process passes the half you quoted.",
    "Feeding the chart re-sorted or cleaned-of-order data -- the I-MR chart reads time; destroy the order " +
      "and the verdict is noise.",
    "The caveat that survives on the PDF but vanishes from the write-up -- or a charter saying 8.4 while " +
      "the baseline says something else, with no reconciliation on record.",
  ],
  source:
    "Method source: NIST/SEMATECH e-Handbook §6.1.6 (capability indices), §1.3.5 (normality: " +
    "Anderson-Darling, advisory only); Western Electric rules with default = rule 1 + rule 4 (zone rules " +
    "opt-in, false-alarm cost stated); traceability matrix III.F.1-III.F.4 and §4a: EXIT-04 (any default-rule " +
    "signal; >=20 points to freeze limits), EXIT-05 (percentile-method supplement at n>=100, observed " +
    "yield/DPMO below); sigma level carries the 1.5-sigma shift convention by name. Acceptance checklist: " +
    "rubric R-MEA-08, R-MEA-09, R-MEA-11.",
};
