import { Field, Panel, TextArea, TextInput } from "../../design/components";
import type { CollectionLogistics } from "../../api/types";

export interface LogisticsFieldsProps {
  value: CollectionLogistics;
  onChange: (v: CollectionLogistics) => void;
  biasNote: string;
  onBiasNoteChange: (v: string) => void;
}

/** Rubric R-MEA-05 #4/#5: who/where/when-how-often, planned n with its
 * rationale (the Sample Size tab's own output, restated here as the
 * plan's committed number), and the bias self-check in the student's own
 * words. */
export function LogisticsFields({ value, onChange, biasNote, onBiasNoteChange }: LogisticsFieldsProps) {
  function set<K extends keyof CollectionLogistics>(key: K, v: CollectionLogistics[K]) {
    onChange({ ...value, [key]: v });
  }

  return (
    <Panel title="Collection logistics" subtitle="Who collects it, where, when/how often, and how much">
      <div className="sigma-dcp-row">
        <Field label="Who collects" htmlFor="dcp-who-collects">
          <TextInput id="dcp-who-collects" data-testid="dcp-who-collects" value={value.who_collects} onChange={(e) => set("who_collects", e.target.value)} />
        </Field>
        <Field label="Where" htmlFor="dcp-where-collected">
          <TextInput id="dcp-where-collected" data-testid="dcp-where-collected" value={value.where_collected} onChange={(e) => set("where_collected", e.target.value)} />
        </Field>
      </div>
      <Field label="When / how often" htmlFor="dcp-when-how-often">
        <TextInput
          id="dcp-when-how-often" data-testid="dcp-when-how-often" value={value.when_how_often}
          onChange={(e) => set("when_how_often", e.target.value)} placeholder="Continuously; exported weekly"
        />
      </Field>
      <div className="sigma-dcp-row">
        <Field label="Planned n" htmlFor="dcp-planned-n" helper="From the Sample Size tab's rule of thumb or calculator.">
          <TextInput
            id="dcp-planned-n" data-testid="dcp-planned-n" type="number" min="1"
            value={value.planned_n ?? ""}
            onChange={(e) => set("planned_n", e.target.value === "" ? null : Number(e.target.value))}
          />
        </Field>
        <Field label="Sample-size rationale" htmlFor="dcp-sample-size-rationale">
          <TextInput
            id="dcp-sample-size-rationale" data-testid="dcp-sample-size-rationale" value={value.sample_size_rationale}
            onChange={(e) => set("sample_size_rationale", e.target.value)}
            placeholder="I-MR baseline rule of thumb: 25-30 points"
          />
        </Field>
      </div>
      <Field label="Bias note" htmlFor="dcp-bias-note" helper="Is this a convenience sample? Say so if it is.">
        <TextArea id="dcp-bias-note" data-testid="dcp-bias-note" rows={2} value={biasNote} onChange={(e) => onBiasNoteChange(e.target.value)} />
      </Field>
    </Panel>
  );
}
