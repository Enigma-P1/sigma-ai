/** check_id -> plain-English label for T-35's prescore strip
 * (prescore/gage_rr.py). `grr_design` replaces every other check when the
 * study cannot be computed at all, so the strip is either that one pill or
 * the full set, never a mix. */
export const GAGE_RR_CHECK_LABELS: Record<string, string> = {
  grr_design: "Study design supports the calculation",
  grr_result_matches_readings: "Result matches the stored readings",
  grr_parts: "Part count meets guidance (>= 10)",
  grr_operators: "Operator count meets guidance (>= 3)",
  grr_replicates: "Repeat readings per cell (>= 2)",
  grr_ndc: "Distinct categories (>= 5)",
  grr_verdict: "%GRR verdict",
  grr_interaction: "Operator x part interaction",
  grr_warnings: "What this study could not resolve",
};
