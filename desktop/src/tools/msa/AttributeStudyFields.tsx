import { Field, TextInput, YesNoToggle } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { emptyAttributeItem } from "./msaLogic";
import type { AttributeItemValue } from "./msaLogic";

export interface AttributeStudyFieldsProps {
  items: AttributeItemValue[];
  onItemsChange: (items: AttributeItemValue[]) => void;
}

/** T-12 attribute-path study design: a two-rater pass/fail judgment table.
 * No resolution pre-check or gauge fields here -- that's a continuous-
 * gauge concept only (matrix §4a). */
export function AttributeStudyFields({ items, onItemsChange }: AttributeStudyFieldsProps) {
  return (
    <Field label="Items and two-rater judgments" helper="Same items, two raters, independent pass/fail judgment each -- >=10 items is the guidance.">
      <DynamicList
        items={items}
        onChange={onItemsChange}
        makeEmpty={() => emptyAttributeItem(items.length)}
        minItems={1}
        addLabel="+ Add item"
        renderRow={(row, i, update) => (
          <div className="sigma-msa-attr-row" data-testid={`msa-attr-row-${i}`}>
            <TextInput
              data-testid={`msa-attr-item-id-${i}`} value={row.item_id}
              onChange={(e) => update({ ...row, item_id: e.target.value })} placeholder={`item-${i + 1}`}
            />
            <span className="sigma-msa-attr-row__label">Rater A: pass?</span>
            <YesNoToggle name={`msa-rater-a-${i}`} value={row.rater_a} onChange={(v) => update({ ...row, rater_a: v })} />
            <span className="sigma-msa-attr-row__label">Rater B: pass?</span>
            <YesNoToggle name={`msa-rater-b-${i}`} value={row.rater_b} onChange={(v) => update({ ...row, rater_b: v })} />
          </div>
        )}
      />
    </Field>
  );
}
