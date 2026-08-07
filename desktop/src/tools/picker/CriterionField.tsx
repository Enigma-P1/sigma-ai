import { Field, TextInput, YesNoToggle } from "../../design/components";
import type { FieldFlag } from "../../design/components";

export interface CriterionFieldProps {
  fieldKey: string;
  label: string;
  helper: string;
  answer: boolean | null;
  detail: string;
  flag?: FieldFlag;
  onAnswerChange: (v: boolean) => void;
  onDetailChange: (v: string) => void;
}

/** One of the picker's five intake criteria: a yes/no plus a one-line
 * reason. Split out from PickerForm purely to keep that file's length down
 * -- there are five near-identical instances of this block. */
export function CriterionField({
  fieldKey,
  label,
  helper,
  answer,
  detail,
  flag,
  onAnswerChange,
  onDetailChange,
}: CriterionFieldProps) {
  return (
    <Field label={label} helper={helper} required flag={flag}>
      <YesNoToggle name={`picker-${fieldKey}`} value={answer} onChange={onAnswerChange} />
      <TextInput
        data-testid={`picker-${fieldKey}-detail`}
        value={detail}
        onChange={(e) => onDetailChange(e.target.value)}
        placeholder="One line: what makes this true?"
        style={{ marginTop: "var(--space-2)" }}
      />
    </Field>
  );
}
