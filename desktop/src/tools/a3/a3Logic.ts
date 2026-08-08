import type { A3Artifact, A3Panel, A3PanelKind, ClosureBlock, RealizedBenefits, TollgateAnswer } from "../../api/types";
import { A3_PANEL_ORDER, TOLLGATE_PHASES } from "../../api/types";

let counter = 0;
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function emptyPanels(): A3Panel[] {
  return A3_PANEL_ORDER.map((panel) => ({ panel, seeded_from: null, narrative: "", seeded_at: null }));
}

export function emptyRealizedBenefits(): RealizedBenefits {
  return { copq_rerun_artifact_id: "", window: "", before_amount: 0, after_amount: 0, fix_cost: 0, annualized_projection: null };
}

export function emptyClosure(): ClosureBlock {
  return { objectives_input: null, objectives_verdict: null, lessons: [], open_items: [], fmea_check: null, close_check: null, project_status: "open" };
}

export interface A3State {
  panels: A3Panel[];
  realizedBenefits: RealizedBenefits;
  tollgateAnswers: Record<string, TollgateAnswer[]>;
  closure: ClosureBlock;
}

export function emptyState(): A3State {
  return { panels: emptyPanels(), realizedBenefits: emptyRealizedBenefits(), tollgateAnswers: {}, closure: emptyClosure() };
}

export function stateFromArtifact(a: A3Artifact): A3State {
  const tollgateAnswers: Record<string, TollgateAnswer[]> = {};
  for (const t of a.tollgates) tollgateAnswers[t.phase] = t.answers;
  return { panels: a.panels, realizedBenefits: a.realized_benefits ?? emptyRealizedBenefits(), tollgateAnswers, closure: a.closure };
}

/** A panel is "complete" once it's either seeded or carries its own
 * narrative -- the same rule prescore/a3.py's panels_seeded_or_narrated
 * check uses server-side, mirrored here for the completeness rail. */
export function panelCompleteness(panels: A3Panel[]): Record<A3PanelKind, boolean> {
  const out = {} as Record<A3PanelKind, boolean>;
  for (const p of panels) out[p.panel] = Boolean(p.seeded_from) || p.narrative.trim() !== "";
  return out;
}

export function missingFields(state: A3State): string[] {
  const empty = Object.entries(panelCompleteness(state.panels)).filter(([, ok]) => !ok).map(([k]) => k);
  return empty.length > 0 ? [`narrative or a seed for: ${empty.join(", ")}`] : [];
}

export function canSave(state: A3State): boolean {
  return missingFields(state).length === 0;
}

export function buildA3Body(input: { artifactId: string; schemaVersion: number; state: A3State }): Record<string, unknown> {
  const now = new Date().toISOString();
  const { state } = input;
  const rb = state.realizedBenefits;
  return {
    schema_version: input.schemaVersion, artifact_id: input.artifactId, tool_id: "T-25", created_at: now, updated_at: now,
    panels: state.panels,
    realized_benefits: rb.copq_rerun_artifact_id.trim() || rb.window.trim() ? rb : null,
    tollgates: TOLLGATE_PHASES.map((phase) => ({ phase, questions: [], answers: state.tollgateAnswers[phase] ?? [] })),
    closure: state.closure,
  };
}
