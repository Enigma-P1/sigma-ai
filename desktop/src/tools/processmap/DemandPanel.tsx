import { Field, Panel, TextInput, VerdictBanner } from "../../design/components";
import type { BottleneckResult, Computed } from "../../api/types";
import type { DemandValue } from "./processMapLogic";

export interface DemandPanelProps {
  demand: DemandValue;
  onChange: (patch: Partial<DemandValue>) => void;
  bottleneck?: Computed<BottleneckResult> | null;
  saved: boolean;
}

/** The demand block (matrix §5a A-7: available time / demand -- two
 * fields) plus the bottleneck banner, which renders ONLY the engine's own
 * computed verdict -- never a client-side max() over the step times. */
export function DemandPanel({ demand, onChange, bottleneck, saved }: DemandPanelProps) {
  return (
    <Panel title="Demand & bottleneck" subtitle="What pace does this process need to hit?">
      <div className="sigma-processmap-inspector-row">
        <Field label="Available time (minutes)" htmlFor="processmap-demand-time" helper="e.g. an 8-hour shift = 480.">
          <TextInput
            id="processmap-demand-time" type="number" min={0} data-testid="processmap-demand-time"
            value={demand.available_time_minutes ?? ""}
            onChange={(e) => onChange({ available_time_minutes: e.target.value === "" ? null : Number(e.target.value) })}
          />
        </Field>
        <Field label="Demand (units)" htmlFor="processmap-demand-units" helper="How many units/customers need to get through in that time.">
          <TextInput
            id="processmap-demand-units" type="number" min={0} data-testid="processmap-demand-units"
            value={demand.demand_units ?? ""}
            onChange={(e) => onChange({ demand_units: e.target.value === "" ? null : Number(e.target.value) })}
          />
        </Field>
      </div>

      <div data-testid="processmap-bottleneck-banner">
        {bottleneck ? (
          <VerdictBanner
            tone={bottleneck.value.meets_pace ? "pass" : "fail"}
            headline={
              `Bottleneck: ${bottleneck.value.bottleneck_step_name} at ${bottleneck.value.bottleneck_time_minutes} min ` +
              `vs a ${bottleneck.value.pace_minutes_per_unit.toFixed(2)} min/unit pace`
            }
            detail={bottleneck.value.meets_pace ? "This step still fits inside the required pace." : "This step is slower than the pace demand requires -- the constraint to attack first."}
          />
        ) : (
          <VerdictBanner
            tone="neutral"
            headline={saved ? "No bottleneck yet -- enter both demand fields and at least one step time, then save." : "Save to see the engine's bottleneck readout."}
          />
        )}
      </div>
    </Panel>
  );
}
