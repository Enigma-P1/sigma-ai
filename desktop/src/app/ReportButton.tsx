import { useState } from "react";
import { Button } from "../design/components";
import { downloadToolReport } from "../api/client";
import type { ReportRequestBody } from "../api/client";
import { ApiError } from "../api/errors";
import { captureChart } from "../charts/capture";
import { safeFilename, saveBlob } from "../api/saveBlob";

export interface ReportButtonProps {
  projectId: string;
  projectName: string;
  toolId: string;
  /** Which registered chart to attach, if this report has one. Absent, or
   * never mounted, and the report still renders — the engine prints why the
   * picture is missing rather than refusing the document. */
  captureKey?: string;
  /** Inputs the engine needs to recompute the report. Never computed
   * values: everything printed is recalculated server-side. */
  body?: ReportRequestBody;
  disabled?: boolean;
  disabledReason?: string;
  label?: string;
}

/** "Download report" — the button that turns a screen into a deliverable.
 *
 * Shared rather than reimplemented per tool so all 23 behave identically:
 * same capture attempt, same failure text, same filename shape. The first
 * version of the project export grew two copies of the blob-to-disk dance
 * and they immediately started drifting; this is that lesson applied up
 * front. */
export function ReportButton({
  projectId,
  projectName,
  toolId,
  captureKey,
  body,
  disabled,
  disabledReason,
  label = "Download report",
}: ReportButtonProps) {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function run() {
    setBusy(true);
    setError(null);
    try {
      const chart = captureKey ? await captureChart(captureKey) : null;
      const blob = await downloadToolReport(projectId, toolId, { ...(body ?? {}), chart });
      saveBlob(blob, `${safeFilename(projectName, projectId)}-${toolId}-report.pdf`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not build the report.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-2)" }}>
      <Button
        variant="secondary"
        size="sm"
        disabled={disabled || busy}
        title={disabled ? disabledReason : "Download this tool as a one-page PDF"}
        onClick={() => void run()}
        data-testid={`report-button-${toolId}`}
      >
        {busy ? "Building…" : label}
      </Button>
      {error && (
        <span role="alert" data-testid={`report-error-${toolId}`} style={{ fontSize: "var(--text-xs)", color: "var(--color-fail)" }}>
          {error}
        </span>
      )}
    </span>
  );
}
