import { useState } from "react";
import { validateArtifact } from "../../api/client";
import { draftNarrativeFor, resolveFmeaCheck } from "./a3Seeding";
import { buildA3Body, type A3State } from "./a3Logic";
import type { A3Artifact, A3PanelKind, ProjectMetadata } from "../../api/types";
import { A3_PANEL_SEED_TOOL_HINT } from "../../api/types";

// This app's fixed single-instance artifact_id per tool (charterLogic.ts /
// fishboneLogic.ts / solutionMatrixLogic.ts / proofState.ts /
// controlPlanLogic.ts's own convention) -- what a panel's default re-seed
// affordance targets.
const DEFAULT_SEED_ARTIFACT_ID: Record<string, string> = {
  "T-03": "charter", "T-15": "fishbone", "T-18": "solution-matrix", "T-20": "proof", "T-22": "control-plan",
};

/** The two "pull fresh data from another artifact" operations, split out
 * of useA3Form.ts (file-size split, not a behavior change): re-seeding a
 * panel's narrative, and loading + previewing the FMEA close-check. */
export function useA3PanelSeeding(
  projectId: string, project: ProjectMetadata, artifactId: string, schemaVersion: number,
  state: A3State, update: (patch: Partial<A3State>) => void, setState: (fn: (prev: A3State) => A3State) => void,
) {
  const [seeding, setSeeding] = useState<A3PanelKind | null>(null);

  async function reseedPanel(panel: A3PanelKind) {
    const toolId = A3_PANEL_SEED_TOOL_HINT[panel];
    const seedArtifactId = DEFAULT_SEED_ARTIFACT_ID[toolId];
    if (!seedArtifactId) return;
    setSeeding(panel);
    try {
      const draft = await draftNarrativeFor(projectId, toolId, seedArtifactId);
      const now = new Date().toISOString();
      update({
        panels: state.panels.map((p) => (p.panel === panel
          ? { ...p, narrative: draft.narrative, seeded_from: { artifact_ref: seedArtifactId, tool_id: toolId, fields: draft.fields }, seeded_at: now }
          : p)),
      });
    } finally {
      setSeeding(null);
    }
  }

  /** Loads the latest FMEA's blocking_flags, then runs a no-save /validate
   * preview (control_chart.py's own "freeze preview needs no new route"
   * pattern) so the close_check banner reflects it immediately -- close_
   * check is server-computed and otherwise only refreshes on a real save. */
  async function loadFmeaForClose() {
    const check = await resolveFmeaCheck(projectId, project);
    const nextClosure = { ...state.closure, fmea_check: check };
    update({ closure: nextClosure });
    try {
      const body = buildA3Body({ artifactId, schemaVersion, state: { ...state, closure: nextClosure } });
      const preview = await validateArtifact("T-25", body);
      const previewClosure = (preview.artifact as A3Artifact).closure;
      setState((prev) => ({ ...prev, closure: { ...prev.closure, close_check: previewClosure.close_check } }));
    } catch {
      /* the close banner just won't refresh until the next real save */
    }
  }

  return { seeding, reseedPanel, loadFmeaForClose };
}
