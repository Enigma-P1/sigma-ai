/** check_id -> plain-English label for T-07's prescore strip
 * (prescore/spaghetti.py's 8 checks). */
export const SPAGHETTI_CHECK_LABELS: Record<string, string> = {
  calibration_present: "Floor plan is calibrated",
  calibration_span_plausible: "Calibration line is a trustworthy length",
  route_count_minimum: "At least 1 route traced",
  route_with_three_plus_points: "At least 1 route with a real (3+ point) trace",
  frequencies_present: "Every route has a frequency",
  operator_labels_non_placeholder: "Operator names aren't placeholders",
  observation_window_stated: "Observation window stated (when/duration/shift)",
  metrics_consistency: "Metrics match the data",
};
