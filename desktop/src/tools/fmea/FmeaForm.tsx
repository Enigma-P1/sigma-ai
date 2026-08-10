import { Button, MissingHint, Panel, VerdictBanner } from "../../design/components";
import { ReportButton } from "../../app/ReportButton";
import { FmeaWorksheet } from "./FmeaWorksheet";
import { PrescoreStrip } from "../PrescoreStrip";
import { FMEA_CHECK_LABELS } from "./fmeaChecks";
import { RPN_LIMITATION_TEXT, fmeaMissingFields } from "./fmeaLogic";
import { useFmeaForm } from "./useFmeaForm";
import type { ProjectMetadata } from "../../api/types";
import "./FmeaForm.css";

export interface FmeaFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-16 process FMEA: the failure-modes worksheet. Every mutation goes
 * through useFmeaForm; RPN and the severity-first sorted order come from
 * the engine once a version has round-tripped (FmeaWorksheet falls back to
 * an honest client "(draft)" value before that -- CopqForm's serverAmount
 * precedent). The blocking-flags banner renders only what the engine
 * actually returns, never a client-side re-derivation of the safety/
 * regulatory keyword screen. */
export function FmeaForm({ projectId, project, onSaved }: FmeaFormProps) {
  const f = useFmeaForm(projectId, project, onSaved);
  const blockingFlags = f.serverArtifact?.blocking_flags?.value ?? [];

  return (
    <Panel
      title="FMEA (process)"
      right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="fmea-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-16"
            disabled={f.version == null}
            disabledReason="Save the FMEA before downloading its report."
          />
        </span>
      }
    >
      <p>
        One row per specific failure of a specific process step. Rate severity, occurrence, and detection against the
        1-10 anchor scales below -- a rating should match its anchor&rsquo;s wording, not a gut feel.
      </p>

      <div data-testid="fmea-rpn-limitation-banner">
        <VerdictBanner tone="neutral" headline={RPN_LIMITATION_TEXT} />
      </div>

      <div data-testid="fmea-blocking-banner">
        {blockingFlags.length > 0 && (
          <VerdictBanner
            tone="fail"
            headline={`${blockingFlags.length} severity-9/10 row(s) with a safety/regulatory effect and no action`}
            detail={
              <ul>
                {blockingFlags.map((flag) => (
                  <li key={flag.row_id}>{flag.failure_mode} -- {flag.reason}</li>
                ))}
              </ul>
            }
          />
        )}
      </div>

      <FmeaWorksheet
        rows={f.rows} anchors={f.serverArtifact?.anchors} sortedView={f.serverArtifact?.sorted_view?.value ?? null}
        processMapSteps={f.processMapSteps} onChange={f.updateRow} onRemove={f.removeRow}
      />

      <Button variant="ghost" size="sm" type="button" onClick={f.addRow} data-testid="fmea-add-row">
        + Add row
      </Button>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <div className="sigma-fmea-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="fmea-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={fmeaMissingFields(f.rows)} />}
      </div>

      <PrescoreStrip results={f.prescore} labels={FMEA_CHECK_LABELS} />
    </Panel>
  );
}
