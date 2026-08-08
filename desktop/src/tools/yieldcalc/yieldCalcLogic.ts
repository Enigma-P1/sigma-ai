import type { PrescoreResult, YieldCalcArtifact } from "../../api/types";

export interface YieldStepValue {
  name: string;
  units_in: number;
  first_pass_correct: number;
}

export interface DpmoBlockValue {
  defects: number;
  units: number;
  opportunities_per_unit: number;
  opportunity_justification: string;
  apply_sigma_shift: boolean;
}

export function flagFor(message?: string) {
  return message ? { status: "hard_flag" as const, message } : undefined;
}

export function emptyYieldStep(): YieldStepValue {
  return { name: "", units_in: 0, first_pass_correct: 0 };
}

export function emptyDpmoBlock(): DpmoBlockValue {
  return { defects: 0, units: 0, opportunities_per_unit: 1, opportunity_justification: "", apply_sigma_shift: true };
}

/** Rebuild step-row state from a loaded/saved artifact (CopqForm's
 * copqRowsFromArtifact precedent) -- the raw inputs only;
 * defective_units_at_step/fpy_at_step are read straight off the
 * server-echoed steps (YieldStepFields' serverStep prop), never re-derived
 * here. */
export function yieldStepsFromArtifact(artifact: YieldCalcArtifact): YieldStepValue[] {
  return artifact.steps.map((s) => ({ name: s.name, units_in: s.units_in, first_pass_correct: s.first_pass_correct }));
}

export function dpmoBlockFromArtifact(artifact: YieldCalcArtifact): DpmoBlockValue | null {
  const b = artifact.dpmo_block;
  if (!b) return null;
  return {
    defects: b.defects,
    units: b.units,
    opportunities_per_unit: b.opportunities_per_unit,
    opportunity_justification: b.opportunity_justification,
    apply_sigma_shift: b.apply_sigma_shift,
  };
}

export function yieldStepsToBody(steps: YieldStepValue[]) {
  return steps.map((s) => ({ name: s.name.trim(), units_in: s.units_in, first_pass_correct: s.first_pass_correct }));
}

export function dpmoBlockToBody(block: DpmoBlockValue) {
  return {
    defects: block.defects,
    units: block.units,
    opportunities_per_unit: block.opportunities_per_unit,
    opportunity_justification: block.opportunity_justification.trim(),
    apply_sigma_shift: block.apply_sigma_shift,
  };
}

/** The exact fields the Save button's disabled state depends on, named in
 * plain English -- yieldCalcCanSave below and the rendered "Missing: ..."
 * hint both read from this one list (copqMissingFields' precedent, Jordan
 * usability fix: they can never drift apart). */
export function yieldCalcMissingFields(
  steps: YieldStepValue[],
  stepsInSeries: boolean | null,
  includeDpmo: boolean,
  dpmoBlock: DpmoBlockValue,
): string[] {
  const missing: string[] = [];
  if (steps.length === 0) missing.push("at least one process step");
  steps.forEach((s, i) => {
    const label = `step ${i + 1}`;
    if (!s.name.trim()) missing.push(`${label} name`);
    if (!(s.units_in > 0)) missing.push(`${label} units entering`);
    if (!(s.first_pass_correct >= 0)) missing.push(`${label} first-pass-correct units`);
    if (s.first_pass_correct > s.units_in) missing.push(`${label} first-pass-correct units (cannot exceed units entering)`);
  });
  if (stepsInSeries === null) missing.push("whether the steps are in series");

  if (includeDpmo) {
    if (!(dpmoBlock.defects >= 0)) missing.push("DPMO defects");
    if (!(dpmoBlock.units > 0)) missing.push("DPMO units");
    if (!(dpmoBlock.opportunities_per_unit >= 1)) missing.push("DPMO opportunities per unit (>= 1)");
    if (dpmoBlock.opportunities_per_unit > 1 && !dpmoBlock.opportunity_justification.trim()) {
      missing.push("opportunity justification (required when opportunities per unit > 1)");
    }
  }
  return missing;
}

export function yieldCalcCanSave(
  steps: YieldStepValue[],
  stepsInSeries: boolean | null,
  includeDpmo: boolean,
  dpmoBlock: DpmoBlockValue,
): boolean {
  return yieldCalcMissingFields(steps, stepsInSeries, includeDpmo, dpmoBlock).length === 0;
}

/** Worst-status-first summary of a subset of prescore checks (copqLogic.ts's
 * copqRowsFlag precedent), so the steps table and the DPMO block can each
 * surface only the checks that pertain to them. */
export function sectionFlag(results: PrescoreResult[], checkIds: string[]) {
  const relevant = results.filter((r) => checkIds.includes(r.check_id) && r.status !== "pass");
  if (relevant.length === 0) return undefined;
  const status = relevant.some((r) => r.status === "hard_flag") ? ("hard_flag" as const) : ("flag" as const);
  return { status, message: relevant.map((r) => r.detail).join(" ") };
}

export function fmt(n: number | null | undefined, digits = 3): string {
  if (n == null) return "—";
  return n.toLocaleString(undefined, { maximumFractionDigits: digits });
}

export function percent(n: number | null | undefined, digits = 1): string {
  if (n == null) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}

/** null sigma_level is a genuine wire value (python float `inf` serializes
 * as JSON null) whenever a process is so capable the z-score has nowhere
 * finite to land -- baseline's own sigmaLevelText handles the same case,
 * duplicated here rather than cross-imported (each tool owns its small
 * formatting helpers, this codebase's established convention). */
export function sigmaLevelText(sigmaLevel: number | null, digits = 2): string {
  return sigmaLevel == null ? "not finite at this scale (process is far more capable than these DPMO figures require)" : fmt(sigmaLevel, digits);
}

/** Per-step draft defective-units/FPY before the first save -- an honest
 * client-side preview, never presented as the engine's own number
 * (CopqRowFields' serverAmount precedent: once a save round-trips, the
 * server-echoed defective_units_at_step/fpy_at_step is what actually
 * renders). FPY is the direct observed ratio (first_pass_correct /
 * units_in) -- no modeled estimate, matching the engine's own convention. */
function draftStepIsSane(step: YieldStepValue): boolean {
  return step.units_in > 0 && step.first_pass_correct >= 0 && step.first_pass_correct <= step.units_in;
}

export function draftDefectiveUnits(step: YieldStepValue): number | null {
  return draftStepIsSane(step) ? step.units_in - step.first_pass_correct : null;
}

export function draftFpy(step: YieldStepValue): number | null {
  return draftStepIsSane(step) ? step.first_pass_correct / step.units_in : null;
}
