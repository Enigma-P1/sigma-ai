import { useState } from "react";
import { Button, Panel, TextInput } from "../../design/components";
import { DeleteReasonModal } from "../DeleteReasonModal";
import type { TimeStudyCycle, WorkElement } from "../../api/types";

export interface CyclesTableProps {
  elements: WorkElement[];
  cycles: TimeStudyCycle[];
  onAddCycle: () => void;
  onUpdateSeconds: (cycleNumber: number, elementId: string, seconds: number) => void;
  onUpdateNote: (cycleNumber: number, note: string) => void;
  onDeleteCycle: (cycleNumber: number, reason: string) => void;
}

/** Every recorded cycle, fully editable: a finished-cycle stopwatch row
 * lands here, and every cell can also be typed/corrected directly (an
 * outlier's note affordance points back at this table's note column) or
 * added from scratch with "+ Add cycle manually." Delete asks for a
 * logged reason (DeleteReasonModal, rubric R-MEA-04) -- the row is never
 * removed, just struck through, with the reason visible on hover. */
export function CyclesTable({ elements, cycles, onAddCycle, onUpdateSeconds, onUpdateNote, onDeleteCycle }: CyclesTableProps) {
  const [pendingDeleteCycle, setPendingDeleteCycle] = useState<number | null>(null);
  const gridStyle = { gridTemplateColumns: `4rem repeat(${elements.length}, 1fr) 2fr auto` };
  const sorted = [...cycles].sort((a, b) => a.cycle_number - b.cycle_number);

  return (
    <Panel title="Cycles" subtitle={`${cycles.length} recorded -- from the stopwatch above, or entered/edited directly here`}>
      <div className="sigma-timestudy-cycles" data-testid="timestudy-cycles-table">
        <div className="sigma-timestudy-cycles__header" style={gridStyle}>
          <span>Cycle</span>
          {elements.map((e) => (
            <span key={e.element_id}>{e.name} (s)</span>
          ))}
          <span>Note</span>
          <span />
        </div>
        {sorted.map((c) => {
          const isDeleted = c.deleted != null;
          return (
            <div
              className={`sigma-timestudy-cycles__row ${isDeleted ? "sigma-timestudy-cycles__row--deleted" : ""}`}
              key={c.cycle_number} data-testid={`timestudy-cycle-${c.cycle_number}`} style={gridStyle}
              title={isDeleted ? `Deleted: ${c.deleted!.reason}` : undefined}
            >
              <span>{c.cycle_number}</span>
              {elements.map((e, elemIndex) => {
                const et = c.element_times.find((x) => x.element_id === e.element_id);
                // Index-based testid (elements array order is stable) --
                // e.element_id is an opaque generated id, unpredictable to
                // anything outside this session (same reasoning as
                // TallyView's tap buttons).
                return (
                  <TextInput
                    key={e.element_id} type="number" step="0.1" value={et ? et.seconds : ""} placeholder="—"
                    disabled={isDeleted} data-testid={`timestudy-cycle-${c.cycle_number}-elem-${elemIndex}`}
                    onChange={(ev) => onUpdateSeconds(c.cycle_number, e.element_id, Number(ev.target.value))}
                  />
                );
              })}
              <TextInput
                value={c.observer_note} disabled={isDeleted} data-testid={`timestudy-cycle-${c.cycle_number}-note`}
                onChange={(ev) => onUpdateNote(c.cycle_number, ev.target.value)}
              />
              {isDeleted ? (
                <span className="sigma-timestudy-cycles__deleted-badge" data-testid={`timestudy-cycle-${c.cycle_number}-deleted`}>
                  Deleted
                </span>
              ) : (
                <button
                  type="button" onClick={() => setPendingDeleteCycle(c.cycle_number)} data-testid={`timestudy-cycle-${c.cycle_number}-delete`}
                  className="sigma-timestudy-cycles__delete"
                >
                  Delete
                </button>
              )}
            </div>
          );
        })}
      </div>
      <Button variant="ghost" size="sm" type="button" onClick={onAddCycle} data-testid="timestudy-add-cycle">
        + Add cycle manually
      </Button>

      {pendingDeleteCycle != null && (
        <DeleteReasonModal
          title={`Delete cycle ${pendingDeleteCycle}?`}
          bodyText="The cycle stays on the record, struck through, with this reason visible on hover -- it's excluded from the computed stats, never erased (rubric R-MEA-04)."
          testIdPrefix="timestudy-delete-reason"
          onClose={() => setPendingDeleteCycle(null)}
          onConfirm={(reason) => {
            onDeleteCycle(pendingDeleteCycle, reason);
            setPendingDeleteCycle(null);
          }}
        />
      )}
    </Panel>
  );
}
