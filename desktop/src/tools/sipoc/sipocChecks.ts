/** check_id -> plain-English label for T-04's prescore strip
 * (prescore/sipoc.py has one check, but it's the three-tier one). */
export const SIPOC_CHECK_LABELS: Record<string, string> = {
  step_count_range: "Process step count is at a workable altitude (4-7)",
};

/** check_id -> the form field path each check should flag, same pattern as
 * charterChecks.ts's CHARTER_CHECK_FIELD -- step_count_range renders both
 * in the PrescoreStrip and right on the process-steps list itself. */
export const SIPOC_CHECK_FIELD: Record<string, string> = {
  step_count_range: "process_steps",
};
