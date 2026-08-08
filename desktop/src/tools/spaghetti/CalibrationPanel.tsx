import { useState } from "react";
import { Button, Field, SelectInput, TextInput, VerdictBanner } from "../../design/components";
import type { Calibration, SpaghettiUnit } from "../../api/types";
import type { DraftPoint } from "./spaghettiLogic";

export interface CalibrationPanelProps {
  calibration: Calibration | null;
  draftPoints: DraftPoint[];
  calibrating: boolean;
  onStart: () => void;
  onConfirm: (realLength: number, unit: SpaghettiUnit) => void;
  onCancel: () => void;
}

/** Draw one known-length line, then confirm its real length + unit
 * (rubric R-MEA-03: "the floor plan is calibrated by a drawn known-length
 * line, and that real length is stated"). The badge stays visible once
 * calibration is set (M2 build brief: "a visible calibration badge
 * thereafter"). */
export function CalibrationPanel({ calibration, draftPoints, calibrating, onStart, onConfirm, onCancel }: CalibrationPanelProps) {
  const [realLength, setRealLength] = useState("");
  const [unit, setUnit] = useState<SpaghettiUnit>("meters");
  const readyToConfirm = calibrating && draftPoints.length === 2 && Number(realLength) > 0;

  return (
    <div className="sigma-spaghetti-calibration">
      <div data-testid="spaghetti-calibration-badge">
        {calibration ? (
          <VerdictBanner tone="pass" headline={`Calibrated: line = ${calibration.real_length} ${calibration.unit}`} />
        ) : (
          <VerdictBanner tone="flag" headline="Not calibrated yet — distances and times can't be computed until you draw a known-length line." />
        )}
      </div>

      {calibrating ? (
        <div className="sigma-spaghetti-calibration-controls">
          <p>
            {draftPoints.length < 2
              ? `Click two points on the floor plan marking a known length (${draftPoints.length}/2 placed).`
              : "Enter the real length that line represents, then confirm."}
          </p>
          <div className="sigma-spaghetti-inspector-row">
            <Field label="Real length" htmlFor="spaghetti-calibration-length">
              <TextInput
                id="spaghetti-calibration-length" type="number" min={0} data-testid="spaghetti-calibration-length"
                value={realLength} onChange={(e) => setRealLength(e.target.value)}
              />
            </Field>
            <Field label="Unit" htmlFor="spaghetti-calibration-unit">
              <SelectInput
                id="spaghetti-calibration-unit" data-testid="spaghetti-calibration-unit" value={unit}
                onChange={(e) => setUnit(e.target.value as SpaghettiUnit)}
              >
                <option value="meters">Meters</option>
                <option value="feet">Feet</option>
              </SelectInput>
            </Field>
            <Button variant="primary" disabled={!readyToConfirm} onClick={() => onConfirm(Number(realLength), unit)} data-testid="spaghetti-calibration-confirm">
              Confirm calibration
            </Button>
            <Button variant="ghost" onClick={onCancel} data-testid="spaghetti-calibration-cancel">Cancel</Button>
          </div>
        </div>
      ) : (
        <Button variant="secondary" onClick={onStart} data-testid="spaghetti-mode-calibrate">
          {calibration ? "Re-calibrate" : "Start calibration"}
        </Button>
      )}
    </div>
  );
}
