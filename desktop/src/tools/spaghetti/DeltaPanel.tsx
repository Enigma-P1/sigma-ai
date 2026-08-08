import { Panel, VerdictBanner } from "../../design/components";
import type { DeltaRow, SpaghettiUnit } from "../../api/types";

export interface DeltaPanelProps {
  delta: DeltaRow[] | null;
  unit: SpaghettiUnit | null;
}

function pct(value: number | null): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

function num(value: number | null, suffix: string): string {
  return value == null ? "—" : `${value.toFixed(1)} ${suffix}`;
}

/** Renders the engine's own delta table verbatim (M2 build brief) -- every
 * number here is a `DeltaRow` field computed server-side; this component
 * does no arithmetic of its own, only formatting. */
export function DeltaPanel({ delta, unit }: DeltaPanelProps) {
  if (!delta) {
    return (
      <Panel title="Current vs. proposed">
        <VerdictBanner tone="neutral" headline="No delta yet — trace at least one route in each layout mode to compare." />
      </Panel>
    );
  }
  const overall = delta.find((d) => d.scope === "overall");
  return (
    <Panel title="Current vs. proposed" subtitle="Engine-computed, per operator and overall">
      <div className="sigma-spaghetti-delta-table">
        <div className="sigma-spaghetti-delta-row sigma-spaghetti-delta-row--head">
          <span>Scope</span><span>Current/day</span><span>Proposed/day</span><span>Change</span>
        </div>
        {delta.map((row) => (
          <div
            key={row.scope} className="sigma-spaghetti-delta-row"
            data-testid={row.scope === "overall" ? "spaghetti-delta-overall" : `spaghetti-delta-${row.scope}`}
          >
            <span>{row.scope_label}</span>
            <span>{num(row.current_daily_distance, unit ?? "")}</span>
            <span>{num(row.proposed_daily_distance, unit ?? "")}</span>
            <span data-testid={row.scope === "overall" ? "spaghetti-delta-overall-pct" : `spaghetti-delta-${row.scope}-pct`}>
              {pct(row.distance_delta_pct)}
            </span>
          </div>
        ))}
      </div>
      {overall && (
        <VerdictBanner
          tone={overall.distance_delta_pct != null && overall.distance_delta_pct < 0 ? "pass" : "flag"}
          headline={`Overall daily travel burden: ${num(overall.current_daily_distance, unit ?? "")} → ${num(overall.proposed_daily_distance, unit ?? "")} (${pct(overall.distance_delta_pct)})`}
        />
      )}
    </Panel>
  );
}
