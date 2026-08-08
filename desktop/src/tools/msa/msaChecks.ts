/** check_id -> plain-English label for T-12's prescore strip
 * (prescore/msa.py has up to four checks; repeats_per_item only fires on
 * the continuous path). */
export const MSA_CHECK_LABELS: Record<string, string> = {
  verdict_recorded: "Verdict recorded",
  result_matches_inputs: "Result matches the stored readings",
  repeats_per_item: "Every item has >= 2 valid repeat readings",
  item_count_meets_guidance: "Item count meets sample guidance (>= 10)",
};
