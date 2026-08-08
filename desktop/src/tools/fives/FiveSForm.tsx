import { Button, Field, MissingHint, Panel, TextInput, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { AuditRoundForm } from "./AuditRoundForm";
import { FiveSTrendChart } from "./FiveSTrendChart";
import { FIVE_S_CHECK_LABELS } from "./fiveSChecks";
import { useFiveSForm } from "./useFiveSForm";
import type { ProjectMetadata } from "../../api/types";
import "./FiveSForm.css";

export interface FiveSFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-23 5S Audit (scored): audit rounds with photos, plus the trend line
 * across rounds -- the field's most-digitized lean activity at SMB level. */
export function FiveSForm({ projectId, project, onSaved }: FiveSFormProps) {
  const f = useFiveSForm(projectId, project, onSaved);

  return (
    <Panel title="5S Audit" right={f.version != null && <span data-testid="fives-version-badge">v{f.version} saved</span>}>
      <p>Score each S category 0-5, photograph the physical state, and give the lowest category an action.</p>

      {f.rounds.map((r) => (
        <AuditRoundForm
          key={r.round_id} round={r} onChange={(patch) => f.updateRound(r.round_id, patch)} onRemove={() => f.removeRound(r.round_id)}
          onPhotoSelected={(file) => void f.addPhoto(r.round_id, file)} uploading={f.uploading}
        />
      ))}
      {f.uploadError && <VerdictBanner tone="fail" headline={f.uploadError} />}
      <Button variant="ghost" size="sm" onClick={f.addRound} data-testid="fives-add-round">+ Add audit round</Button>

      <Panel title="Recurrence schedule" subtitle="Or let the trend's own 2+ points make recurrence real">
        <Field label="Cadence note" htmlFor="fives-cadence-note"><TextInput id="fives-cadence-note" data-testid="fives-cadence-note" value={f.cadenceNote} onChange={(e) => f.setCadenceNote(e.target.value)} /></Field>
        <Field label="Next round due" htmlFor="fives-next-due"><TextInput id="fives-next-due" type="date" value={f.nextRoundDue ?? ""} onChange={(e) => f.setNextRoundDue(e.target.value || null)} /></Field>
      </Panel>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <div className="sigma-fives-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="fives-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={f.missing} />}
      </div>

      <FiveSTrendChart trend={f.serverArtifact?.trend ?? null} />

      <PrescoreStrip results={f.prescore} labels={FIVE_S_CHECK_LABELS} />
    </Panel>
  );
}
