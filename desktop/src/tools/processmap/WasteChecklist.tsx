import { TextInput } from "../../design/components";
import type { WasteEntry, WasteId } from "../../api/types";
import { WASTE_CATALOG } from "./processMapLogic";

export interface WasteChecklistProps {
  wastes: WasteEntry[];
  onChange: (wastes: WasteEntry[]) => void;
}

/** The 8-wastes checklist for one step: checking a waste adds a
 * WasteEntry with an empty note; unchecking removes it. The note field
 * only appears once checked (rubric R-MEA-02: "concrete observations tied
 * to locations on the map," never a recited list -- prescore's
 * waste_notes_present flags a checked-but-empty note). */
export function WasteChecklist({ wastes, onChange }: WasteChecklistProps) {
  function noteFor(id: WasteId): string | undefined {
    return wastes.find((w) => w.waste_id === id)?.note;
  }
  function toggle(id: WasteId, checked: boolean) {
    if (checked) onChange([...wastes, { waste_id: id, note: "" }]);
    else onChange(wastes.filter((w) => w.waste_id !== id));
  }
  function setNote(id: WasteId, note: string) {
    onChange(wastes.map((w) => (w.waste_id === id ? { ...w, note } : w)));
  }

  return (
    <div className="sigma-processmap-wastes">
      {WASTE_CATALOG.map(({ id, label }) => {
        const note = noteFor(id);
        const checked = note != null;
        return (
          <div className="sigma-processmap-waste-row" key={id}>
            <label className="sigma-processmap-waste-label">
              <input type="checkbox" data-testid={`processmap-waste-${id}`} checked={checked} onChange={(e) => toggle(id, e.target.checked)} />
              {label}
            </label>
            {checked && (
              <TextInput
                data-testid={`processmap-waste-note-${id}`}
                value={note} placeholder="What did you observe, and where?"
                onChange={(e) => setNote(id, e.target.value)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
