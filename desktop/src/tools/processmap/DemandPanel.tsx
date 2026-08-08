import { Field, Panel, TextInput, VerdictBanner } from "../../design/components";
import type { Computed, ConstraintStepResult, LongestStepResult } from "../../api/types";
import type { DemandValue } from "./processMapLogic";

export interface DemandPanelProps {
  demand: DemandValue;
  onChange: (patch: Partial<DemandValue>) => void;
  longestStep?: Computed<LongestStepResult> | null;
  constraintStep?: Computed<ConstraintStepResult> | null;
  saved: boolean;
}

/** The demand block (matrix §5a A-7: available time / demand -- two
 * fields) plus two separately-rendered, engine-only readouts -- never a
 * client-side max() over the step times: `constraintStep` (processing
 * steps only -- this is what meets_pace judges, and the one to attack
 * first) and `longestStep` (any step type, waits included -- may be the
 * same step, or may be a queue sitting downstream of the real constraint;
 * fidelity fix: a pure wait can never be named the constraint). */
export function DemandPanel({ demand, onChange, longestStep, constraintStep, saved }: DemandPanelProps) {
  const waitIsLongerThanConstraint =
    longestStep != null && constraintStep != null && longestStep.value.step_id !== constraintStep.value.step_id;

  return (
    <Panel title="Demand & constraint" subtitle="What pace does this process need to hit?">
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

      <div data-testid="processmap-constraint-banner">
        {constraintStep ? (
          <VerdictBanner
            tone={constraintStep.value.meets_pace ? "pass" : "fail"}
            headline={
              `Constraint: ${constraintStep.value.step_name} at ${constraintStep.value.time_minutes} min ` +
              `vs a ${constraintStep.value.pace_minutes_per_unit.toFixed(2)} min/unit pace`
            }
            detail={
              constraintStep.value.meets_pace
                ? "This step still fits inside the required pace -- the one to attack first if that changes."
                : "This step is slower than the pace demand requires -- the constraint to attack first (processing steps only; a wait can't be the constraint)."
            }
          />
        ) : (
          <VerdictBanner
            tone="neutral"
            headline={saved ? "No constraint yet -- enter both demand fields and give at least one value-add/enabling step a time, then save." : "Save to see the engine's constraint readout."}
          />
        )}
      </div>

      <div data-testid="processmap-longest-step-banner">
        {longestStep && (
          <VerdictBanner
            tone="neutral"
            headline={`Longest step (any type): ${longestStep.value.step_name} at ${longestStep.value.time_minutes} min`}
            detail={
              waitIsLongerThanConstraint
                ? "This is a wait, not a constraint -- it's downstream of the real constraint above, a consequence rather than the cause."
                : constraintStep
                  ? "This is the same step named the constraint above."
                  : "Enter both demand fields to compare this against the constraint readout."
            }
          />
        )}
      </div>
    </Panel>
  );
}
