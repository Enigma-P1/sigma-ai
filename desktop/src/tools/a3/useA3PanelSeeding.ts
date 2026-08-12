import { useState } from "react";
import { validateArtifact } from "../../api/client";
import { draftNarrativeFor, resolveFmeaCheck, type NarrativeDraft } from "./a3Seeding";
import { buildA3Body, type A3State } from "./a3Logic";
import type { A3Artifact, A3Panel, A3PanelKind, ProjectMetadata } from "../../api/types";
import { A3_PANEL_SEED_TOOL_HINT } from "../../api/types";

// This app's fixed single-instance artifact_id per tool (charterLogic.ts /
// fishboneLogic.ts / solutionMatrixLogic.ts / proofState.ts /
// controlPlanLogic.ts's own convention) -- what a panel's default re-seed
// affordance targets.
const DEFAULT_SEED_ARTIFACT_ID: Record<string, string> = {
  "T-03": "charter", "T-15": "fishbone", "T-18": "solution-matrix", "T-20": "proof", "T-22": "control-plan",
};

/** The three "pull fresh data from another artifact" operations, split out
 * of useA3Form.ts (file-size split, not a behavior change): re-seeding a
 * panel's narrative by hand, auto-seeding every eligible panel on open,
 * and loading + previewing the FMEA close-check. */
export function useA3PanelSeeding(
  projectId: string, project: ProjectMetadata, artifactId: string, schemaVersion: number,
  state: A3State, update: (patch: Partial<A3State> | ((prev: A3State) => Partial<A3State>)) => void,
  setState: (fn: (prev: A3State) => A3State) => void,
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

  /** Fills every panel that is still blank with its default source
   * artifact's draft, once, when the A3 is opened (docs/uat/README.md:
   * "the A3 opens empty even when the work exists" -- Dave saved a
   * dataset, six fishbone causes and several charts, opened T-25, and got
   * eight panels reading "Not seeded yet"; PLAN §2.3). Same two
   * conditions "Re-seed from artifact" already relies on for one panel,
   * just run automatically for all of them: (a) the panel's default
   * source artifact is actually saved in this project, and (b) the panel
   * has no narrative yet. A panel whose source genuinely isn't saved (or,
   * T-13's case, never writes an artifact at all) is left exactly as it
   * was -- still an honest "Not seeded yet", never a placeholder
   * pretending a seed happened.
   *
   * NEVER OVERWRITES A HUMAN'S TEXT, by construction, not by luck: which
   * panels are worth fetching is decided once from the `panels` snapshot
   * the caller hands in, but the write at the bottom re-checks each
   * panel's narrative against the LATEST state at apply time, not that
   * snapshot. If a person starts typing -- or a restored draft lands --
   * in one of these panels while its fetch is still in flight, this sees
   * a non-empty narrative when the result comes back and leaves that
   * panel untouched. seeded_from is written in exactly the shape
   * reseedPanel above writes it, so an auto-seeded panel is
   * indistinguishable from one a person re-seeded by hand -- this is the
   * same action, just triggered by opening the tool instead of a click.
   */
  async function autoSeedOnOpen(panels: A3Panel[]) {
    const now = new Date().toISOString();

    // One fetch per distinct source artifact, not per panel: `background`
    // and `goal` both seed from T-03, `results` and `lessons` both from
    // T-20, and a project with real work behind it -- the exact case this
    // exists for -- is precisely where several panels share a source.
    const bySource = new Map<string, { toolId: string; panels: A3PanelKind[] }>();
    for (const p of panels) {
      if (p.narrative.trim() !== "") continue;
      const toolId = A3_PANEL_SEED_TOOL_HINT[p.panel];
      const seedArtifactId = DEFAULT_SEED_ARTIFACT_ID[toolId];
      if (!seedArtifactId || !project.artifact_index[seedArtifactId]) continue;
      const entry = bySource.get(seedArtifactId) ?? { toolId, panels: [] };
      entry.panels.push(p.panel);
      bySource.set(seedArtifactId, entry);
    }
    if (bySource.size === 0) return;

    const drafts = new Map<A3PanelKind, { seedArtifactId: string; toolId: string; draft: NarrativeDraft }>();
    await Promise.all(
      Array.from(bySource.entries()).map(async ([seedArtifactId, { toolId, panels: kinds }]) => {
        try {
          const draft = await draftNarrativeFor(projectId, toolId, seedArtifactId);
          for (const kind of kinds) drafts.set(kind, { seedArtifactId, toolId, draft });
        } catch {
          /* leave these panels "Not seeded yet" -- an honest state, not a silent error */
        }
      }),
    );
    if (drafts.size === 0) return;

    update((prev) => ({
      panels: prev.panels.map((p) => {
        const found = drafts.get(p.panel);
        if (!found || p.narrative.trim() !== "") return p; // re-checked here against the latest state -- see doc comment above
        return {
          ...p, narrative: found.draft.narrative,
          seeded_from: { artifact_ref: found.seedArtifactId, tool_id: found.toolId, fields: found.draft.fields },
          seeded_at: now,
        };
      }),
    }));
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

  return { seeding, reseedPanel, autoSeedOnOpen, loadFmeaForClose };
}
