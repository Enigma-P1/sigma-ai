/** check_id -> plain-English label for T-18's prescore strip
 * (prescore/solution_matrix.py's 3 checks). */
export const SOLUTION_MATRIX_CHECK_LABELS: Record<string, string> = {
  unlinked_solution_flags: "Every solution links to a cause",
  ranked_list_exists: "The ranked fix list has something in it",
  quadrant_vs_rank_consistency: "Quadrant and ranking match the ratings",
};
