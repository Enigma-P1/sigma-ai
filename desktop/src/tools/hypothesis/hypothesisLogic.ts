import type { HypComparisonType, HypExitId, HypRouteName, HypRoutingDecision } from "../../api/types";

/** Display-only helpers: number formatting and plain-English labels built
 * from the engine's own categorical fields (route name, comparison type,
 * switch_reason). No statistic is computed here -- every number rendered
 * anywhere in T-17 comes straight from an engine response. */

export function fmt(n: number, digits = 3): string {
  return Number.isFinite(n) ? n.toFixed(digits) : String(n);
}

export function fmtCI(ci: [number, number] | null | undefined, digits = 3): string {
  if (!ci) return "not computed";
  return `[${fmt(ci[0], digits)}, ${fmt(ci[1], digits)}]`;
}

export function fmtPValue(p: number): string {
  return p < 0.0001 ? "< 0.0001" : p.toFixed(4);
}

export const ROUTE_LABELS: Record<HypRouteName, string> = {
  welch_two_sample_t: "Welch's two-sample t-test",
  paired_t: "paired t-test",
  one_sample_t: "one-sample t-test",
  one_way_anova: "one-way ANOVA",
  mann_whitney_u: "Mann-Whitney U test",
  wilcoxon_signed_rank: "Wilcoxon signed-rank test",
  chi_square_independence: "chi-square test of independence",
  two_proportion_z: "two-proportion z-test",
  one_proportion: "one-proportion exact test",
};

const COMPARISON_TYPE_PHRASE: Record<HypComparisonType, string> = {
  two_independent: "comparing two independent groups",
  paired: "comparing before/after pairs on the same units",
  multi_group: "comparing three or more independent groups",
  one_sample_vs_target: "comparing one group against a fixed target",
  proportions: "comparing proportions",
  association_categorical: "checking association between two categorical variables",
  relationship_continuous: "checking a relationship between two continuous variables",
};

export const HYP_EXIT_TITLES: Record<HypExitId, string> = {
  "EXIT-06": "Sample too small for this test",
  "EXIT-07": "Table too sparse for a trustworthy chi-square",
  "EXIT-08": "Repeated measures beyond a paired design",
  "EXIT-09": "Data is autocorrelated (time-dependent)",
  "EXIT-11": "This is rate or defect-count data",
  "EXIT-12": "More than one comparison in play",
  "EXIT-14": "Non-normal data across 3+ groups",
  "EXIT-15": "This is a relationship question, not a comparison",
};

/** One sentence naming why the engine routed where it did, built only from
 * the routing decision's own categorical fields -- the honest counterpart
 * to the printed tree, not a restatement of any computed number. */
export function whyThisTestSentence(routing: HypRoutingDecision): string {
  if (routing.exit || !routing.route) return "";
  const test = ROUTE_LABELS[routing.route];
  const phrase = COMPARISON_TYPE_PHRASE[routing.comparison_type as HypComparisonType] ?? "this comparison";
  const switchNote = routing.switch_reason
    ? ` The rank-based route was used in place of the usual default because ${routing.switch_reason}.`
    : "";
  return `Routed to the ${test} because you're ${phrase}, and the design cleared this route's sample-size floor.${switchNote}`;
}
