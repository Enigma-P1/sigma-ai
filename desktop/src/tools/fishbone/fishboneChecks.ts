/** check_id -> plain-English label for T-15's prescore strip
 * (prescore/fishbone.py's 5 checks). */
export const FISHBONE_CHECK_LABELS: Record<string, string> = {
  branch_coverage_minimum: "At least 4 of the 6 branches explored",
  cause_count_minimum: "At least 6 causes on the board",
  absent_solution_language: "No cause reads as an absent solution",
  verified_causes_have_evidence: "Every verified cause has evidence",
  ruled_out_causes_retained: "Ruled-out causes kept on the board",
};
