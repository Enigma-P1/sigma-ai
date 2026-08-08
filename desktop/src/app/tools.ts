import type { Phase } from "../api/types";

export const PHASES: Phase[] = ["Intake", "Define", "Measure", "Analyze", "Improve", "Control", "Wrap"];

export interface ToolDef {
  id: string;
  name: string;
  phase: Phase;
  /** Real engine-backed functionality exists for this tool -- either
   * registered in ARTIFACT_REGISTRY (T-01..T-05: validate/save/prescore)
   * or, as of M2, its own bespoke routes (T-11 datasets, T-13 baseline,
   * T-14 stats/charts). Drives the rail's Available-vs-Not-yet-built pill. */
  live: boolean;
  /** Has a dedicated form screen in this app (vs. a generic placeholder).
   * T-01..T-05 (M1) plus T-11/T-13/T-14 (M2). Everything else stays a
   * placeholder until its own milestone. */
  hasForm: boolean;
  /** This tool's fixed saved-artifact id (each *Form.tsx's own private
   * ARTIFACT_ID constant, e.g. useCopqForm.ts's "copq"), mirrored here as
   * the one central place ToolRouter/ToolScreen can read it from without
   * importing 23 separate form modules just for a string (M5 unit 2: "the
   * tool forms know their ARTIFACT_ID constants; thread it through
   * ToolScreen's props the way helperContent already flows"). Undefined
   * for T-13/T-14 (Baseline, Chart Set) -- both are stats-computed views
   * with no ARTIFACT_REGISTRY entry on the engine side (routes/stats.py),
   * so neither ever has a saved artifact_id to review. */
  artifactId?: string;
}

/** The Tier-A tool inventory, mirrored by hand from
 * docs/traceability-matrix.md §1 ("the single authoritative tool count").
 * 25 tools, phases + ids + names verbatim from that table. */
export const TOOLS: ToolDef[] = [
  // Intake
  { id: "T-01", name: "Project Picker (+ PDCA quick path routing)", phase: "Intake", live: true, hasForm: true, artifactId: "picker" },

  // Define
  { id: "T-02", name: "COPQ / Benefit Calculator", phase: "Define", live: true, hasForm: true, artifactId: "copq" },
  { id: "T-03", name: "Project Charter", phase: "Define", live: true, hasForm: true, artifactId: "charter" },
  { id: "T-04", name: "SIPOC", phase: "Define", live: true, hasForm: true, artifactId: "sipoc" },
  { id: "T-05", name: "VoC → CTQ Tree", phase: "Define", live: true, hasForm: true, artifactId: "voc-ctq" },

  // Measure
  { id: "T-06", name: "Process Map (swimlane) + Waste Walk", phase: "Measure", live: true, hasForm: true, artifactId: "process-map" },
  { id: "T-07", name: "Spaghetti Diagram (interactive)", phase: "Measure", live: true, hasForm: true, artifactId: "spaghetti" },
  { id: "T-08", name: "Check Sheet / Tally", phase: "Measure", live: true, hasForm: true, artifactId: "checksheet" },
  { id: "T-09", name: "Guided Time Study / Work Sampling", phase: "Measure", live: true, hasForm: true, artifactId: "timestudy" },
  { id: "T-10", name: "Yield Calculator (FPY/RTY + DPMO)", phase: "Measure", live: true, hasForm: true, artifactId: "yieldcalc" },
  // T-11: dataset-import half (M2) plus the sample-size calculator panel
  // (this unit) -- both live on the same screen.
  { id: "T-11", name: "Data Collection Plan (+ sample-size guidance)", phase: "Measure", live: true, hasForm: true, artifactId: "collection-plan" },
  { id: "T-12", name: "Measurement Check (narrow MSA)", phase: "Measure", live: true, hasForm: true, artifactId: "msa" },
  // T-13/T-14: stats-computed views, no saved artifact -- artifactId
  // deliberately omitted (see ToolDef.artifactId's docstring).
  { id: "T-13", name: "Baseline: Stability then Capability", phase: "Measure", live: true, hasForm: true },
  { id: "T-14", name: "Pareto / Histogram / Run Chart", phase: "Measure", live: true, hasForm: true },

  // Analyze
  { id: "T-15", name: "Fishbone (6M) + 5 Whys", phase: "Analyze", live: true, hasForm: true, artifactId: "fishbone" },
  { id: "T-16", name: "FMEA (process)", phase: "Analyze", live: true, hasForm: true, artifactId: "fmea" },
  { id: "T-17", name: "Hypothesis Testing (guided selector)", phase: "Analyze", live: true, hasForm: true, artifactId: "hypothesis" },

  // Improve
  { id: "T-18", name: "Solution Selection Matrix", phase: "Improve", live: true, hasForm: true, artifactId: "solution-matrix" },
  { id: "T-19", name: "Pilot Plan", phase: "Improve", live: true, hasForm: true, artifactId: "pilot-plan" },
  { id: "T-20", name: "Before/After Proof + Remaining-Gap Check", phase: "Improve", live: true, hasForm: true, artifactId: "proof" },

  // Control
  { id: "T-21", name: "Control Charts (I-MR, p)", phase: "Control", live: true, hasForm: true, artifactId: "control-chart" },
  {
    id: "T-22",
    name: "Control Plan + Response Plan (OCAP) + Scheduled Check-ins",
    phase: "Control",
    live: true,
    hasForm: true,
    artifactId: "control-plan",
  },
  { id: "T-23", name: "5S Audit (scored)", phase: "Control", live: true, hasForm: true, artifactId: "five-s" },
  { id: "T-24", name: "Standard Work / SOP", phase: "Control", live: true, hasForm: true, artifactId: "sop" },

  // Wrap
  { id: "T-25", name: "A3 Final Report + Tollgate Checklists", phase: "Wrap", live: true, hasForm: true, artifactId: "a3" },
];

export function toolsForPhase(phase: Phase): ToolDef[] {
  return TOOLS.filter((t) => t.phase === phase);
}

export function toolById(toolId: string): ToolDef | undefined {
  return TOOLS.find((t) => t.id === toolId);
}

