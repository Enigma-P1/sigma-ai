import { Field, Panel, TextArea, TextInput } from "../../design/components";
import type { FieldFlag } from "../../design/components";
import { DynamicList } from "./DynamicList";
import type { SmartGoal } from "../../api/types";

export interface GoalSectionProps {
  value: SmartGoal;
  onChange: (v: SmartGoal) => void;
  statementFlag?: FieldFlag;
  consequentialFlag?: FieldFlag;
}

/** SMART goal: statement, metric, baseline/target, date, guardrail metrics. */
export function GoalSection({ value, onChange, statementFlag, consequentialFlag }: GoalSectionProps) {
  return (
    <Panel title="SMART goal" subtitle="Specific, measurable, with a baseline, a target, and a date.">
      <Field label="Goal statement" required htmlFor="charter-goal-statement" flag={statementFlag}>
        <TextArea
          id="charter-goal-statement"
          data-testid="charter-goal-statement"
          value={value.statement}
          onChange={(e) => onChange({ ...value, statement: e.target.value })}
          placeholder="Reduce line-2 scrap from 6.2% to 3% by Nov 30, 2026."
          rows={2}
        />
      </Field>
      <Field label="Metric name" required htmlFor="charter-metric-name">
        <TextInput
          id="charter-metric-name"
          data-testid="charter-goal-metric-name"
          value={value.metric_name}
          onChange={(e) => onChange({ ...value, metric_name: e.target.value })}
          placeholder="line-2 scrap rate"
        />
      </Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-2)" }}>
        <Field label="Baseline" htmlFor="charter-baseline">
          <TextInput
            id="charter-baseline"
            type="number"
            data-testid="charter-goal-baseline"
            value={value.baseline_value ?? ""}
            onChange={(e) => onChange({ ...value, baseline_value: e.target.value === "" ? null : Number(e.target.value) })}
          />
        </Field>
        <Field label="Target" required htmlFor="charter-target">
          <TextInput
            id="charter-target"
            type="number"
            data-testid="charter-goal-target"
            value={value.target_value}
            onChange={(e) => onChange({ ...value, target_value: Number(e.target.value) })}
          />
        </Field>
        <Field label="Unit" required htmlFor="charter-goal-unit">
          <TextInput
            id="charter-goal-unit"
            data-testid="charter-goal-unit"
            value={value.unit}
            onChange={(e) => onChange({ ...value, unit: e.target.value })}
            placeholder="%"
          />
        </Field>
      </div>
      <Field label="Target date" required htmlFor="charter-target-date">
        <TextInput
          id="charter-target-date"
          type="date"
          data-testid="charter-goal-target-date"
          value={value.target_date}
          onChange={(e) => onChange({ ...value, target_date: e.target.value })}
        />
      </Field>
      <Field label="Consequential (guardrail) metrics" flag={consequentialFlag} helper="What else shouldn't get worse while you fix this?">
        <DynamicList
          items={value.consequential_metrics}
          onChange={(items) => onChange({ ...value, consequential_metrics: items })}
          makeEmpty={() => ""}
          addLabel="+ Add guardrail metric"
          renderRow={(item, i, update) => (
            <TextInput
              data-testid={`charter-consequential-metric-${i}`}
              value={item}
              onChange={(e) => update(e.target.value)}
              placeholder="line-2 throughput"
            />
          )}
        />
      </Field>
    </Panel>
  );
}
