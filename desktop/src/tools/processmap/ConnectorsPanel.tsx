import { useState } from "react";
import { Button, Field, Panel, SelectInput, TextInput } from "../../design/components";
import type { ProcessMapConnector, ProcessMapStep } from "../../api/types";

export interface ConnectorsPanelProps {
  steps: ProcessMapStep[];
  connectors: ProcessMapConnector[];
  onAdd: (fromStep: string, toStep: string, label: string) => void;
  onRemove: (index: number) => void;
}

function stepName(steps: ProcessMapStep[], id: string): string {
  return steps.find((s) => s.step_id === id)?.name ?? id;
}

/** Click-to-connect, implemented as a from/to picker rather than raw
 * canvas pixel-clicking (Konva nodes are canvas-drawn, not DOM nodes, so a
 * form control is the reliable way to drive this deterministically); the
 * resulting connector still renders on the canvas with orthogonal routing
 * (ProcessMapCanvas.connectorPoints). */
export function ConnectorsPanel({ steps, connectors, onAdd, onRemove }: ConnectorsPanelProps) {
  const [fromStep, setFromStep] = useState("");
  const [toStep, setToStep] = useState("");
  const [label, setLabel] = useState("");

  function handleAdd() {
    if (!fromStep || !toStep) return;
    onAdd(fromStep, toStep, label);
    setLabel("");
  }

  return (
    <Panel title="Connectors" subtitle="Connect the flow between steps" collapsible defaultOpen>
      <div className="sigma-processmap-connector-row">
        <Field label="From" htmlFor="processmap-connector-from">
          <SelectInput id="processmap-connector-from" data-testid="processmap-connector-from" value={fromStep} onChange={(e) => setFromStep(e.target.value)}>
            <option value="">Select a step…</option>
            {steps.map((s) => (
              <option key={s.step_id} value={s.step_id}>{s.name}</option>
            ))}
          </SelectInput>
        </Field>
        <Field label="To" htmlFor="processmap-connector-to">
          <SelectInput id="processmap-connector-to" data-testid="processmap-connector-to" value={toStep} onChange={(e) => setToStep(e.target.value)}>
            <option value="">Select a step…</option>
            {steps.map((s) => (
              <option key={s.step_id} value={s.step_id}>{s.name}</option>
            ))}
          </SelectInput>
        </Field>
        <Field label="Label (optional)" htmlFor="processmap-connector-label">
          <TextInput id="processmap-connector-label" data-testid="processmap-connector-label" value={label} onChange={(e) => setLabel(e.target.value)} placeholder="e.g. rework" />
        </Field>
        <Button variant="ghost" size="sm" type="button" onClick={handleAdd} disabled={!fromStep || !toStep} data-testid="processmap-connector-add">
          + Connect
        </Button>
      </div>

      <ul className="sigma-processmap-connector-list">
        {connectors.map((c, i) => (
          <li key={`${c.from_step}-${c.to_step}-${i}`}>
            <span>{stepName(steps, c.from_step)} → {stepName(steps, c.to_step)}{c.label ? ` (${c.label})` : ""}</span>
            <button type="button" aria-label="Remove connector" onClick={() => onRemove(i)}>×</button>
          </li>
        ))}
      </ul>
    </Panel>
  );
}
