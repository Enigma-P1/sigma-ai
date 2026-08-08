import { Field, TextInput } from "../../design/components";
import type { YieldStep } from "../../api/types";
import { draftDefects, draftDpu, draftFpy, flagFor, fmt, percent } from "./yieldCalcLogic";
import type { YieldStepValue } from "./yieldCalcLogic";

export interface YieldStepFieldsProps {
  index: number;
  step: YieldStepValue;
  /** The engine's own computed step (YieldStep.defects_at_step/dpu_at_step/
   * fpy_at_step, artifacts/yield_calc.py) once a save has round-tripped it
   * back -- undefined until then, same "not yet computed" honesty as
   * CopqRowFields' serverAmount. */
  serverStep?: YieldStep;
  onChange: (patch: Partial<YieldStepValue>) => void;
  errors?: Partial<Record<"name" | "units_in" | "first_pass_correct", string>>;
}

/** One process step's fields: name, units entering, first-pass-correct
 * units -- the one input convention this tool uses (defects, DPU, and FPY
 * are always engine-derived, read-only here). Rendered inside DynamicList's
 * row wrapper, same split-out-for-length rationale as CopqRowFields. */
export function YieldStepFields({ index, step, serverStep, onChange, errors }: YieldStepFieldsProps) {
  const id = (suffix: string) => `yieldcalc-step-${index}-${suffix}`;
  const defects = serverStep?.defects_at_step ?? draftDefects(step) ?? undefined;
  const dpu = serverStep?.dpu_at_step ?? draftDpu(step) ?? undefined;
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
        <Field label="Defects" helper="Computed: units entering − first-pass-correct.">
          <TextInput data-testid={id("defects")} value={defects != null ? fmt(defects, 2) : "not yet computed"} disabled />
        </Field>
        <Field label="DPU" helper="Computed by the engine.">
          <TextInput data-testid={id("dpu")} value={dpu != null ? fmt(dpu, 4) : "not yet computed"} disabled />
        </Field>
        <Field label="FPY" helper="e^-DPU, computed by the engine.">
          <TextInput data-testid={id("fpy")} value={fpy != null ? percent(fpy, 2) : "not yet computed"} disabled />
        </Field>
      </div>
    </>
  );
}
