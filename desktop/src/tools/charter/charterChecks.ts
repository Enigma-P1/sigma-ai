/** check_id -> plain-English label for T-03's prescore strip
 * (prescore/charter.py). */
export const CHARTER_CHECK_LABELS: Record<string, string> = {
  problem_statement_solution_language: "Problem statement avoids solution language",
  goal_solution_language: "Goal avoids solution language",
  magnitude_pattern: "Problem statement has number + unit + period",
  owner_not_placeholder: "Process owner is a real, named person",
  consequential_metric_present: "At least one guardrail metric named",
  risk_block_present: "Key risks & mitigations listed",
};

/** check_id -> the form field path each check should flag (M1 brief:
 * "render field-level flags" fed by validation *and* prescore responses).
 * Kept as a single reviewable table rather than scattered through the
 * section components. */
export const CHARTER_CHECK_FIELD: Record<string, string> = {
  problem_statement_solution_language: "problem_statement.what",
  goal_solution_language: "goal.statement",
  magnitude_pattern: "problem_statement.magnitude",
  owner_not_placeholder: "process_owner.name",
  consequential_metric_present: "goal.consequential_metrics",
  risk_block_present: "risks",
};
