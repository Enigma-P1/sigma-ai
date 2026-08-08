import { Field, TextInput } from "../../design/components";
import type { YieldStep } from "../../api/types";
import { draftDefectiveUnits, draftFpy, flagFor, fmt, percent } from "./yieldCalcLogic";
import type { YieldStepValue } from "./yieldCalcLogic";

export interface YieldStepFieldsProps {
  index: number;
  step: YieldStepValue;
  /** The engine's own computed step (YieldStep.defective_units_at_step/
   * fpy_at_step, artifacts/yield_calc.py) once a save has round-tripped it
   * back -- undefined until then, same "not yet computed" honesty as
   * CopqRowFields' serverAmount. */
  serverStep?: YieldStep;
  onChange: (patch: Partial<YieldStepValue>) => void;
  errors?: Partial<Record<"name" | "units_in" | "first_pass_correct", string>>;
}

/** One process step's fields: name, units entering, first-pass-correct
 * units -- the one input convention this tool uses (defective units and
 * FPY are always engine-derived, read-only here). Rendered inside
 * DynamicList's row wrapper, same split-out-for-length rationale as
 * CopqRowFields. */
export function YieldStepFields({ index, step, serverStep, onChange, errors }: YieldStepFieldsProps) {
  const id = (suffix: string) => `yieldcalc-step-${index}-${suffix}`;
  const defectiveUnits = serverStep?.defective_units_at_step ?? draftDefectiveUnits(step) ?? undefined;
  const fpy = serverStep?.fpy_at_step ?? draftFpy(step) ?? undefined;

  return (
    <>
      <div className="sigma-yieldcalc-step-grid">
        <Field label="Step name" required htmlFor={id("name")} flag={flagFor(errors?.name)}>
          <TextInput id={id("name")} data-testid={id("name")} value={step.name} onChange={(e) => onChange({ name: e.target.value })} placeholder="e.g. Mold part" />
        </Field>
        <Field label="Units entering" required htmlFor={id("units-in")} flag={flagFor(errors?.units_in)}>
          <TextInput id={id("units-in")} type="number" data-testid={id("units-in")} value={step.units_in} onChange={(e) => onChange({ units_in: Number(e.target.value) })} />
        </Field>
        <Field
          label="First-pass-correct units"
          required
          htmlFor={id("fpc")}
          helper="Units that came out right the first time -- no rework, no scrap."
          flag={flagFor(errors?.first_pass_correct)}
        >
          <TextInput id={id("fpc")} type="number" data-testid={id("fpc")} value={step.first_pass_correct} onChange={(e) => onChange({ first_pass_correct: Number(e.target.value) })} />
        </Field>
        <Field label="Defective units" helper="Computed: units entering − first-pass-correct.">
          <TextInput data-testid={id("defective-units")} value={defectiveUnits != null ? fmt(defectiveUnits, 2) : "not yet computed"} disabled />
        </Field>
        <Field label="FPY" helper="First-pass-correct ÷ units entering (direct observed ratio), computed by the engine.">
          <TextInput data-testid={id("fpy")} value={fpy != null ? percent(fpy, 2) : "not yet computed"} disabled />
        </Field>
      </div>
    </>
  );
}
