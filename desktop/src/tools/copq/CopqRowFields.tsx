import { Field, SelectInput, TextInput, YesNoToggle } from "../../design/components";
import { COPQ_CATEGORIES } from "../../api/types";
import type { CopqCategory } from "../../api/types";
import { CATEGORY_LABELS, flagFor } from "./copqLogic";

export interface CopqRowValue {
  category: CopqCategory;
  custom_label: string;
  quantity: number;
  rate: number;
  period: string;
  basis: string;
  is_estimate: boolean;
}

export interface CopqRowFieldsProps {
  index: number;
  row: CopqRowValue;
  /** The engine's own computed_field amount for this row (CopqRow.amount,
   * artifacts/copq.py), present once a save has round-tripped it back --
   * undefined until then, shown honestly as "not yet computed" rather than
   * a locally-multiplied stand-in presented as authoritative. */
  serverAmount?: number;
  onChange: (patch: Partial<CopqRowValue>) => void;
  errors?: Partial<Record<"custom_label" | "quantity" | "rate" | "period" | "basis", string>>;
}

/** One COPQ cost-bucket row's fields: category, quantity x rate, period,
 * and a basis note (rubric R-DEF-05: "labeled estimate where records don't
 * exist"). Rendered inside DynamicList's row wrapper (add/remove handled
 * there, same as every charter section) -- split out purely to keep
 * CopqForm's length down, same rationale as picker's CriterionField. */
export function CopqRowFields({ index, row, serverAmount, onChange, errors }: CopqRowFieldsProps) {
  const id = (suffix: string) => `copq-row-${index}-${suffix}`;
  return (
    <>
      <div style={{ display: "grid", gridTemplateColumns: row.category === "custom" ? "1fr 1fr" : "1fr", gap: "var(--space-2)" }}>
        <Field label="Category" required htmlFor={id("category")}>
          <SelectInput id={id("category")} data-testid={id("category")} value={row.category} onChange={(e) => onChange({ category: e.target.value as CopqCategory })}>
            {COPQ_CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {CATEGORY_LABELS[c]}
              </option>
            ))}
          </SelectInput>
        </Field>
        {row.category === "custom" && (
          <Field label="Custom label" required htmlFor={id("custom-label")} flag={flagFor(errors?.custom_label)}>
            <TextInput id={id("custom-label")} data-testid={id("custom-label")} value={row.custom_label} onChange={(e) => onChange({ custom_label: e.target.value })} placeholder="e.g. warranty claims" />
          </Field>
        )}
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: "var(--space-2)" }}>
        <Field label="Quantity" required htmlFor={id("quantity")} flag={flagFor(errors?.quantity)}>
          <TextInput id={id("quantity")} type="number" data-testid={id("quantity")} value={row.quantity} onChange={(e) => onChange({ quantity: Number(e.target.value) })} />
        </Field>
        <Field label="Rate" required htmlFor={id("rate")} flag={flagFor(errors?.rate)}>
          <TextInput id={id("rate")} type="number" data-testid={id("rate")} value={row.rate} onChange={(e) => onChange({ rate: Number(e.target.value) })} />
        </Field>
        <Field label="Amount" helper="Computed by the engine on save -- never typed here.">
          <TextInput data-testid={id("amount")} value={serverAmount != null ? serverAmount.toLocaleString() : "not yet computed"} disabled />
        </Field>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
        <Field label="Period" required htmlFor={id("period")} helper="e.g. Q2 2026, per month." flag={flagFor(errors?.period)}>
          <TextInput id={id("period")} data-testid={id("period")} value={row.period} onChange={(e) => onChange({ period: e.target.value })} placeholder="Q2 2026" />
        </Field>
        <Field label="Basis note" required htmlFor={id("basis")} helper="A record, a system export, or an estimate." flag={flagFor(errors?.basis)}>
          <TextInput id={id("basis")} data-testid={id("basis")} value={row.basis} onChange={(e) => onChange({ basis: e.target.value })} placeholder="Q2 scrap log export" />
        </Field>
      </div>
      <Field label="This is an estimate, not a record" helper="Yes if there's no hard record behind this row yet.">
        <YesNoToggle name={id("estimate")} value={row.is_estimate} onChange={(v) => onChange({ is_estimate: v })} />
      </Field>
    </>
  );
}
