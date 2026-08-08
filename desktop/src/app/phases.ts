import type { Phase } from "../api/types";

/** Which gate_id(s) (gates.py's GATE_TABLE) must be checked before a phase
 * is considered entered. Mirrored by hand from gates.py -- Define has two
 * gates (one soft, one hard) covering the same Intake->Define transition,
 * and Analyze likewise pairs the soft measure_to_analyze sequence gate
 * with the hard capability-language gate; every other transition has
 * exactly one soft gate. Intake has none: it's the first phase, always
 * open. */
export const PHASE_ENTRY_GATES: Record<Phase, string[]> = {
  Intake: [],
  Define: ["intake_picker_present", "intake_picker_not_exit01"],
  Measure: ["define_to_measure"],
  Analyze: ["measure_to_analyze", "measure_capability_language_requires_msa_pass"],
  Improve: ["analyze_to_improve"],
  Control: ["improve_to_control"],
  Wrap: ["control_to_wrap"],
};

export const PHASE_BLURB: Record<Phase, string> = {
  Intake: "Is this a good first project?",
  Define: "Problem, goal, scope, and who it matters to.",
  Measure: "Baseline the process as it really runs today.",
  Analyze: "Find and verify root causes.",
  Improve: "Pilot fixes for verified causes, one at a time.",
  Control: "Hold the gain and hand it off.",
  Wrap: "Tell the story, close the loop.",
};
