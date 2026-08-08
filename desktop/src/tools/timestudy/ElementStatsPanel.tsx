import { Panel, StatusPill, TextInput, VerdictBanner } from "../../design/components";
import type { ElementStats, TimeStudyCycle } from "../../api/types";

export interface ElementStatsPanelProps {
  stats: ElementStats[];
  cycles: TimeStudyCycle[];
  onEditCycleNote: (cycleNumber: number, note: string) => void;
}

function noteFor(cycles: TimeStudyCycle[], cycleNumber: number): string {
  return cycles.find((c) => c.cycle_number === cycleNumber)?.observer_note ?? "";
}

/** Renders TimeStudyArtifact.element_stats faithfully -- every number here
 * comes from the engine's response, nothing recomputed on screen (same
 * contract as BaselineResultView/MsaResultView). Each outlier badge
 * carries a note affordance bound straight to that cycle's observer_note
 * in CyclesTable -- one field, not a separate free-floating reason. */
export function ElementStatsPanel({ stats, cycles, onEditCycleNote }: ElementStatsPanelProps) {
  return (
    <Panel title="Per-element stats" subtitle="Engine-computed -- mean/median/SD/IQR, never recalculated on screen">
      <div className="sigma-timestudy-stats" data-testid="timestudy-stats-panel">
        {/* Index-based testids (element_stats.value is in the same stable
         * order as the declared elements array) -- element_id is an opaque
         * generated id, unpredictable to anything outside this session. */}
        {stats.map((s, i) => (
          <div className="sigma-timestudy-stats__element" key={s.element_id} data-testid={`timestudy-stats-${i}`}>
            <div className="sigma-timestudy-stats__name">{s.element_name}</div>
            {s.descriptive ? (
              <dl className="sigma-timestudy-stats__dl">
                <div><dt>n</dt><dd data-testid={`timestudy-stats-${i}-n`}>{s.descriptive.n}</dd></div>
                <div><dt>Mean</dt><dd data-testid={`timestudy-stats-${i}-mean`}>{s.descriptive.mean.toFixed(2)}s</dd></div>
                <div><dt>Median</dt><dd>{s.descriptive.median.toFixed(2)}s</dd></div>
                <div><dt>SD</dt><dd>{s.descriptive.sd.toFixed(2)}s</dd></div>
                <div><dt>IQR</dt><dd>{s.descriptive.iqr.toFixed(2)}s (Q1={s.descriptive.q1.toFixed(2)}, Q3={s.descriptive.q3.toFixed(2)})</dd></div>
              </dl>
            ) : (
              <VerdictBanner tone="neutral" headline={`n=${s.n} -- not enough recorded times yet for spread (need >= 2)`} />
            )}
            {s.below_recommended_cycles && <VerdictBanner tone="flag" headline={s.cycle_count_note} />}
            {s.outliers.length > 0 && (
              <div className="sigma-timestudy-stats__outliers">
                {s.outliers.map((o) => (
                  <div className="sigma-timestudy-stats__outlier" key={o.cycle_number} data-testid={`timestudy-outlier-${i}-${o.cycle_number}`}>
                    <StatusPill tone="flag" label={`Outlier: cycle ${o.cycle_number} (${o.seconds.toFixed(1)}s)`} title={o.reason} />
                    <TextInput
                      placeholder="Explain this outlier…" value={noteFor(cycles, o.cycle_number)}
                      data-testid={`timestudy-outlier-${i}-${o.cycle_number}-note`}
                      onChange={(e) => onEditCycleNote(o.cycle_number, e.target.value)}
                    />
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}
