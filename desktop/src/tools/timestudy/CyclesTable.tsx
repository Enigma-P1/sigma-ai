import { useState } from "react";
import { Button, Panel, TextInput } from "../../design/components";
import type { TimeStudyCycle, WorkElement } from "../../api/types";

export interface CyclesTableProps {
  elements: WorkElement[];
  cycles: TimeStudyCycle[];
  onAddCycle: () => void;
  onUpdateSeconds: (cycleNumber: number, elementId: string, seconds: number) => void;
  onUpdateNote: (cycleNumber: number, note: string) => void;
  onRemove: (cycleNumber: number) => void;
}

/** Every recorded cycle, fully editable: a finished-cycle stopwatch row
 * lands here, and every cell can also be typed/corrected directly (an
 * outlier's note affordance points back at this table's note column) or
 * added from scratch with "+ Add cycle manually." Delete uses the same
 * two-click confirm as EntriesTable, no native dialog. */
export function CyclesTable({ elements, cycles, onAddCycle, onUpdateSeconds, onUpdateNote, onRemove }: CyclesTableProps) {
  const [confirmingCycle, setConfirmingCycle] = useState<number | null>(null);
  const gridStyle = { gridTemplateColumns: `4rem repeat(${elements.length}, 1fr) 2fr auto` };

  function handleDeleteClick(cycleNumber: number) {
    if (confirmingCycle === cycleNumber) {
      onRemove(cycleNumber);
      setConfirmingCycle(null);
    } else {
      setConfirmingCycle(cycleNumber);
    }
  }

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
        {sorted.map((c) => (
          <div className="sigma-timestudy-cycles__row" key={c.cycle_number} data-testid={`timestudy-cycle-${c.cycle_number}`} style={gridStyle}>
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
                  data-testid={`timestudy-cycle-${c.cycle_number}-elem-${elemIndex}`}
                  onChange={(ev) => onUpdateSeconds(c.cycle_number, e.element_id, Number(ev.target.value))}
                />
              );
            })}
            <TextInput
              value={c.observer_note} data-testid={`timestudy-cycle-${c.cycle_number}-note`}
              onChange={(ev) => onUpdateNote(c.cycle_number, ev.target.value)}
            />
            <button
              type="button" onClick={() => handleDeleteClick(c.cycle_number)} data-testid={`timestudy-cycle-${c.cycle_number}-delete`}
              className={`sigma-timestudy-cycles__delete ${confirmingCycle === c.cycle_number ? "sigma-timestudy-cycles__delete--confirm" : ""}`}
              onBlur={() => setConfirmingCycle((n) => (n === c.cycle_number ? null : n))}
            >
              {confirmingCycle === c.cycle_number ? "Confirm?" : "Delete"}
            </button>
          </div>
        ))}
      </div>
      <Button variant="ghost" size="sm" type="button" onClick={onAddCycle} data-testid="timestudy-add-cycle">
        + Add cycle manually
      </Button>
    </Panel>
  );
}
