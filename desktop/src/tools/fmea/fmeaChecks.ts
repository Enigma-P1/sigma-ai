/** check_id -> plain-English label for T-16's prescore strip
 * (prescore/fmea.py's 5 checks). */
export const FMEA_CHECK_LABELS: Record<string, string> = {
  mode_specificity: "Failure modes are specific, not generic",
  ratings_in_range: "Ratings are all 1-10",
  anchors_consulted_confirmed: "Anchor scale confirmed shown per rating",
  high_severity_without_action: "No severity-9/10 row left unaddressed",
  action_owners_present: "Every recorded action has an owner",
};
