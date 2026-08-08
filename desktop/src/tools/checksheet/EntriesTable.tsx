import { useState } from "react";
import { Panel, TextInput } from "../../design/components";
import { DeleteReasonModal } from "../DeleteReasonModal";
import type { CheckSheetCategory, CheckSheetEntry, StrataFieldDef } from "../../api/types";

export interface EntriesTableProps {
  entries: CheckSheetEntry[];
  categories: CheckSheetCategory[];
  strataFields: StrataFieldDef[];
  onUpdateNote: (entryId: string, note: string) => void;
  onDeleteEntry: (entryId: string, reason: string) => void;
}

/** The captured-so-far log: editable notes, delete asks for a logged
 * reason (DeleteReasonModal, rubric R-MEA-04 generalized to T-08) --
 * the entry is never removed, just struck through with the reason
 * visible on hover. */
export function EntriesTable({ entries, categories, strataFields, onUpdateNote, onDeleteEntry }: EntriesTableProps) {
  const [pendingDeleteId, setPendingDeleteId] = useState<string | null>(null);
  const labelById = Object.fromEntries(categories.map((c) => [c.category_id, c.label]));

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
        {sorted.map((e) => {
          const isDeleted = e.deleted != null;
          return (
            <div
              className={`sigma-checksheet-entries__row ${isDeleted ? "sigma-checksheet-entries__row--deleted" : ""}`}
              key={e.entry_id} data-testid={`checksheet-entry-${e.entry_id}`}
              title={isDeleted ? `Deleted: ${e.deleted!.reason}` : undefined}
            >
              <span className="sigma-checksheet-entries__category">{labelById[e.category_id] ?? e.category_id}</span>
              <span className="sigma-checksheet-entries__timestamp">{e.timestamp}</span>
              <span className="sigma-checksheet-entries__strata">
                {strataFields.map((f) => e.strata[f.key]).filter(Boolean).join(", ") || "—"}
              </span>
              <TextInput
                placeholder="Note…" value={e.note} disabled={isDeleted} data-testid={`checksheet-entry-${e.entry_id}-note`}
                onChange={(ev) => onUpdateNote(e.entry_id, ev.target.value)}
              />
              {isDeleted ? (
                <span className="sigma-checksheet-entries__deleted-badge" data-testid={`checksheet-entry-${e.entry_id}-deleted`}>
                  Deleted
                </span>
              ) : (
                <button
                  type="button" className="sigma-checksheet-entries__delete"
                  data-testid={`checksheet-entry-${e.entry_id}-delete`} onClick={() => setPendingDeleteId(e.entry_id)}
                >
                  Delete
                </button>
              )}
            </div>
          );
        })}
      </div>

      {pendingDeleteId != null && (
        <DeleteReasonModal
          title="Delete this entry?"
          bodyText="The entry stays on the record, struck through, with this reason visible on hover -- it's excluded from the exported dataset, never erased (rubric R-MEA-04)."
          testIdPrefix="checksheet-delete-reason"
          onClose={() => setPendingDeleteId(null)}
          onConfirm={(reason) => {
            onDeleteEntry(pendingDeleteId, reason);
            setPendingDeleteId(null);
          }}
        />
      )}
    </Panel>
  );
}
