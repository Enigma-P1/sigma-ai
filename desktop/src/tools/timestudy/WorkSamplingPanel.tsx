import { Button, Panel, StatusPill, TextInput, VerdictBanner } from "../../design/components";
import { WORK_SAMPLING_CATEGORIES } from "../../api/types";
import type { Computed, IntervalObservation, WorkSamplingCategory, WorkSamplingSummary } from "../../api/types";

export interface WorkSamplingPanelProps {
  observations: IntervalObservation[];
  onLog: (category: WorkSamplingCategory) => void;
  onUpdateNote: (observationId: string, note: string) => void;
  onRemove: (observationId: string) => void;
  summary: Computed<WorkSamplingSummary> | null | undefined;
}

const CATEGORY_LABELS: Record<WorkSamplingCategory, string> = {
  working: "Working", waiting: "Waiting", moving: "Moving", other: "Other",
};

/** T-09's optional work-sampling mode: tap what's happening right now,
 * and once saved, the engine's own share-per-category renders verbatim
 * (never recomputed client-side, same contract as Pareto's tally). */
export function WorkSamplingPanel({ observations, onLog, onUpdateNote, onRemove, summary }: WorkSamplingPanelProps) {
  return (
    <Panel title="Work sampling (optional)" subtitle="Interval logger: tap what's happening right now" collapsible defaultOpen={false}>
      <div className="sigma-timestudy-sampling__buttons">
        {WORK_SAMPLING_CATEGORIES.map((cat) => (
          <Button key={cat} type="button" variant="secondary" onClick={() => onLog(cat)} data-testid={`timestudy-sampling-log-${cat}`}>
            {CATEGORY_LABELS[cat]}
          </Button>
        ))}
      </div>

      {summary && (
        <div className="sigma-timestudy-sampling__shares" data-testid="timestudy-sampling-summary">
          {summary.value.shares.map((s) => (
            <StatusPill key={s.category} tone="accent" label={`${CATEGORY_LABELS[s.category]}: ${(s.share * 100).toFixed(0)}% (${s.count})`} />
          ))}
        </div>
      )}
      {!summary && observations.length > 0 && <VerdictBanner tone="neutral" headline="Save to get the engine's computed share per category." />}

      {observations.length > 0 && (
        <div className="sigma-timestudy-sampling__log" data-testid="timestudy-sampling-log">
          {observations.map((o) => (
            <div className="sigma-timestudy-sampling__row" key={o.observation_id}>
              <span>{CATEGORY_LABELS[o.category]}</span>
              <span>{o.timestamp}</span>
              <TextInput value={o.note} data-testid={`timestudy-sampling-${o.observation_id}-note`} onChange={(e) => onUpdateNote(o.observation_id, e.target.value)} />
              <button type="button" onClick={() => onRemove(o.observation_id)} aria-label="Remove observation">
                ×
              </button>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
