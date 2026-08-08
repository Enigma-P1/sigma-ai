import { useState } from "react";
import { Panel, TextInput } from "../../design/components";
import type { CheckSheetCategory, CheckSheetEntry, StrataFieldDef } from "../../api/types";

export interface EntriesTableProps {
  entries: CheckSheetEntry[];
  categories: CheckSheetCategory[];
  strataFields: StrataFieldDef[];
  onUpdateNote: (entryId: string, note: string) => void;
  onRemove: (entryId: string) => void;
}

/** The captured-so-far log: editable notes, delete with a two-click
 * confirm (no native browser dialog -- keeps this reliably driveable from
 * the smoke test and any future component test). */
export function EntriesTable({ entries, categories, strataFields, onUpdateNote, onRemove }: EntriesTableProps) {
  const [confirmingId, setConfirmingId] = useState<string | null>(null);
  const labelById = Object.fromEntries(categories.map((c) => [c.category_id, c.label]));

  function handleDeleteClick(entryId: string) {
    if (confirmingId === entryId) {
      onRemove(entryId);
      setConfirmingId(null);
    } else {
      setConfirmingId(entryId);
    }
  }

  if (entries.length === 0) {
    return (
      <Panel title="Entries" subtitle="Nothing tallied yet">
        <p data-testid="checksheet-entries-empty">Tap a category above to log the first entry.</p>
      </Panel>
    );
  }

  const sorted = [...entries].sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  return (
    <Panel title="Entries" subtitle={`${entries.length} tallied`}>
      <div className="sigma-checksheet-entries" data-testid="checksheet-entries-table">
        {sorted.map((e) => (
          <div className="sigma-checksheet-entries__row" key={e.entry_id} data-testid={`checksheet-entry-${e.entry_id}`}>
            <span className="sigma-checksheet-entries__category">{labelById[e.category_id] ?? e.category_id}</span>
            <span className="sigma-checksheet-entries__timestamp">{e.timestamp}</span>
            <span className="sigma-checksheet-entries__strata">
              {strataFields.map((f) => e.strata[f.key]).filter(Boolean).join(", ") || "—"}
            </span>
            <TextInput
              placeholder="Note…" value={e.note} data-testid={`checksheet-entry-${e.entry_id}-note`}
              onChange={(ev) => onUpdateNote(e.entry_id, ev.target.value)}
            />
            <button
              type="button" className={`sigma-checksheet-entries__delete ${confirmingId === e.entry_id ? "sigma-checksheet-entries__delete--confirm" : ""}`}
              data-testid={`checksheet-entry-${e.entry_id}-delete`} onClick={() => handleDeleteClick(e.entry_id)}
              onBlur={() => setConfirmingId((id) => (id === e.entry_id ? null : id))}
            >
              {confirmingId === e.entry_id ? "Confirm?" : "Delete"}
            </button>
          </div>
        ))}
      </div>
    </Panel>
  );
}
