import type { HypComparisonType, HypDeclaredDataType, HypothesisQuestion } from "../../api/types";

/** Local UI-only state for T-17's data-entry fields -- how a group's
 * numbers got onto the screen (typed, or pulled from a project dataset,
 * optionally filtered by a second column's value). Kept separate from
 * HypothesisQuestion (api/types.ts): the source bookkeeping (which
 * dataset/column/filter) never travels to the engine -- only the resolved
 * values, or an official column ref, do (hypothesisRequestBuilder.ts). */

export type ArraySourceMode = "paste" | "dataset";

export interface ArraySourceValue {
  label: string;
  mode: ArraySourceMode;
  pasteText: string;
  datasetId: string;
  column: string;
  /** "" = no filter, the whole numeric column is the array (resolves to
   * an official server-side dataset-column ref, with real provenance). A
   * non-empty split column client-filters rows to `splitValue` first (no
   * server support for "split one column by another" -- resolves to raw
   * values with a manually-built note instead of engine provenance). */
  splitColumn: string;
  splitValue: string;
}

export function emptyArraySource(label: string): ArraySourceValue {
  return { label, mode: "paste", pasteText: "", datasetId: "", column: "", splitColumn: "", splitValue: "" };
}

/** Pads `groups` up to `min` entries (for multi_group's >=3 floor) without
 * discarding anything the user already typed -- computed at render time,
 * never stored, so switching comparison types and back never loses data. */
export function ensureMinGroups(groups: ArraySourceValue[], min: number): ArraySourceValue[] {
  if (groups.length >= min) return groups;
  const padded = [...groups];
  while (padded.length < min) padded.push(emptyArraySource(`Group ${padded.length + 1}`));
  return padded;
}

export interface ProportionGroupValue {
  label: string;
  successesText: string;
  nText: string;
}

export function emptyProportionGroup(label: string): ProportionGroupValue {
  return { label, successesText: "", nText: "" };
}

export interface ContingencyState {
  rowLabels: string[];
  colLabels: string[];
  /** cells[r][c] as typed text -- parsed to int at submit time. */
  cells: string[][];
}

export function emptyContingency(): ContingencyState {
  return { rowLabels: ["Row 1", "Row 2"], colLabels: ["Col 1", "Col 2"], cells: [["", ""], ["", ""]] };
}

export interface HypothesisFormState {
  questionText: string;
  comparisonType: HypComparisonType;
  declaredDataType: HypDeclaredDataType;
  userShapeConcern: boolean;
  timeOrdered: boolean;
  measurementsPerUnitText: string;
  comparisonsDeclaredText: string;
  testsRunText: string;
  declaredPrimary: boolean;

  groups: ArraySourceValue[]; // two_independent (uses [0],[1]) / multi_group (>=3)
  pairedBefore: ArraySourceValue;
  pairedAfter: ArraySourceValue;
  sample: ArraySourceValue;
  targetText: string; // one_sample_vs_target

  proportionGroups: ProportionGroupValue[]; // 1 (vs target) or 2 (vs each other)
  proportionTargetText: string;

  contingency: ContingencyState;

  reflection: string; // "what does this mean for your project?" -- saved as artifact.notes
}

export function emptyHypothesisFormState(): HypothesisFormState {
  return {
    questionText: "",
    comparisonType: "two_independent",
    declaredDataType: "continuous",
    userShapeConcern: false,
    timeOrdered: false,
    measurementsPerUnitText: "1",
    comparisonsDeclaredText: "1",
    testsRunText: "1",
    declaredPrimary: true,
    groups: [emptyArraySource("Group A"), emptyArraySource("Group B")],
    pairedBefore: emptyArraySource("Before"),
    pairedAfter: emptyArraySource("After"),
    sample: emptyArraySource("Sample"),
    targetText: "",
    proportionGroups: [emptyProportionGroup("Group A")],
    proportionTargetText: "",
    contingency: emptyContingency(),
    reflection: "",
  };
}

/** Reverse-maps a saved artifact's question back onto the form for
 * reopening. Every array always comes back as "paste" text -- the saved
 * question only ever carries resolved values (artifacts/hypothesis.py has
 * no dataset-ref slots), so which dataset/column originally produced them
 * isn't recoverable, and pretending otherwise would be dishonest. */
export function formStateFromQuestion(q: HypothesisQuestion): Partial<HypothesisFormState> {
  const fromValues = (label: string, values: number[] | null | undefined): ArraySourceValue => ({
    ...emptyArraySource(label), pasteText: (values ?? []).join(", "),
  });
  const isProportions = q.comparison_type === "proportions";
  const table = q.contingency_table;

  return {
    questionText: q.question_text,
    comparisonType: q.comparison_type,
    declaredDataType: q.declared_data_type,
    userShapeConcern: q.user_shape_concern,
    timeOrdered: q.time_ordered,
    measurementsPerUnitText: String(q.measurements_per_unit),
    comparisonsDeclaredText: String(q.comparisons_declared),
    testsRunText: String(q.tests_run_including_this_one),
    declaredPrimary: q.declared_primary,
    groups: !isProportions && q.groups.length > 0 ? q.groups.map((g) => fromValues(g.label, g.values)) : [emptyArraySource("Group A"), emptyArraySource("Group B")],
    pairedBefore: fromValues(q.paired_before_label, q.paired_before),
    pairedAfter: fromValues(q.paired_after_label, q.paired_after),
    sample: fromValues(q.sample_label, q.sample),
    targetText: !isProportions && q.target != null ? String(q.target) : "",
    proportionGroups: isProportions && q.groups.length > 0
      ? q.groups.map((g) => ({ label: g.label, successesText: g.successes != null ? String(g.successes) : "", nText: g.n != null ? String(g.n) : "" }))
      : [emptyProportionGroup("Group A")],
    proportionTargetText: isProportions && q.target != null ? String(q.target) : "",
    contingency: table
      ? { rowLabels: q.row_labels ?? table.map((_, i) => `Row ${i + 1}`), colLabels: q.col_labels ?? (table[0] ?? []).map((_, j) => `Col ${j + 1}`), cells: table.map((row) => row.map(String)) }
      : emptyContingency(),
  };
}
