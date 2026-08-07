import { Field, Panel, TextInput } from "../../design/components";
import { DynamicList } from "./DynamicList";
import type { BusinessImpact, TimelineMilestone } from "../../api/types";

export interface TimelineImpactSectionProps {
  timeline: TimelineMilestone[];
  onTimelineChange: (v: TimelineMilestone[]) => void;
  impact: BusinessImpact;
  onImpactChange: (v: BusinessImpact) => void;
}

const emptyMilestone = (): TimelineMilestone => ({ name: "", date: "" });

/** Timeline milestones and the business-impact figure (PLAN §4.1: "dollars
 * or hours, the language leadership hears"). */
export function TimelineImpactSection({ timeline, onTimelineChange, impact, onImpactChange }: TimelineImpactSectionProps) {
  return (
    <Panel title="Timeline and business impact">
      <Field label="Timeline" required helper="At least one milestone.">
        <DynamicList
          items={timeline}
          onChange={onTimelineChange}
          makeEmpty={emptyMilestone}
          minItems={1}
          addLabel="+ Add milestone"
          renderRow={(m, i, update) => (
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
              <TextInput
                data-testid={`charter-timeline-${i}-name`}
                value={m.name}
                onChange={(e) => update({ ...m, name: e.target.value })}
                placeholder="Define complete"
              />
              <TextInput
                type="date"
                data-testid={`charter-timeline-${i}-date`}
                value={m.date}
                onChange={(e) => update({ ...m, date: e.target.value })}
              />
            </div>
          )}
        />
      </Field>

      <Field label="Business impact" required helper="Dollars or hours -- the language leadership hears.">
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 2fr", gap: "var(--space-2)" }}>
          <TextInput
            type="number"
            data-testid="charter-impact-amount"
            value={impact.amount}
            onChange={(e) => onImpactChange({ ...impact, amount: Number(e.target.value) })}
            placeholder="40000"
          />
          <TextInput
            data-testid="charter-impact-unit"
            value={impact.unit}
            onChange={(e) => onImpactChange({ ...impact, unit: e.target.value })}
            placeholder="dollars"
          />
          <TextInput
            data-testid="charter-impact-basis"
            value={impact.basis}
            onChange={(e) => onImpactChange({ ...impact, basis: e.target.value })}
            placeholder="Q2 actuals x 4"
          />
        </div>
      </Field>
    </Panel>
  );
}
