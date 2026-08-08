/** check_id -> plain-English label for T-19's prescore strip
 * (prescore/pilot_plan.py's 4 checks). */
export const PILOT_PLAN_CHECK_LABELS: Record<string, string> = {
  threshold_before_data_advisory: "Threshold declared before data (advisory)",
  falsification_substance_heuristic: "Falsification line has real teeth",
  checklist_completeness: "Every confounder note is filled in",
  package_declaration_quality: "Declared package reads as a real package",
};

/** A short, real-route picklist for the analysis-plan's "free pick"
 * (stats.hypothesis_common.RouteName mirrored by hand, same idiom
 * fmeaLogic.ts's CLIENT_ANCHORS documents for engine constants). The
 * engine field itself stays a plain string -- this is the desktop's
 * offered choices, not a schema constraint. */
export const ANALYSIS_ROUTE_OPTIONS: { value: string; label: string }[] = [
  { value: "welch_two_sample_t", label: "Welch two-sample t (two independent groups, continuous)" },
  { value: "paired_t", label: "Paired t (same units, before/after)" },
  { value: "one_sample_t", label: "One-sample t (vs. a stated target)" },
  { value: "one_way_anova", label: "One-way ANOVA (3+ groups, continuous)" },
  { value: "one_proportion", label: "One-proportion (vs. a stated target rate)" },
  { value: "two_proportion_z", label: "Two-proportion z (two independent rates)" },
  { value: "chi_square_independence", label: "Chi-square independence (categorical association)" },
  { value: "mann_whitney_u", label: "Mann-Whitney U (nonparametric, two independent groups)" },
  { value: "wilcoxon_signed_rank", label: "Wilcoxon signed-rank (nonparametric, paired)" },
];
