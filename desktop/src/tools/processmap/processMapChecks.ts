/** check_id -> plain-English label for T-06's prescore strip
 * (prescore/process_map.py's 9 checks). */
export const PROCESS_MAP_CHECK_LABELS: Record<string, string> = {
  lane_count_minimum: "At least 2 lanes",
  lane_owner_present: "Every lane has an owner",
  step_count_minimum: "At least 3 steps",
  step_type_tag_present: "Every step is VA/NVA/enabling tagged",
  reason_required_for_tagged_steps: "VA/NVA steps have a reason",
  times_present_half: "Times on at least half the steps",
  orphan_steps: "No disconnected steps",
  waste_notes_present: "Checked wastes have a note",
  bottleneck_fields_consistency: "Bottleneck matches the data",
};
