import { Field, SelectInput, TextArea, TextInput } from "../../design/components";
import { HYP_COMPARISON_TYPES } from "../../api/types";
import type { HypDeclaredDataType } from "../../api/types";
import type { HypothesisFormState } from "./hypothesisFormState";
import "./HypothesisForm.css";

export interface QuestionIntakeFieldsProps {
  state: HypothesisFormState;
  patch: (p: Partial<HypothesisFormState>) => void;
}

/** R-ANA-04 #1: the question stated first, in plain words -- this is what
 * gets stored as the artifact's stated question, before anything
 * structured. Then the structured intake the selector actually reads. */
export function QuestionIntakeFields({ state, patch }: QuestionIntakeFieldsProps) {
  return (
    <>
      <Field
        label="What are you asking, in your own words?" required htmlFor="hyp-question-text"
        helper='e.g. "Is the afternoon shift slower at handing off orders than the morning shift?" -- not a test name, the real question.'
      >
        <TextArea id="hyp-question-text" data-testid="hyp-question-text" rows={2} value={state.questionText} onChange={(e) => patch({ questionText: e.target.value })} />
      </Field>

      <div className="sigma-hyp-row">
        <Field label="What are you comparing?" htmlFor="hyp-comparison-type">
          <SelectInput
            id="hyp-comparison-type" data-testid="hyp-comparison-type" value={state.comparisonType}
            onChange={(e) => patch({ comparisonType: e.target.value as HypothesisFormState["comparisonType"] })}
          >
            {HYP_COMPARISON_TYPES.map((c) => <option key={c.value} value={c.value}>{c.label}</option>)}
          </SelectInput>
        </Field>
        <Field label="Data type" htmlFor="hyp-data-type" helper="Ordinal = ranked categories (e.g. satisfaction 1-5), not a measured amount.">
          <SelectInput id="hyp-data-type" data-testid="hyp-data-type" value={state.declaredDataType} onChange={(e) => patch({ declaredDataType: e.target.value as HypDeclaredDataType })}>
            <option value="continuous">Continuous (a measured amount)</option>
            <option value="ordinal">Ordinal (ranked categories)</option>
            <option value="nominal_categorical">Nominal categorical (named categories)</option>
            <option value="count_rate">Rate or defect count</option>
          </SelectInput>
        </Field>
      </div>

      <div className="sigma-hyp-row">
        <label className="sigma-hyp-checkbox">
          <input type="checkbox" data-testid="hyp-shape-concern" checked={state.userShapeConcern} onChange={(e) => patch({ userShapeConcern: e.target.checked })} />
          My data looks skewed or has outliers
        </label>
        <label className="sigma-hyp-checkbox">
          <input type="checkbox" data-testid="hyp-time-ordered" checked={state.timeOrdered} onChange={(e) => patch({ timeOrdered: e.target.checked })} />
          This data was collected in time order
        </label>
      </div>

      <details className="sigma-hyp-advanced">
        <summary>Advanced: repeated measures, one pre-declared comparison</summary>
        <div className="sigma-hyp-row">
          <Field label="Measurements per unit" htmlFor="hyp-measurements-per-unit" helper="More than 2 (beyond before/after) is repeated-measures territory (EXIT-08).">
            <TextInput id="hyp-measurements-per-unit" data-testid="hyp-measurements-per-unit" type="number" min={1} value={state.measurementsPerUnitText} onChange={(e) => patch({ measurementsPerUnitText: e.target.value })} />
          </Field>
          <Field label="Comparisons pre-declared" htmlFor="hyp-comparisons-declared" helper="How many primary comparisons you decided on before looking at the data.">
            <TextInput id="hyp-comparisons-declared" data-testid="hyp-comparisons-declared" type="number" min={1} value={state.comparisonsDeclaredText} onChange={(e) => patch({ comparisonsDeclaredText: e.target.value })} />
          </Field>
          <Field label="Tests run so far (incl. this one)" htmlFor="hyp-tests-run" helper="Running more tests than declared is shotgun testing -- the engine refuses (EXIT-12) rather than let you narrate only the significant one.">
            <TextInput id="hyp-tests-run" data-testid="hyp-tests-run" type="number" min={1} value={state.testsRunText} onChange={(e) => patch({ testsRunText: e.target.value })} />
          </Field>
        </div>
        <label className="sigma-hyp-checkbox">
          <input type="checkbox" data-testid="hyp-declared-primary" checked={state.declaredPrimary} onChange={(e) => patch({ declaredPrimary: e.target.checked })} />
          This is my one pre-declared primary comparison for this question
        </label>
      </details>
    </>
  );
}
