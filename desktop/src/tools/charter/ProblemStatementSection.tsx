import { Field, Panel, TextInput } from "../../design/components";
import type { FieldFlag } from "../../design/components";
import type { ProblemStatement } from "../../api/types";

export interface ProblemStatementSectionProps {
  value: ProblemStatement;
  onChange: (v: ProblemStatement) => void;
  whatFlag?: FieldFlag;
  magnitudeFlag?: FieldFlag;
}

/** Problem statement: what/where/when + magnitude (number, unit, period). */
export function ProblemStatementSection({ value, onChange, whatFlag, magnitudeFlag }: ProblemStatementSectionProps) {
  return (
    <Panel title="Problem statement" subtitle="What's wrong, where, when, and how much -- no causes, no solutions.">
      <Field label="What" required htmlFor="charter-what" flag={whatFlag}>
        <TextInput
          id="charter-what"
          data-testid="charter-problem-what"
          value={value.what}
          onChange={(e) => onChange({ ...value, what: e.target.value })}
          placeholder="Line 2 scrap rate"
        />
      </Field>
      <Field label="Where" required htmlFor="charter-where">
        <TextInput
          id="charter-where"
          data-testid="charter-problem-where"
          value={value.where}
          onChange={(e) => onChange({ ...value, where: e.target.value })}
          placeholder="Line 2, Plant A"
        />
      </Field>
      <Field label="When" required htmlFor="charter-when">
        <TextInput
          id="charter-when"
          data-testid="charter-problem-when"
          value={value.when}
          onChange={(e) => onChange({ ...value, when: e.target.value })}
          placeholder="Q2 2026"
        />
      </Field>
      <Field label="Magnitude" required flag={magnitudeFlag} helper="Number + unit + period, so anyone can tell if it's improving.">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-2)" }}>
          <TextInput
            type="number"
            data-testid="charter-magnitude-number"
            value={value.magnitude.number}
            onChange={(e) => onChange({ ...value, magnitude: { ...value.magnitude, number: Number(e.target.value) } })}
            placeholder="6.2"
          />
          <TextInput
            data-testid="charter-magnitude-unit"
            value={value.magnitude.unit}
            onChange={(e) => onChange({ ...value, magnitude: { ...value.magnitude, unit: e.target.value } })}
            placeholder="%"
          />
          <TextInput
            data-testid="charter-magnitude-period"
            value={value.magnitude.period}
            onChange={(e) => onChange({ ...value, magnitude: { ...value.magnitude, period: e.target.value } })}
            placeholder="Q2 2026"
          />
        </div>
      </Field>
    </Panel>
  );
}
