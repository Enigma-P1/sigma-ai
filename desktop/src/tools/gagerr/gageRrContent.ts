import type { HelperFrameContent } from "../helperFrameTypes";

/** T-35 Gage R&R helper content. "What good looks like" is drawn from
 * rubric R-MEA-07, the same anchor item T-12 answers to — one source of
 * truth, no parallel checklist (tier-a-done-means §2). The 10%/30% bands
 * and the 5-category floor quoted below are the frozen convention values
 * in stats/gage_rr.py; they change only by logged decision. */
export const gageRrHelperContent: HelperFrameContent = {
  toolId: "T-35",
  isPlaceholder: false,
  whatThisIs:
    "The full study T-12 routes out of. Several operators each measure the same set of parts, several times " +
    "each, and the engine splits the variation you observed into the part of it that is the parts and the " +
    "part of it that is the measuring. Measuring error splits again: repeatability is one person getting a " +
    "different answer twice on the same part (the equipment); reproducibility is two people getting different " +
    "answers on the same part (the operators). The headline is %GRR — measurement error as a share of either " +
    "the study's own variation or the tolerance you have to hold. Bands, frozen: 10% or less acceptable; over " +
    "10% up to 30% marginal; over 30% not fit for the job. The second number that matters, and the one people " +
    "skip, is distinct categories: how many non-overlapping groups this gauge can sort these parts into. Below " +
    "5 the gauge sorts rather than measures, and a change smaller than one category is invisible to it no " +
    "matter how good the percentage looks.",
  whenToUse:
    "When the measurement is the thing in question and more than one person does it. That covers most of " +
    "manufacturing inspection and a good deal of service work: two nurses timing the same handoff, three " +
    "inspectors gauging the same bore, two auditors scoring the same file. Run it before the baseline, in " +
    "Measure — the same slot T-12 occupies — and re-run it after any change to the gauge, the fixture, or the " +
    "operational definition. Also run it when T-12 passes but people still argue about the numbers: T-12 " +
    "cannot see operator-to-operator disagreement at all, so a clean repeatability% and a shop floor that " +
    "does not trust the data is exactly the signature this study is for.",
  whenNotTo:
    "Not for a single operator — with one person there is no reproducibility term, and the honest tool is " +
    "T-12, which says so on its face. Not for pass/fail judgments: this is a variance decomposition and it " +
    "needs measured numbers; two raters judging good/bad is T-12's attribute path (% agreement plus kappa). " +
    "Not on parts that are all alike — the percentages here are ratios against the part-to-part variation in " +
    "THIS study, so a study run on ten parts off the same pallet understates part-to-part, overstates %GRR, " +
    "and no arithmetic on this screen can detect it. And not as a substitute for the questions a crossed " +
    "study genuinely cannot answer: bias against a known standard, linearity across the range, and drift over " +
    "months are separate studies, and they are still EXIT-03.",
  fieldGuidance: [
    {
      field: "Parts",
      good: "10 parts pulled to span what production actually produces — a few near each spec limit, the rest across the middle.",
      bad: "10 parts off the top of one pallet. (they measure alike, part-to-part collapses, and the gauge looks far better than it is)",
    },
    {
      field: "Operators",
      good: "3 people who really do this measurement on shift, each measuring blind to what the others recorded.",
      bad: "The two most careful people on the team. (the study then describes a measurement system nobody uses)",
    },
    {
      field: "Trials",
      good: "3 repeats per person per part, in randomized order, with the part re-presented each time — re-clamped, re-seated, re-read.",
      bad: "Reading the same display twice without disturbing the setup. (that measures the display, not the measurement)",
    },
    {
      field: "Tolerance width",
      good: "USL minus LSL as a single number — a 0.5 mm tolerance entered as 0.5, from the drawing or the customer requirement.",
      bad: "Left blank when a spec exists. (the study then answers whether the gauge can see the process vary, not whether it can police the spec — the question actually being asked)",
    },
    {
      field: "Interaction handling",
      good: "Let the engine decide, and read what it decided. Pooling is the convention when operator x part is not significant at 0.25.",
      bad: "Forcing pooling to make the number look better. (the two models give visibly different %GRR, and the report names which one produced it)",
    },
  ],
  whatGoodLooksLike: [
    "The study ran before the baseline was trusted, and the verdict was obeyed: acceptable → proceed; marginal → proceed carrying the caveat into the narrative; unacceptable → stop, fix the measurement, re-run (EXIT-02). Taking that stop is Pass-level work.",
    "The denominator is named. %GRR of tolerance and %GRR of study variation answer different questions and a gauge can clear one and fail the other — whichever is quoted, it is quoted as which one it is.",
    "Distinct categories is reported alongside the percentage, not instead of it, and a study below 5 is described as a sorting tool rather than a measuring one however good the percentage looks.",
    "The parts are stated to span the real range of production, because every percentage here is a ratio against the part-to-part variation this study happened to see.",
    "Clamped components and the pooling decision are carried into the narrative rather than quietly dropped — both change what the number means.",
    "Questions this study still cannot answer — bias, linearity, stability over time — are named and routed out (EXIT-03), not improvised around.",
  ],
  commonMistakes: [
    "Parts chosen for convenience instead of range. This is the single most common way a Gage R&R flatters a gauge, and it is invisible in the arithmetic.",
    "Operators who know what they, or the last person, recorded. Once the study stops being blind it measures memory.",
    "Reading the same setup twice and calling it a repeat. A trial has to include the whole act of measuring — presenting, seating, reading.",
    "Quoting %GRR of study variation as if it were %GRR of tolerance, or shopping between them for the friendlier number.",
    "Treating a passing %GRR with 3 distinct categories as a pass. It is not: the gauge cannot resolve the improvement the project is about to try to prove.",
    "Blaming training for a large reproducibility term before looking at whether operator x part interaction was significant — that pattern is usually the method or the fixture, not the people.",
    "Running this instead of fixing an obviously broken measurement. If the operational definition is ambiguous, the study will faithfully quantify the ambiguity and cost a day doing it.",
  ],
  source:
    "Method: two-way crossed ANOVA with interaction; variance components from expected mean squares, negative " +
    "components clamped to zero and reported as clamped; interaction pooled into repeatability when not " +
    "significant at alpha = 0.25; ndc = sqrt(2) x sigma_part / sigma_GRR, truncated. Structure follows " +
    "NIST/SEMATECH §2.4 (gauge studies). The 10%/30% acceptance bands and the 5-category floor are industry " +
    "threshold conventions, frozen in stats/gage_rr.py; the verdict wording is this engine's own. Rubric: " +
    "R-MEA-07. Exits: EXIT-02 (fail → fix the measurement, re-run), EXIT-03 (bias, linearity, stability — " +
    "studies this tool still does not run).",
};
