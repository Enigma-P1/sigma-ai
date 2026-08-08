import { Field, TextArea, TextInput, YesNoToggle } from "../../design/components";
import { flagFor } from "./yieldCalcLogic";
import type { DpmoBlockValue } from "./yieldCalcLogic";

export interface DpmoBlockFieldsProps {
  block: DpmoBlockValue;
  onChange: (patch: Partial<DpmoBlockValue>) => void;
  errors?: Partial<Record<"defects" | "units" | "opportunities_per_unit" | "opportunity_justification", string>>;
}

/** The DPMO block's fields: defects, units, opportunities per unit, and --
 * only once opportunities_per_unit > 1 -- the required justification field
 * naming what the extra opportunities are (the opportunity-inflation
 * honesty guard, rubric R-MEA-09; engine-enforced in artifacts/
 * yield_calc.py, this is the client-side mirror of that same rule).
 * Conditional-field pattern copied from CopqRowFields' custom-category
 * label field. */
export function DpmoBlockFields({ block, onChange, errors }: DpmoBlockFieldsProps) {
  const id = (suffix: string) => `yieldcalc-dpmo-${suffix}`;
  const inflated = block.opportunities_per_unit > 1;

  return (
    <>
      <div className="sigma-yieldcalc-dpmo-grid">
        <Field label="Defects" required htmlFor={id("defects")} flag={flagFor(errors?.defects)}>
          <TextInput id={id("defects")} type="number" data-testid={id("defects")} value={block.defects} onChange={(e) => onChange({ defects: Number(e.target.value) })} />
        </Field>
        <Field label="Units" required htmlFor={id("units")} flag={flagFor(errors?.units)}>
          <TextInput id={id("units")} type="number" data-testid={id("units")} value={block.units} onChange={(e) => onChange({ units: Number(e.target.value) })} />
        </Field>
        <Field
          label="Opportunities per unit"
          required
          htmlFor={id("opportunities")}
          helper="Default 1: one opportunity, the unit itself."
          flag={flagFor(errors?.opportunities_per_unit)}
        >
          <TextInput
            id={id("opportunities")}
            type="number"
            min={1}
            data-testid={id("opportunities")}
            value={block.opportunities_per_unit}
            onChange={(e) => onChange({ opportunities_per_unit: Number(e.target.value) })}
          />
        </Field>
      </div>

      {inflated && (
        <Field
          label="What are the extra opportunities?"
          required
          htmlFor={id("justification")}
          helper="Name them specifically. The classic DPMO game is inflating this count to flatter sigma -- a vague word here ('several', 'various') is treated the same as leaving it blank."
          flag={flagFor(errors?.opportunity_justification)}
        >
          <TextArea
            id={id("justification")}
            data-testid={id("justification")}
            value={block.opportunity_justification}
            onChange={(e) => onChange({ opportunity_justification: e.target.value })}
            placeholder="e.g. Three inspected weld points per bracket, per the weld QC spec."
            rows={2}
          />
        </Field>
      )}

      <Field label="Apply the 1.5σ shift convention?" helper="Reporting convention, not physics -- the frozen default is Yes, and the result always names which convention produced it.">
        <YesNoToggle name={id("shift")} value={block.apply_sigma_shift} onChange={(v) => onChange({ apply_sigma_shift: v })} />
      </Field>
    </>
  );
}
