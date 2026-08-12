import { useState } from "react";
import { downloadPhasePack } from "../api/client";
import { ApiError } from "../api/errors";
import { captureChart } from "../charts/capture";
import type { Capture } from "../charts/capture";
import { safeFilename, saveBlob } from "../api/saveBlob";
import { TOOLS } from "./tools";
import type { Phase } from "../api/types";

/** Which capture key belongs to which tool. Only the diagram and chart
 * screens have one, and only the screen the user is currently standing on
 * is mounted — so a pack collects whatever happens to be live and the
 * engine prints its usual "chart not captured" line for the rest.
 *
 * Deliberately NOT a reason to block the download: a pack whose value is
 * the index and the text should not require touring every screen first. */
const CAPTURE_KEYS: Record<string, string> = {
  "T-06": "T-06-process-map",
  "T-07": "T-07-spaghetti",
  "T-13": "T-13-imr",
  "T-15": "T-15-fishbone",
  "T-21": "T-21-chart",
  "T-35": "T-35-components",
};

export interface PhasePackButtonProps {
  projectId: string;
  projectName: string;
  phase: Phase;
  /** Tool ids with a saved artifact, so the button can say how many
   * reports the pack will actually contain — and disable itself when the
   * answer is none. */
  doneToolIds: ReadonlySet<string>;
}

/** "Download the phase pack" — every report in one phase, with a cover and
 * a verdict index, as one document a manager can print and annotate. */
export function PhasePackButton({ projectId, projectName, phase, doneToolIds }: PhasePackButtonProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Intake folds into the Define pack (pack_pdf.PHASE_FOLD_IN), so the
  // count has to fold too or the button under-reports what it will send.
  const phasesCovered: Phase[] = phase === "Define" ? ["Intake", "Define"] : [phase];
  const inPhase = TOOLS.filter((t) => phasesCovered.includes(t.phase));
  const ready = inPhase.filter((t) => doneToolIds.has(t.id));

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const charts: Record<string, Capture> = {};
      for (const tool of ready) {
        const key = CAPTURE_KEYS[tool.id];
        if (!key) continue;
        const capture = await captureChart(key);
        if (capture) charts[tool.id] = capture;
      }
      const blob = await downloadPhasePack(projectId, phase, charts);
      saveBlob(blob, `${safeFilename(projectName, projectId)}-${phase.toLowerCase()}-pack.pdf`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not build the pack.");
    } finally {
      setBusy(false);
    }
  }

  if (phase === "Intake") return null; // folded into Define

  return (
    <div className="sigma-phase__pack">
      <button
        type="button"
        className="sigma-phase__pack-button"
        disabled={busy || ready.length === 0}
        title={
          ready.length === 0
            ? `No ${phase} tools have been saved yet`
            : `${ready.length} of ${inPhase.length} ${phase} tools, with a cover and a verdict index`
        }
        onClick={() => void run()}
        data-testid={`phase-pack-${phase}`}
      >
        {busy ? "Building…" : `Download the ${phase} pack (${ready.length})`}
      </button>
      {error && (
        <span role="alert" data-testid={`phase-pack-error-${phase}`} className="sigma-phase__pack-error">
          {error}
        </span>
      )}
    </div>
  );
}
