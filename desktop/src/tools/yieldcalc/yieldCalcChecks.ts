/** check_id -> plain-English label for T-10's prescore strip
 * (prescore/yield_calc.py has four checks). */
export const YIELD_CALC_CHECK_LABELS: Record<string, string> = {
  rty_only_claimed_in_series: "RTY only computed when steps are in series",
  rty_matches_recomputed: "RTY matches a fresh recompute",
  dpmo_result_matches_recomputed: "DPMO / sigma level matches a fresh recompute",
  opportunity_inflation_justified: "Opportunities-per-unit inflation is justified (or not inflated)",
};
