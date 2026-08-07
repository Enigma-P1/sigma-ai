import "./Field.css";

export interface YesNoToggleProps {
  value: boolean | null;
  onChange: (value: boolean) => void;
  name: string;
  disabled?: boolean;
}

/** Two-button yes/no toggle — used by the T-01 picker's five intake
 * criteria. Not a native radio group because the selected state needs
 * pass/fail coloring, not just a checkmark. */
export function YesNoToggle({ value, onChange, name, disabled }: YesNoToggleProps) {
  return (
    <div className="sigma-yesno" role="radiogroup" aria-label={name}>
      <button
        type="button"
        role="radio"
        aria-checked={value === true}
        disabled={disabled}
        data-testid={`${name}-yes`}
        className={`sigma-yesno__option ${value === true ? "sigma-yesno__option--selected-yes" : ""}`}
        onClick={() => onChange(true)}
      >
        Yes
      </button>
      <button
        type="button"
        role="radio"
        aria-checked={value === false}
        disabled={disabled}
        data-testid={`${name}-no`}
        className={`sigma-yesno__option ${value === false ? "sigma-yesno__option--selected-no" : ""}`}
        onClick={() => onChange(false)}
      >
        No
      </button>
    </div>
  );
}
