import { Field, StatusPill, TextArea } from "../../design/components";
import { signalKey } from "./controlChartLogic";
import type { AckState } from "./controlChartState";
import type { TrackedSignal } from "../../api/types";

export interface SignalListProps {
  signals: TrackedSignal[];
  acknowledgments: Record<string, AckState>;
  onChange: (key: string, patch: Partial<AckState>) => void;
}

/** R-CTL-02's mechanics: every fired signal gets an acknowledge checkbox
 * plus a response-note field, keyed by the engine's own signal identity
 * (rule_id:start_index:end_index:side) so acks survive a fresh signal
 * recompute against the frozen limits (control_chart.py's `signals`
 * validator re-merges by this same key). An empty list is the honest
 * "armed and quiet" state -- rendered by the caller, not here. */
export function SignalList({ signals, acknowledgments, onChange }: SignalListProps) {
  if (signals.length === 0) return null;
  return (
    <div className="sigma-controlchart-signals" data-testid="controlchart-signal-list">
      {signals.map((ts, i) => {
        const key = signalKey(ts.signal.rule_id, ts.signal.start_index, ts.signal.end_index, ts.signal.side);
        const ack = acknowledgments[key] ?? { acknowledged: false, response_note: "" };
        return (
          <div key={key} className="sigma-controlchart-signal-row" data-testid={`controlchart-signal-${i}`}>
            <StatusPill tone={ack.acknowledged ? "pass" : "fail"} label={`${ts.signal.rule_id} — ${ts.signal.side}`} title={ts.signal.description} />
            <p>{ts.signal.description}</p>
            <label>
              <input
                type="checkbox" data-testid={`controlchart-signal-${i}-acknowledge`}
                checked={ack.acknowledged} onChange={(e) => onChange(key, { acknowledged: e.target.checked })}
              />
              {" "}Acknowledged — special cause investigated
            </label>
            <Field label="Response / investigation note" htmlFor={`controlchart-signal-${i}-note`}>
              <TextArea
                id={`controlchart-signal-${i}-note`} data-testid={`controlchart-signal-${i}-response-note`} rows={2}
                value={ack.response_note} onChange={(e) => onChange(key, { response_note: e.target.value })}
              />
            </Field>
          </div>
        );
      })}
    </div>
  );
}
