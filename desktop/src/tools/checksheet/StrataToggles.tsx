import { useState } from "react";
import { Button, TextInput } from "../../design/components";
import type { StrataFieldDef } from "../../api/types";

export interface StrataTogglesProps {
  field: StrataFieldDef;
  /** Position among declared strata fields -- used for data-testids
   * instead of field.key, which is an opaque generated id a test script
   * (or anything else outside this session) can't predict in advance. */
  index: number;
  options: string[];
  active: string;
  onSetActive: (value: string) => void;
  onAddOption: (value: string) => void;
}

/** One strata field's toggle-chip row: click a chip to set it as the
 * active value for the next tap, or type + add a new value to grow the
 * chip set (PLAN §4.1 T-08 row: "the current strata selections shown as
 * toggles"). Values are freeform text -- nothing in the schema enumerates
 * them, so the chip set is bootstrapped from whatever gets typed here. */
export function StrataToggles({ field, index, options, active, onSetActive, onAddOption }: StrataTogglesProps) {
  const [draft, setDraft] = useState("");

  function addDraft() {
    const value = draft.trim();
    if (!value) return;
    onAddOption(value);
    setDraft("");
  }

  return (
    <div className="sigma-checksheet-strata" data-testid={`checksheet-strata-toggles-${index}`}>
      <div className="sigma-checksheet-strata__label">{field.label}</div>
      <div className="sigma-checksheet-strata__chips">
        {options.map((value) => (
          <button
            key={value} type="button" onClick={() => onSetActive(value)}
            className={`sigma-checksheet-chip ${active === value ? "sigma-checksheet-chip--active" : ""}`}
            data-testid={`checksheet-strata-chip-${index}-${value}`}
          >
            {value}
          </button>
        ))}
      </div>
      <div className="sigma-checksheet-strata__add">
        <TextInput
          placeholder={`Add a ${field.label.toLowerCase()} value…`} value={draft}
          data-testid={`checksheet-strata-add-${index}-input`}
          onChange={(e) => setDraft(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addDraft();
            }
          }}
        />
        <Button variant="ghost" size="sm" type="button" onClick={addDraft} data-testid={`checksheet-strata-add-${index}-button`}>
          + Add
        </Button>
      </div>
    </div>
  );
}
