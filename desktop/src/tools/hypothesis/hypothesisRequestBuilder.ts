import { ensureMinGroups } from "./hypothesisFormState";
import type { ArraySourceValue, HypothesisFormState } from "./hypothesisFormState";
import { parseNumberList, toFloatOrNull, toInt } from "./hypothesisParsing";
import type { HypDatasetColumnRef, HypothesisRequestBody } from "../../api/client";
import type { DatasetDetail, HypGroupInput, HypothesisQuestion } from "../../api/types";

export interface ResolvedArraySource {
  values: number[];
  ref?: HypDatasetColumnRef;
  /** Set only when a split column client-filtered the dataset -- there is
   * no server-side "split one column by another" support, so this slot
   * carries no official DatasetProvenance and this note stands in for it. */
  note?: string;
}

/** Turns one array-source field into either raw values (paste, or a
 * dataset column filtered client-side by a second column's value) or an
 * official dataset-column ref (a whole numeric column, left for the
 * engine to resolve and stamp with real provenance). Filtering here is
 * row selection, not statistics -- no number is computed. */
export async function resolveArraySource(
  source: ArraySourceValue,
  getDatasetDetail: (datasetId: string) => Promise<DatasetDetail>,
  opts: { preferRef?: boolean } = {},
): Promise<ResolvedArraySource> {
  if (source.mode === "paste") return { values: parseNumberList(source.pasteText) };
  if (!source.datasetId || !source.column) return { values: [] };

  const preferRef = opts.preferRef ?? true;
  if (!source.splitColumn && preferRef) return { values: [], ref: { dataset_id: source.datasetId, column: source.column } };

  const detail = await getDatasetDetail(source.datasetId);
  const rows = source.splitColumn ? detail.rows.filter((r) => r[source.splitColumn] === source.splitValue) : detail.rows;
  const values = rows.map((r) => Number(r[source.column])).filter((n) => Number.isFinite(n));
  const filterNote = source.splitColumn ? `, where ${source.splitColumn}=${source.splitValue}` : "";
  return { values, note: `${values.length} row(s) from "${detail.meta.source_filename}", column "${source.column}"${filterNote}` };
}

/** Assembles the full request body from the form's UI state, resolving
 * every array-source slot along the way. Returns the notes for any
 * client-filtered (dataset-split) slots alongside the body, so the caller
 * can display them next to whatever official dataset_provenance the
 * response itself carries for the ref-based slots. */
export async function buildHypothesisRequest(
  state: HypothesisFormState,
  projectId: string,
  getDatasetDetail: (datasetId: string) => Promise<DatasetDetail>,
  opts: { preferRef?: boolean } = {},
): Promise<{ body: HypothesisRequestBody; notes: string[] }> {
  const notes: string[] = [];
  const group_columns: Record<number, HypDatasetColumnRef> = {};
  let paired_before_column: HypDatasetColumnRef | undefined;
  let paired_after_column: HypDatasetColumnRef | undefined;
  let sample_column: HypDatasetColumnRef | undefined;

  const question: HypothesisQuestion = {
    question_text: state.questionText.trim(),
    comparison_type: state.comparisonType,
    declared_data_type: state.declaredDataType,
    groups: [],
    paired_before_label: state.pairedBefore.label.trim() || "before",
    paired_after_label: state.pairedAfter.label.trim() || "after",
    sample_label: state.sample.label.trim() || "sample",
    time_ordered: state.timeOrdered,
    user_shape_concern: state.userShapeConcern,
    measurements_per_unit: toInt(state.measurementsPerUnitText, 1),
    comparisons_declared: toInt(state.comparisonsDeclaredText, 1),
    tests_run_including_this_one: toInt(state.testsRunText, 1),
    declared_primary: state.declaredPrimary,
  };

  if (state.comparisonType === "two_independent" || state.comparisonType === "multi_group") {
    const sources = state.comparisonType === "multi_group" ? ensureMinGroups(state.groups, 3) : state.groups.slice(0, 2);
    const groups: HypGroupInput[] = [];
    for (let i = 0; i < sources.length; i++) {
      const resolved = await resolveArraySource(sources[i], getDatasetDetail, opts);
      groups.push({ label: sources[i].label.trim() || `group ${i + 1}`, values: resolved.values });
      if (resolved.ref) group_columns[i] = resolved.ref;
      if (resolved.note) notes.push(resolved.note);
    }
    question.groups = groups;
  } else if (state.comparisonType === "paired") {
    const before = await resolveArraySource(state.pairedBefore, getDatasetDetail, opts);
    const after = await resolveArraySource(state.pairedAfter, getDatasetDetail, opts);
    question.paired_before = before.values;
    question.paired_after = after.values;
    if (before.ref) paired_before_column = before.ref;
    if (after.ref) paired_after_column = after.ref;
    notes.push(...[before.note, after.note].filter((n): n is string => Boolean(n)));
  } else if (state.comparisonType === "one_sample_vs_target") {
    const resolved = await resolveArraySource(state.sample, getDatasetDetail, opts);
    question.sample = resolved.values;
    question.target = toFloatOrNull(state.targetText);
    if (resolved.ref) sample_column = resolved.ref;
    if (resolved.note) notes.push(resolved.note);
  } else if (state.comparisonType === "proportions") {
    question.groups = state.proportionGroups.map((g) => ({
      label: g.label.trim() || "group", successes: toInt(g.successesText, 0), n: toInt(g.nText, 0),
    }));
    if (state.proportionGroups.length === 1) question.target = toFloatOrNull(state.proportionTargetText);
  } else if (state.comparisonType === "association_categorical") {
    question.contingency_table = state.contingency.cells.map((row) => row.map((c) => toInt(c, 0)));
    question.row_labels = state.contingency.rowLabels;
    question.col_labels = state.contingency.colLabels;
  }
  // relationship_continuous: no data entry -- the selector exits (EXIT-15) before looking at any values.

  const body: HypothesisRequestBody = { question };
  const refsGiven = Object.keys(group_columns).length > 0 || paired_before_column || paired_after_column || sample_column;
  if (refsGiven) {
    body.project_id = projectId;
    if (Object.keys(group_columns).length > 0) body.group_columns = group_columns;
    if (paired_before_column) body.paired_before_column = paired_before_column;
    if (paired_after_column) body.paired_after_column = paired_after_column;
    if (sample_column) body.sample_column = sample_column;
  }
  return { body, notes };
}

/** The save path: HypothesisRunArtifact.question has no dataset-ref slots
 * (the thin artifact stores resolved values only -- artifacts/hypothesis.py),
 * so every array source must resolve to concrete numbers here, never a
 * server-side ref, even for a whole-column pick that /route or /run would
 * otherwise resolve remotely. */
export async function buildResolvedQuestion(
  state: HypothesisFormState,
  getDatasetDetail: (datasetId: string) => Promise<DatasetDetail>,
): Promise<HypothesisQuestion> {
  const { body } = await buildHypothesisRequest(state, "", getDatasetDetail, { preferRef: false });
  return body.question;
}
