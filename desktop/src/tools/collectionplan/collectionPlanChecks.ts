/** check_id -> plain-English label for T-11's Collection Plan prescore
 * strip (prescore/data_collection_plan.py has 6 checks, rubric R-MEA-05). */
export const COLLECTION_PLAN_CHECK_LABELS: Record<string, string> = {
  operational_definition_complete: "Operational definition complete",
  two_people_confirmed: "Two-people test confirmed",
  data_type_declared: "Data type declared",
  stratification_or_reason: "Stratification factors (or a stated reason for none)",
  logistics_complete: "Collection logistics complete",
  planned_n_with_rationale: "Planned n stated with rationale",
};
