import { Field, Panel, SelectInput, TextArea, TextInput, VerdictBanner } from "../../design/components";
import { ANALYSIS_ROUTE_OPTIONS } from "./pilotPlanChecks";
import type { PilotDirection } from "../../api/types";

export interface ThresholdAnalysisSectionProps {
  metricRef: string;
  direction: PilotDirection;
  thresholdValue: number;
  expectedRoute: string;
  rationale: string;
  /** The engine-stamped declared_at from the last saved version, if any --
   * never client-guessed (module docstring's honesty framing). */
  declaredAt: string | null;
  onMetricRefChange: (v: string) => void;
  onDirectionChange: (v: PilotDirection) => void;
  onThresholdValueChange: (v: number) => void;
  onExpectedRouteChange: (v: string) => void;
  onRationaleChange: (v: string) => void;
}

/** Step 3: success threshold and analysis plan, declared BEFORE data
 * collection (rubric R-IMP-02 #3). declared_at is stamped by the engine at
 * save time, never typed by the user -- the honest framing is stated
 * plainly rather than implied, per the rubric's own pre-score note. */
export function ThresholdAnalysisSection({
  metricRef, direction, thresholdValue, expectedRoute, rationale, declaredAt,
  onMetricRefChange, onDirectionChange, onThresholdValueChange, onExpectedRouteChange, onRationaleChange,
}: ThresholdAnalysisSectionProps) {
  return (
    <Panel title="3. Success threshold and analysis plan" subtitle="Declared now, checked later -- never moved after seeing results">
      <Field label="Metric" htmlFor="pilot-metric-ref" required>
        <TextInput id="pilot-metric-ref" data-testid="pilot-metric-ref" value={metricRef} onChange={(e) => onMetricRefChange(e.target.value)} placeholder="line-2 scrap rate" />
      </Field>
      <div className="sigma-pilot-threshold-row">
        <Field label="Direction" htmlFor="pilot-direction">
          <SelectInput id="pilot-direction" data-testid="pilot-direction" value={direction} onChange={(e) => onDirectionChange(e.target.value as PilotDirection)}>
            <option value="lower_is_better">Lower is better</option>
            <option value="higher_is_better">Higher is better</option>
          </SelectInput>
        </Field>
        <Field label="Threshold value" htmlFor="pilot-threshold-value" required>
          <TextInput id="pilot-threshold-value" data-testid="pilot-threshold-value" type="number" step="any" value={thresholdValue} onChange={(e) => onThresholdValueChange(Number(e.target.value))} />
        </Field>
      </div>

      <div data-testid="pilot-declared-at-note">
        <VerdictBanner
          tone="neutral"
          headline={declaredAt ? `Declared before data collection: recorded at ${declaredAt}` : "Declared before data collection: stamped the moment you save"}
          detail="The record shows entry order, not observation order -- a spreadsheet could defeat a timestamp, so this is honesty support, not proof."
        />
      </div>

      <Field label="Expected analysis route" htmlFor="pilot-expected-route" required helper="A forecast, not a lock -- T-20 re-runs the real route against the actual data.">
        <SelectInput id="pilot-expected-route" data-testid="pilot-expected-route" value={expectedRoute} onChange={(e) => onExpectedRouteChange(e.target.value)}>
          {ANALYSIS_ROUTE_OPTIONS.map((r) => <option key={r.value} value={r.value}>{r.label}</option>)}
        </SelectInput>
      </Field>
      <Field label="Why this route" htmlFor="pilot-route-rationale" required>
        <TextArea id="pilot-route-rationale" data-testid="pilot-route-rationale" rows={2} value={rationale} onChange={(e) => onRationaleChange(e.target.value)} placeholder="Two independent time windows of continuous scrap-rate data." />
      </Field>
    </Panel>
  );
}
