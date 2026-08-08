import { Field, Panel, SelectInput, TextArea } from "../../design/components";
import type { ComparisonKind, PilotComparisonDesign, PilotInclusion } from "../../api/types";

export interface ComparisonInclusionSectionProps {
  comparisonDesign: PilotComparisonDesign;
  inclusion: PilotInclusion;
  onComparisonChange: (next: PilotComparisonDesign) => void;
  onInclusionChange: (next: PilotInclusion) => void;
}

const KINDS: { value: ComparisonKind; label: string }[] = [
  { value: "before_period", label: "Before period (compare to a prior window)" },
  { value: "parallel_group", label: "Parallel group (compare to an unchanged group running alongside)" },
];

/** Step 2: the comparison, defined before running (rubric R-IMP-02 #2) --
 * plus who/what is in the pilot and how they were picked, with an explicit
 * honesty-note field for the quiet part about selection. */
export function ComparisonInclusionSection({ comparisonDesign, inclusion, onComparisonChange, onInclusionChange }: ComparisonInclusionSectionProps) {
  return (
    <Panel title="2. Comparison, inclusion, and honesty" subtitle="Defined before you run it -- not chosen after seeing results">
      <Field label="Comparison design" htmlFor="pilot-comparison-kind" required>
        <SelectInput id="pilot-comparison-kind" data-testid="pilot-comparison-kind" value={comparisonDesign.kind} onChange={(e) => onComparisonChange({ ...comparisonDesign, kind: e.target.value as ComparisonKind })}>
          {KINDS.map((k) => <option key={k.value} value={k.value}>{k.label}</option>)}
        </SelectInput>
      </Field>
      <Field label="Describe the period or group" htmlFor="pilot-comparison-description" required helper="The exact window or group, in your own words -- 'prior 4 weeks' or 'Line 3, unchanged, run in parallel.'">
        <TextArea id="pilot-comparison-description" data-testid="pilot-comparison-description" rows={2} value={comparisonDesign.description} onChange={(e) => onComparisonChange({ ...comparisonDesign, description: e.target.value })} />
      </Field>

      <Field label="Who/what is included" htmlFor="pilot-inclusion-who" required>
        <TextArea id="pilot-inclusion-who" data-testid="pilot-inclusion-who" rows={2} value={inclusion.who_or_what} onChange={(e) => onInclusionChange({ ...inclusion, who_or_what: e.target.value })} placeholder="Line 2, all three shifts" />
      </Field>
      <Field label="How was it selected?" htmlFor="pilot-inclusion-how" required>
        <TextArea id="pilot-inclusion-how" data-testid="pilot-inclusion-how" rows={2} value={inclusion.how_selected} onChange={(e) => onInclusionChange({ ...inclusion, how_selected: e.target.value })} placeholder="Only line with the fixture-alignment issue" />
      </Field>
      <Field label="Honesty note" htmlFor="pilot-inclusion-honesty" helper="Say the quiet part: was this convenience, not randomization? Name it here rather than leave it unstated.">
        <TextArea id="pilot-inclusion-honesty" data-testid="pilot-inclusion-honesty" rows={2} value={inclusion.honesty_note} onChange={(e) => onInclusionChange({ ...inclusion, honesty_note: e.target.value })} />
      </Field>
    </Panel>
  );
}
