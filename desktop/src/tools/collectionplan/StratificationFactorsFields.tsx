import { Field, Panel, TextArea, TextInput } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { emptyStratificationFactor, formatValuesExpected, parseValuesExpected } from "./collectionPlanLogic";
import type { StratificationFactor } from "../../api/types";

export interface StratificationFactorsFieldsProps {
  factors: StratificationFactor[];
  onChange: (factors: StratificationFactor[]) => void;
  noReason: string;
  onNoReasonChange: (v: string) => void;
}

/** Rubric R-MEA-05 #3, with the rubric's own escape hatch: >=1 factor, OR
 * an explicit "none apply" reason -- never factors invented just to
 * satisfy a checklist. The reason field only matters once the list is
 * empty, so it only renders then. */
export function StratificationFactorsFields({ factors, onChange, noReason, onNoReasonChange }: StratificationFactorsFieldsProps) {
  return (
    <Panel title="Stratification factors" subtitle="Suspected sources of difference -- shift, machine, operator, day...">
      <Field label="Factors">
        <DynamicList
          items={factors}
          onChange={onChange}
          makeEmpty={emptyStratificationFactor}
          addLabel="+ Add stratification factor"
          renderRow={(factor, i, update) => (
            <>
              <TextInput
                data-testid={`dcp-factor-${i}-name`} value={factor.name}
                onChange={(e) => update({ ...factor, name: e.target.value })}
                placeholder="shift"
              />
              <TextInput
                data-testid={`dcp-factor-${i}-values`} value={formatValuesExpected(factor.values_expected)}
                onChange={(e) => update({ ...factor, values_expected: parseValuesExpected(e.target.value) })}
                placeholder="values expected, comma-separated -- morning, afternoon"
              />
            </>
          )}
        />
      </Field>

      {factors.length === 0 && (
        <Field
          label="No stratification factors apply -- why not?" htmlFor="dcp-no-stratification-reason"
          helper="Only needed while the list above stays empty -- a genuinely uniform single stream can say so."
        >
          <TextArea
            id="dcp-no-stratification-reason" data-testid="dcp-no-stratification-reason" rows={2}
            value={noReason} onChange={(e) => onNoReasonChange(e.target.value)}
          />
        </Field>
      )}
    </Panel>
  );
}
