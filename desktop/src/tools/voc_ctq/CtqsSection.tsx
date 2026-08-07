import { Field, Panel, SelectInput, TextArea, TextInput } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { CTQ_DIRECTIONS } from "../../api/types";
import type { Ctq, CtqDirection, CustomerNeed } from "../../api/types";
import { CTQ_DIRECTION_LABELS } from "./vocCtqLogic";

export interface CtqsSectionProps {
  value: Ctq[];
  onChange: (v: Ctq[]) => void;
  makeEmpty: () => Ctq;
  needs: CustomerNeed[];
}

/** CTQs, each linked to exactly one parent need -- the need -> CTQ edge of
 * the tree -- plus the tool's namesake reflection question (rubric
 * R-DEF-07 Pass #4): is this what the customer critically needs, or what
 * the process finds easy to measure? Answered per CTQ, required. */
export function CtqsSection({ value, onChange, makeEmpty, needs }: CtqsSectionProps) {
  return (
    <Panel title="CTQs" subtitle="Measurable requirements, each traced to one need.">
      <Field label="CTQs" required helper="Each CTQ must resolve to a need above.">
        <DynamicList
          items={value}
          onChange={onChange}
          makeEmpty={makeEmpty}
          minItems={1}
          addLabel="+ Add CTQ"
          renderRow={(ctq, i, update) => (
            <>
              <SelectInput data-testid={`voc-ctq-${i}-need`} value={ctq.need_id} onChange={(e) => update({ ...ctq, need_id: e.target.value })}>
                <option value="">Pick the need this CTQ measures…</option>
                {needs.map((n) => (
                  <option key={n.need_id} value={n.need_id}>
                    {n.need_id}: {n.text.slice(0, 50) || "(empty)"}
                  </option>
                ))}
              </SelectInput>
              <div style={{ display: "grid", gridTemplateColumns: "2fr 1fr 1fr", gap: "var(--space-2)" }}>
                <TextInput data-testid={`voc-ctq-${i}-measure`} value={ctq.measure} onChange={(e) => update({ ...ctq, measure: e.target.value })} placeholder="crack rate at receiving" />
                <SelectInput data-testid={`voc-ctq-${i}-direction`} value={ctq.direction} onChange={(e) => update({ ...ctq, direction: e.target.value as CtqDirection })}>
                  {CTQ_DIRECTIONS.map((d) => (
                    <option key={d} value={d}>
                      {CTQ_DIRECTION_LABELS[d]}
                    </option>
                  ))}
                </SelectInput>
                <TextInput data-testid={`voc-ctq-${i}-target`} value={ctq.target ?? ""} onChange={(e) => update({ ...ctq, target: e.target.value })} placeholder="<1%" />
              </div>
              <Field label="Critical to the customer, or just easy to measure?" required helper="Answer honestly, in your own words -- the tool's namesake check.">
                <TextArea
                  data-testid={`voc-ctq-${i}-critical-check`}
                  value={ctq.critical_vs_easy_check}
                  onChange={(e) => update({ ...ctq, critical_vs_easy_check: e.target.value })}
                  rows={2}
                  placeholder="Customer-critical: cracked parts are returned and re-ordered; not chosen for ease of measurement."
                />
              </Field>
            </>
          )}
        />
      </Field>
    </Panel>
  );
}
