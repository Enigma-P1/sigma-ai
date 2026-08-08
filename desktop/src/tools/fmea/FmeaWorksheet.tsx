import { useState } from "react";
import { Button, SelectInput, TextInput } from "../../design/components";
import type { FmeaAnchors, FmeaRow, ProcessMapStep } from "../../api/types";
import { FMEA_ACTION_STATUSES } from "../../api/types";
import { RatingSelect } from "./RatingSelect";
import { CLIENT_ANCHORS, draftRpn, orderedRows } from "./fmeaLogic";

export interface FmeaWorksheetProps {
  rows: FmeaRow[];
  anchors: FmeaAnchors | null | undefined;
  sortedView: string[] | null;
  processMapSteps: ProcessMapStep[];
  onChange: (rowId: string, patch: Partial<FmeaRow>) => void;
  onRemove: (rowId: string) => void;
}

const ACTION_STATUS_LABELS: Record<FmeaRow["action_status"], string> = { open: "Open", done: "Done", na: "N/A" };

/** The rows table: step link, mode/effect/cause, S/O/D with the anchor
 * text surfaced on focus, the computed RPN column (draft pre-save,
 * engine-authoritative after), and action tracking. Sort toggle default is
 * severity-first (the tool's default view, rubric R-ANA-03 #3) with an
 * RPN-sort option -- neither reorders the underlying `rows` array, only
 * the render order, so save/remove/etc. never depend on the active sort. */
export function FmeaWorksheet({ rows, anchors, sortedView, processMapSteps, onChange, onRemove }: FmeaWorksheetProps) {
  const [sortMode, setSortMode] = useState<"severity" | "rpn">("severity");
  const [activeAnchor, setActiveAnchor] = useState<{ dimension: "severity" | "occurrence" | "detection"; value: number } | null>(null);
  const effectiveAnchors = anchors ?? CLIENT_ANCHORS;
  const visible = orderedRows(rows, sortMode, sortMode === "severity" ? sortedView : null);

  return (
    <div>
      <div className="sigma-fmea-sort-row">
        <span>Sort:</span>
        <Button variant={sortMode === "severity" ? "primary" : "secondary"} size="sm" type="button" onClick={() => setSortMode("severity")} data-testid="fmea-sort-severity">
          Severity first
        </Button>
        <Button variant={sortMode === "rpn" ? "primary" : "secondary"} size="sm" type="button" onClick={() => setSortMode("rpn")} data-testid="fmea-sort-rpn">
          By RPN
        </Button>
      </div>

      <div className="sigma-fmea-anchor-helper" data-testid="fmea-anchor-helper">
        {activeAnchor
          ? `${activeAnchor.dimension[0].toUpperCase()}${activeAnchor.dimension.slice(1)} ${activeAnchor.value}: ${effectiveAnchors[activeAnchor.dimension][String(activeAnchor.value)]}`
          : "Focus a Severity / Occurrence / Detection rating to read its anchor before you pick a number."}
      </div>

      <div className="sigma-fmea-table-scroll">
        <table className="sigma-fmea-table" data-testid="fmea-table">
          <thead>
            <tr>
              <th>Step</th><th>Failure mode</th><th>Effect</th><th>Cause</th>
              <th>S</th><th>O</th><th>D</th><th>RPN</th>
              <th>Action</th><th>Owner</th><th>Due</th><th>Status</th><th />
            </tr>
          </thead>
          <tbody>
            {visible.map((row) => (
              <tr key={row.row_id} data-testid={`fmea-row-${row.row_id}`}>
                <td>
                  {processMapSteps.length > 0 && (
                    <SelectInput
                      data-testid={`fmea-row-${row.row_id}-step-picker`}
                      value={row.process_step_ref ?? ""}
                      onChange={(e) => {
                        const step = processMapSteps.find((s) => s.step_id === e.target.value);
                        onChange(row.row_id, { process_step_ref: step?.step_id ?? null, step_name: step?.name ?? row.step_name });
                      }}
                    >
                      <option value="">-- free text --</option>
                      {processMapSteps.map((s) => (
                        <option key={s.step_id} value={s.step_id}>{s.name}</option>
                      ))}
                    </SelectInput>
                  )}
                  <TextInput data-testid={`fmea-row-${row.row_id}-step-name`} value={row.step_name} onChange={(e) => onChange(row.row_id, { step_name: e.target.value })} placeholder="Step name" />
                </td>
                <td><TextInput data-testid={`fmea-row-${row.row_id}-mode`} value={row.failure_mode} onChange={(e) => onChange(row.row_id, { failure_mode: e.target.value })} placeholder="Specific failure of this step" /></td>
                <td><TextInput data-testid={`fmea-row-${row.row_id}-effect`} value={row.effect} onChange={(e) => onChange(row.row_id, { effect: e.target.value })} /></td>
                <td><TextInput data-testid={`fmea-row-${row.row_id}-cause`} value={row.cause} onChange={(e) => onChange(row.row_id, { cause: e.target.value })} /></td>
                <td>
                  <RatingSelect dimension="severity" value={row.severity} anchors={effectiveAnchors} testId={`fmea-row-${row.row_id}-severity`}
                    onChange={(v) => onChange(row.row_id, { severity: v, anchors_consulted: true })} onFocusAnchor={(d, v) => { setActiveAnchor({ dimension: d, value: v }); onChange(row.row_id, { anchors_consulted: true }); }} />
                </td>
                <td>
                  <RatingSelect dimension="occurrence" value={row.occurrence} anchors={effectiveAnchors} testId={`fmea-row-${row.row_id}-occurrence`}
                    onChange={(v) => onChange(row.row_id, { occurrence: v, anchors_consulted: true })} onFocusAnchor={(d, v) => { setActiveAnchor({ dimension: d, value: v }); onChange(row.row_id, { anchors_consulted: true }); }} />
                </td>
                <td>
                  <RatingSelect dimension="detection" value={row.detection} anchors={effectiveAnchors} testId={`fmea-row-${row.row_id}-detection`}
                    onChange={(v) => onChange(row.row_id, { detection: v, anchors_consulted: true })} onFocusAnchor={(d, v) => { setActiveAnchor({ dimension: d, value: v }); onChange(row.row_id, { anchors_consulted: true }); }} />
                </td>
                <td data-testid={`fmea-row-${row.row_id}-rpn`} className="sigma-fmea-rpn-cell">
                  {row.rpn != null ? row.rpn : `${draftRpn(row)} (draft)`}
                </td>
                <td><TextInput data-testid={`fmea-row-${row.row_id}-action`} value={row.action} onChange={(e) => onChange(row.row_id, { action: e.target.value })} /></td>
                <td><TextInput data-testid={`fmea-row-${row.row_id}-owner`} value={row.action_owner} onChange={(e) => onChange(row.row_id, { action_owner: e.target.value })} /></td>
                <td><input className="sigma-input" type="date" data-testid={`fmea-row-${row.row_id}-due`} value={row.action_due ?? ""} onChange={(e) => onChange(row.row_id, { action_due: e.target.value || null })} /></td>
                <td>
                  <SelectInput data-testid={`fmea-row-${row.row_id}-status`} value={row.action_status} onChange={(e) => onChange(row.row_id, { action_status: e.target.value as FmeaRow["action_status"] })}>
                    {FMEA_ACTION_STATUSES.map((s) => (
                      <option key={s} value={s}>{ACTION_STATUS_LABELS[s]}</option>
                    ))}
                  </SelectInput>
                </td>
                <td>
                  <button type="button" className="sigma-fmea-row-remove" aria-label={`Remove row`} data-testid={`fmea-row-${row.row_id}-remove`} onClick={() => onRemove(row.row_id)}>×</button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
