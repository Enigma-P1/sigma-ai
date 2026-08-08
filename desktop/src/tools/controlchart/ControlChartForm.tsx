import { Button, Field, MissingHint, Panel, SelectInput, TextArea, TextInput, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { ArraySourceInput } from "../hypothesis/ArraySourceInput";
import { ImrChart } from "../baseline/ImrChart";
import { PChart } from "./PChart";
import { SignalList } from "./SignalList";
import { useControlChartForm } from "./useControlChartForm";
import { useState } from "react";
import type { ProjectMetadata } from "../../api/types";

export interface ControlChartFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

const CHECK_LABELS: Record<string, string> = {
  family_matches_data: "Chart family matches data type",
  frozen_limits_present_before_signals: "Frozen limits before signals",
  never_armed: "Monitoring armed",
  signal_acknowledgment_completeness: "Every signal acknowledged",
  recalculation_log_has_reasons: "Recalculation log has reasons",
};

/** T-21 Control Charts: the printed selector (data shape, then --
 * attribute only -- defectives-or-defects, EXIT-11 on "defects"), the
 * chart itself (I-MR reused verbatim, a new PChart for the attribute
 * half), the freeze banner + recalculate affordance, armed-state
 * control, and the signal list with acknowledge + response-note. */
export function ControlChartForm({ projectId, project, onSaved }: ControlChartFormProps) {
  const f = useControlChartForm(projectId, project, onSaved);
  const [recalcReasonDraft, setRecalcReasonDraft] = useState("");
  const frozen = f.serverArtifact?.imr_baseline ?? f.serverArtifact?.p_baseline ?? null;
  const chartType = f.state.dataShape === "continuous" ? "imr" : "p";

  return (
    <Panel title="Control Chart" right={f.version != null && <span data-testid="controlchart-version-badge">v{f.version} saved</span>}>
      <p>Pick the chart family by data type, freeze limits from a stable window, arm monitoring, and respond to signals.</p>

      <div className="sigma-controlchart-selector">
        <Field label="Data shape" htmlFor="controlchart-data-shape">
          <SelectInput
            id="controlchart-data-shape" data-testid="controlchart-data-shape" value={f.state.dataShape}
            onChange={(e) => f.update({ dataShape: e.target.value as "continuous" | "attribute" })}
          >
            <option value="continuous">Continuous (a measured value per unit)</option>
            <option value="attribute">Attribute (pass/fail units, or counts)</option>
          </SelectInput>
        </Field>
        {f.state.dataShape === "attribute" && (
          <Field label="Defectives or defects?" htmlFor="controlchart-defectives-or-defects" helper="Defectives: whole units pass/fail. Defects: counts per unit/area (refused by name -- EXIT-11).">
            <SelectInput
              id="controlchart-defectives-or-defects" data-testid="controlchart-defectives-or-defects" value={f.state.defectivesOrDefects}
              onChange={(e) => f.update({ defectivesOrDefects: e.target.value as "defectives" | "defects" | "" })}
            >
              <option value="">Select…</option>
              <option value="defectives">Defectives — pass/fail units</option>
              <option value="defects">Defects — counts per unit/area</option>
            </SelectInput>
          </Field>
        )}
        <Field label="Metric monitored" htmlFor="controlchart-metric-ref">
          <TextInput id="controlchart-metric-ref" data-testid="controlchart-metric-ref" value={f.state.metricRef} onChange={(e) => f.update({ metricRef: e.target.value })} />
        </Field>
      </div>

      {chartType === "imr" ? (
        <ArraySourceInput
          value={f.state.imrSource} onChange={(v) => f.update({ imrSource: v })}
          datasets={f.datasets} datasetDetails={f.datasetDetails} onNeedDatasetDetail={f.loadDatasetDetail}
          testId="controlchart-imr-source" labelText="Control chart data"
        />
      ) : (
        <Field label="Subgroups (one per line: label,n,defective_count)" htmlFor="controlchart-p-subgroups-paste">
          <TextArea
            id="controlchart-p-subgroups-paste" data-testid="controlchart-p-subgroups-paste" rows={5}
            placeholder="day-1,50,12&#10;day-2,50,9"
            value={f.state.pSubgroupsPasteText} onChange={(e) => f.update({ pSubgroupsPasteText: e.target.value })}
          />
        </Field>
      )}

      {f.exitError && (
        <div data-testid="controlchart-exit11-banner">
          <VerdictBanner tone="exit" headline={f.exitError} />
        </div>
      )}

      <div className="sigma-controlchart-actions">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleFreeze()} data-testid="controlchart-freeze">
          {f.saving ? "Working…" : frozen ? "Re-verify data" : "Freeze limits"}
        </Button>
        {!f.saving && <MissingHint fields={f.missing} />}
      </div>

      {frozen && (
        <div data-testid="controlchart-freeze-banner">
          <VerdictBanner
            tone="pass" headline={`Limits frozen ${f.serverArtifact?.frozen_at}`}
            detail={`Source hash ${f.serverArtifact?.source_dataset_hash?.slice(0, 16)}… — recalculated only on a deliberate, logged decision.`}
          />
          <div className="sigma-controlchart-recalculate">
            <Field label="Reason for recalculating (required)" htmlFor="controlchart-recalculate-reason">
              <TextInput id="controlchart-recalculate-reason" data-testid="controlchart-recalculate-reason" value={recalcReasonDraft} onChange={(e) => setRecalcReasonDraft(e.target.value)} />
            </Field>
            <Button disabled={!recalcReasonDraft.trim() || f.saving} onClick={() => void f.handleRecalculate(recalcReasonDraft)} data-testid="controlchart-recalculate">
              Recalculate limits
            </Button>
          </div>
        </div>
      )}

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      {f.serverArtifact?.imr_baseline && f.serverArtifact.imr_values && (
        <ImrChart
          values={f.serverArtifact.imr_values} stability={f.serverArtifact.imr_baseline}
          stable={!f.serverArtifact.imr_baseline.value.signals.some((s) => s.rule_id === "rule1" || s.rule_id === "rule4")}
          stabilityNote="Frozen baseline — limits do not move as new points arrive."
          testId="controlchart-imr-chart"
        />
      )}
      {f.serverArtifact?.p_baseline && (
        <PChart
          points={f.serverArtifact.p_baseline.value.points} pBar={f.serverArtifact.p_baseline.value.p_bar}
          signals={f.serverArtifact.signals?.value.map((ts) => ts.signal) ?? []} meetsFreezeFloor={f.serverArtifact.p_baseline.value.meets_freeze_floor}
          testId="controlchart-p-chart"
        />
      )}

      <Panel title="Monitoring">
        <label>
          <input type="checkbox" data-testid="controlchart-armed-toggle" checked={f.state.monitoringStarted} onChange={(e) => f.update({ monitoringStarted: e.target.checked })} />
          {" "}Start monitoring
        </label>
        <Field label="Cadence" htmlFor="controlchart-cadence-note">
          <TextInput id="controlchart-cadence-note" data-testid="controlchart-cadence-note" value={f.state.cadenceNote} onChange={(e) => f.update({ cadenceNote: e.target.value })} />
        </Field>
        <Button onClick={() => void f.handleSaveMeta()} disabled={f.saving} data-testid="controlchart-save-meta">Save monitoring state</Button>
      </Panel>

      {f.serverArtifact?.signals && (
        <SignalList signals={f.serverArtifact.signals.value} acknowledgments={f.state.acknowledgments} onChange={f.updateAcknowledgment} />
      )}
      {f.serverArtifact?.armed.monitoring_started && f.serverArtifact.signals?.value.length === 0 && (
        <div data-testid="controlchart-armed-quiet-banner">
          <VerdictBanner tone="pass" headline="Armed and quiet — no signals yet" detail="A thin pass: the chart is running, nothing has fired." />
        </div>
      )}

      <PrescoreStrip results={f.prescore} labels={CHECK_LABELS} />
    </Panel>
  );
}
