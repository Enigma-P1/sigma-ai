import type { ReactNode } from "react";
import { Button } from "../../design/components";
import "./DynamicList.css";

export interface DynamicListProps<T> {
  items: T[];
  onChange: (items: T[]) => void;
  makeEmpty: () => T;
  renderRow: (item: T, index: number, update: (value: T) => void) => ReactNode;
  addLabel: string;
  /** Rows can't be removed below this count (e.g. team needs >=1 member). */
  minItems?: number;
}

/** Small add/remove list editor shared by every repeatable block in the
 * charter form (team, timeline, risks, consequential metrics) -- one
 * implementation instead of four near-identical ones. */
export function DynamicList<T>({ items, onChange, makeEmpty, renderRow, addLabel, minItems = 0 }: DynamicListProps<T>) {
  function updateAt(index: number, value: T) {
    onChange(items.map((it, i) => (i === index ? value : it)));
  }
  function removeAt(index: number) {
    onChange(items.filter((_, i) => i !== index));
  }

  return (
    <div className="sigma-dynlist">
      {items.map((item, i) => (
        // Index keys are fine here: rows have no stable id, aren't
        // reordered, and only ever grow/shrink from the end or by removal.
        <div className="sigma-dynlist__row" key={i}>
          <div className="sigma-dynlist__row-fields">{renderRow(item, i, (value) => updateAt(i, value))}</div>
          {items.length > minItems && (
            <button type="button" className="sigma-dynlist__remove" onClick={() => removeAt(i)} aria-label="Remove row">
              ×
            </button>
          )}
        </div>
      ))}
      <Button variant="ghost" size="sm" type="button" onClick={() => onChange([...items, makeEmpty()])}>
        {addLabel}
      </Button>
    </div>
  );
}
