import { Button, Field, MissingHint, Panel, TextInput, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { CheckInPanel } from "./CheckInPanel";
import { MonitoredItemsTable } from "./MonitoredItemsTable";
import { OcapEditor } from "./OcapEditor";
import { TrainingRowsEditor } from "./TrainingRowsEditor";
import { CONTROL_PLAN_CHECK_LABELS } from "./controlPlanChecks";
import { useControlPlanForm } from "./useControlPlanForm";
import type { ProjectMetadata } from "../../api/types";

export interface ControlPlanFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-22 Control Plan + Response Plan (OCAP) + Scheduled Check-ins: the
 * plan table, the OCAP editor, the training rows, and the check-in panel
 * -- everything the field's most-abandoned phase needs to actually get
 * chased (PLAN §4.1). */
export function ControlPlanForm({ projectId, project, onSaved }: ControlPlanFormProps) {
  const f = useControlPlanForm(projectId, project, onSaved);
  const health = f.serverArtifact?.plan_health?.value ?? null;

  return (
    <Panel title="Control Plan" right={f.version != null && <span data-testid="controlplan-version-badge">v{f.version} saved</span>}>
      <p>What&rsquo;s monitored, how often, and by WHOM -- a control plan with no owner is theater, not control.</p>

      {health && (
        <div data-testid="controlplan-theater-banner">
          {health.is_theater ? (
            <VerdictBanner tone="fail" headline={`${health.ownerless_item_ids.length} monitored item(s) with no owner -- flagged as theater`} detail={health.ownerless_item_ids.join(", ")} />
          ) : (
            <VerdictBanner tone="pass" headline="Every monitored item has a named owner" />
          )}
        </div>
      )}

      <MonitoredItemsTable items={f.state.items} onChange={f.updateItem} onRemove={f.removeItem} onAddOcap={f.addOcap} />
      <Button variant="ghost" size="sm" onClick={f.addItem} data-testid="controlplan-add-item">+ Add monitored item</Button>

      <OcapEditor entries={f.state.ocapEntries} onChange={f.updateOcap} onRemove={f.removeOcap} />
      <TrainingRowsEditor rows={f.state.trainingRows} onAdd={f.addTraining} onChange={f.updateTraining} onRemove={f.removeTraining} />

      <Panel title="As of" subtitle="Reference date for the overdue check-in read">
        <Field label="As of date" htmlFor="controlplan-as-of">
          <TextInput id="controlplan-as-of" data-testid="controlplan-as-of" type="date" value={f.state.asOf} onChange={(e) => f.update({ asOf: e.target.value })} />
        </Field>
      </Panel>

      <CheckInPanel
        frozenLimits={f.frozenLimits} nextDue={f.serverArtifact?.check_in_schedule?.next_due?.value ?? null}
        completed={f.state.completed} onEnter={f.addCheckIn}
      />

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <div className="sigma-controlplan-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="controlplan-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={f.missing} />}
      </div>

      <PrescoreStrip results={f.prescore} labels={CONTROL_PLAN_CHECK_LABELS} />
    </Panel>
  );
}
