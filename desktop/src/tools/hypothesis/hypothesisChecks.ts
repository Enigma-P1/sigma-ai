/** check_id -> plain-English label for T-17's prescore strip
 * (prescore/hypothesis.py's five rule-checkable R-ANA-04 lines). */
export const HYP_CHECK_LABELS: Record<string, string> = {
  routing_recorded: "Routing decision recorded",
  route_tamper_check: "Saved route matches the recorded question",
  declared_primary_present: "Declared-primary flag present",
  exit_honored: "No result stored past a raised exit",
  tests_run_vs_declared_primary: "Tests run within the declared count",
};
