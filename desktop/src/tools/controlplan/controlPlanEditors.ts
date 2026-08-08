import type { MonitoredItem, OcapEntry, TrainingRow } from "../../api/types";
import { emptyMonitoredItem, emptyOcapEntry, emptyTrainingRow, genId, type ControlPlanState } from "./controlPlanLogic";

/** The monitored-item/OCAP/training/check-in CRUD handlers, factored out
 * of useControlPlanForm.ts (a single-Write-under-~120-lines split, not a
 * behavior change) -- each just calls the hook's own `update(patch)`. */
export function makeControlPlanEditors(state: ControlPlanState, update: (patch: Partial<ControlPlanState>) => void) {
  return {
    addItem: () => update({ items: [...state.items, emptyMonitoredItem()] }),
    updateItem: (itemId: string, patch: Partial<MonitoredItem>) =>
      update({ items: state.items.map((i) => (i.item_id === itemId ? { ...i, ...patch } : i)) }),
    removeItem: (itemId: string) =>
      update({ items: state.items.filter((i) => i.item_id !== itemId), ocapEntries: state.ocapEntries.filter((o) => o.monitored_item_id !== itemId) }),

    addOcap: (monitoredItemId: string) => update({ ocapEntries: [...state.ocapEntries, emptyOcapEntry(monitoredItemId)] }),
    updateOcap: (ocapId: string, patch: Partial<OcapEntry>) =>
      update({ ocapEntries: state.ocapEntries.map((o) => (o.ocap_id === ocapId ? { ...o, ...patch } : o)) }),
    removeOcap: (ocapId: string) => update({ ocapEntries: state.ocapEntries.filter((o) => o.ocap_id !== ocapId) }),

    addTraining: () => update({ trainingRows: [...state.trainingRows, emptyTrainingRow()] }),
    updateTraining: (rowId: string, patch: Partial<TrainingRow>) =>
      update({ trainingRows: state.trainingRows.map((r) => (r.row_id === rowId ? { ...r, ...patch } : r)) }),
    removeTraining: (rowId: string) => update({ trainingRows: state.trainingRows.filter((r) => r.row_id !== rowId) }),

    addCheckIn: (value: number, note: string) => {
      const now = new Date().toISOString();
      update({
        completed: [...state.completed, {
          check_in_id: genId("chk"), label: `check-in on ${now.slice(0, 10)}: is the fix holding?`,
          due_date: state.completed.length === 0 ? state.startDate : now.slice(0, 10), completed_at: now,
          entered: { kind: "manual", dataset_id: null, values: [value], subgroup: null }, note,
        }],
      });
    },
  };
}
