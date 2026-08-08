import { Button, Field, TextInput } from "../../design/components";
import type { CheckSheetCategory, StrataFieldDef } from "../../api/types";
import "./CheckSheetForm.css";

export interface CategorySetupProps {
  categories: CheckSheetCategory[];
  onAddCategory: () => void;
  onUpdateCategory: (id: string, patch: Partial<CheckSheetCategory>) => void;
  onRemoveCategory: (id: string) => void;
  strataFields: StrataFieldDef[];
  onAddStrataField: () => void;
  onUpdateStrataField: (key: string, patch: Partial<StrataFieldDef>) => void;
  onRemoveStrataField: (key: string) => void;
}

/** T-08's first two steps, in visible order: 1. define categories, 2.
 * declare strata fields (both up front, before any tally view exists). */
export function CategorySetup({
  categories, onAddCategory, onUpdateCategory, onRemoveCategory,
  strataFields, onAddStrataField, onUpdateStrataField, onRemoveStrataField,
}: CategorySetupProps) {
  return (
    <div className="sigma-checksheet-setup">
      <div className="sigma-checksheet-setup__block">
        <div className="sigma-checksheet-setup__title">1. Categories</div>
        {categories.map((c, i) => (
          <div className="sigma-checksheet-setup__row" key={c.category_id}>
            <Field label={`Category ${i + 1}`} htmlFor={`checksheet-category-${i}-label`}>
              <TextInput
                id={`checksheet-category-${i}-label`} data-testid={`checksheet-category-${i}-label`} value={c.label}
                onChange={(e) => onUpdateCategory(c.category_id, { label: e.target.value })}
              />
            </Field>
            {categories.length > 1 && (
              <button type="button" className="sigma-checksheet-setup__remove" aria-label={`Remove ${c.label}`} onClick={() => onRemoveCategory(c.category_id)}>
                ×
              </button>
            )}
          </div>
        ))}
        <Button variant="ghost" size="sm" type="button" onClick={onAddCategory} data-testid="checksheet-add-category">
          + Add category
        </Button>
      </div>

      <div className="sigma-checksheet-setup__block">
        <div className="sigma-checksheet-setup__title">2. Stratification fields (optional — e.g. shift, station)</div>
        {strataFields.map((f, i) => (
          <div className="sigma-checksheet-setup__row" key={f.key}>
            <Field label={`Field ${i + 1} label`} htmlFor={`checksheet-strata-${i}-label`}>
              <TextInput
                id={`checksheet-strata-${i}-label`} data-testid={`checksheet-strata-${i}-label`} value={f.label}
                onChange={(e) => onUpdateStrataField(f.key, { label: e.target.value })}
              />
            </Field>
            <button type="button" className="sigma-checksheet-setup__remove" aria-label={`Remove ${f.label}`} onClick={() => onRemoveStrataField(f.key)}>
              ×
            </button>
          </div>
        ))}
        <Button variant="ghost" size="sm" type="button" onClick={onAddStrataField} data-testid="checksheet-add-strata">
          + Add stratification field
        </Button>
      </div>
    </div>
  );
}
