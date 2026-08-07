import type { Phase } from "../api/types";

export const PHASES: Phase[] = ["Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap"];

export interface ToolDef {
  id: string;
  name: string;
  phase: Phase;
  /** Registered in the engine's ARTIFACT_REGISTRY (registry.py) -- can be
   * validated, saved, and pre-scored. T-01..T-05 only, this milestone. */
  live: boolean;
  /** Has a dedicated form screen in this app (vs. a generic placeholder).
   * T-01..T-05 only -- the whole Intake+Define tool set this milestone
   * completes. T-06 and later stay placeholders (the engine doesn't
   * register them yet either -- see `live`). */
  hasForm: boolean;
}

/** The Tier-A tool inventory, mirrored by hand from
 * docs/traceability-matrix.md §1 ("the single authoritative tool count").
 * 25 tools, phases + ids + names verbatim from that table. */
export const TOOLS: ToolDef[] = [
  // Intake
  { id: "T-01", name: "Project Picker (+ PDCA quick path routing)", phase: "Intake", live: true, hasForm: true },

  // Define
  { id: "T-02", name: "COPQ / Benefit Calculator", phase: "Define", live: true, hasForm: true },
  { id: "T-03", name: "Project Charter", phase: "Define", live: true, hasForm: true },
  { id: "T-04", name: "SIPOC", phase: "Define", live: true, hasForm: true },
  { id: "T-05", name: "VoC → CTQ Tree", phase: "Define", live: true, hasForm: true },

  // Measure
  { id: "T-06", name: "Process Map (swimlane) + Waste Walk", phase: "Measure", live: false, hasForm: false },
  { id: "T-07", name: "Spaghetti Diagram (interactive)", phase: "Measure", live: false, hasForm: false },
  { id: "T-08", name: "Check Sheet / Tally", phase: "Measure", live: false, hasForm: false },
  { id: "T-09", name: "Guided Time Study / Work Sampling", phase: "Measure", live: false, hasForm: false },
  { id: "T-10", name: "Yield Calculator (FPY/RTY + DPMO)", phase: "Measure", live: false, hasForm: false },
  { id: "T-11", name: "Data Collection Plan (+ sample-size guidance)", phase: "Measure", live: false, hasForm: false },
  { id: "T-12", name: "Measurement Check (narrow MSA)", phase: "Measure", live: false, hasForm: false },
  { id: "T-13", name: "Baseline: Stability then Capability", phase: "Measure", live: false, hasForm: false },
  { id: "T-14", name: "Pareto / Histogram / Run Chart", phase: "Measure", live: false, hasForm: false },

  // Analyze
  { id: "T-15", name: "Fishbone (6M) + 5 Whys", phase: "Analyze", live: false, hasForm: false },
  { id: "T-16", name: "FMEA (process)", phase: "Analyze", live: false, hasForm: false },
  { id: "T-17", name: "Hypothesis Testing (guided selector)", phase: "Analyze", live: false, hasForm: false },

  // Improve
  { id: "T-18", name: "Solution Selection Matrix", phase: "Improve", live: false, hasForm: false },
  { id: "T-19", name: "Pilot Plan", phase: "Improve", live: false, hasForm: false },
  { id: "T-20", name: "Before/After Proof + Remaining-Gap Check", phase: "Improve", live: false, hasForm: false },

  // Control
  { id: "T-21", name: "Control Charts (I-MR, p)", phase: "Control", live: false, hasForm: false },
  {
    id: "T-22",
    name: "Control Plan + Response Plan (OCAP) + Scheduled Check-ins",
    phase: "Control",
    live: false,
    hasForm: false,
  },
  { id: "T-23", name: "5S Audit (scored)", phase: "Control", live: false, hasForm: false },
  { id: "T-24", name: "Standard Work / SOP", phase: "Control", live: false, hasForm: false },

  // Wrap
  { id: "T-25", name: "A3 Final Report + Tollgate Checklists", phase: "Wrap", live: false, hasForm: false },
];

export function toolsForPhase(phase: Phase): ToolDef[] {
  return TOOLS.filter((t) => t.phase === phase);
}

export function toolById(toolId: string): ToolDef | undefined {
  return TOOLS.find((t) => t.id === toolId);
}

