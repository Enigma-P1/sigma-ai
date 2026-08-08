/** check_id -> plain-English label for T-09's prescore strip
 * (prescore/time_study.py has 5 checks). */
export const TIME_STUDY_CHECK_LABELS: Record<string, string> = {
  elements_defined_before_timing: "Elements defined before timing",
  cycle_count_floor: "Cycle count meets guidance",
  spread_present: "Spread reported once n >= 2",
  outliers_have_notes: "Flagged outliers explained",
  stats_match_recomputation: "Stats match a fresh recomputation",
};
