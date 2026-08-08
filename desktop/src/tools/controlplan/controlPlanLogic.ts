import type {
  CadenceUnit, CheckInCadence, CompletedCheckIn, ControlPlanArtifact, FrozenLimitsRef,
  MonitoredItem, OcapEntry, TrainingRow,
} from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as fmeaLogic.ts's genId. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export interface ControlPlanState {
  items: MonitoredItem[];
  ocapEntries: OcapEntry[];
  trainingRows: TrainingRow[];
  cadence: CheckInCadence;
  startDate: string;
  controlChartRef: string;
  completed: CompletedCheckIn[];
  asOf: string;
}

export function emptyMonitoredItem(): MonitoredItem {
  return {
    item_id: genId("item"), characteristic: "", how_measured: "", operational_definition_ref: "",
    where: "", frequency: "", frequency_reason: "", is_primary_ctq: false, is_improve_change: false,
    owner_name: "", owner_accepted: false, per_shift_owners: [],
  };
}

export function emptyOcapEntry(monitoredItemId: string): OcapEntry {
  return {
    ocap_id: genId("ocap"), monitored_item_id: monitoredItemId, trigger_signal: "",
    action_steps: ["", ""], escalation_trigger: "", escalation_contact: "", acting_owner: "",
  };
}

export function emptyTrainingRow(): TrainingRow {
  return { row_id: genId("train"), who: "", sop_ref: null, by_whom: "", by_when: null, verified_how: "", verified_at: null, done: false };
}

export function emptyControlPlanState(): ControlPlanState {
  return {
    items: [emptyMonitoredItem()], ocapEntries: [], trainingRows: [],
    cadence: { unit: "weeks", interval: 1 }, startDate: new Date().toISOString().slice(0, 10),
    controlChartRef: "", completed: [], asOf: new Date().toISOString().slice(0, 10),
  };
}

export function controlPlanStateFromArtifact(a: ControlPlanArtifact): ControlPlanState {
  return {
    items: a.monitored_items, ocapEntries: a.ocap_entries, trainingRows: a.training_rows,
    cadence: a.check_in_schedule?.cadence ?? { unit: "weeks", interval: 1 },
    startDate: a.check_in_schedule?.start_date ?? new Date().toISOString().slice(0, 10),
    controlChartRef: a.check_in_schedule?.control_chart_ref ?? "",
    completed: a.check_in_schedule?.completed ?? [], asOf: a.as_of,
  };
}

export function missingFields(state: ControlPlanState): string[] {
  const missing: string[] = [];
  if (state.items.length === 0) missing.push("at least one monitored item");
  if (!state.items.every((i) => i.characteristic.trim() && i.how_measured.trim() && i.where.trim() && i.frequency.trim())) {
    missing.push("every item's characteristic/how/where/frequency");
  }
  return missing;
}

export function canSave(state: ControlPlanState): boolean {
  return missingFields(state).length === 0;
}

export function buildControlPlanBody(input: {
  artifactId: string; schemaVersion: number; state: ControlPlanState; frozenLimits: FrozenLimitsRef | null;
}): Record<string, unknown> {
  const now = new Date().toISOString();
  const { state, frozenLimits } = input;
  const checkInSchedule = frozenLimits
    ? {
        cadence: state.cadence, start_date: state.startDate, control_chart_ref: frozenLimits.control_chart_artifact_id,
        frozen_limits: frozenLimits, completed: state.completed,
      }
    : null;
  return {
    schema_version: input.schemaVersion, artifact_id: input.artifactId, tool_id: "T-22",
    created_at: now, updated_at: now,
    monitored_items: state.items, ocap_entries: state.ocapEntries, training_rows: state.trainingRows,
    check_in_schedule: checkInSchedule, as_of: state.asOf,
  };
}

export const CADENCE_UNIT_LABELS: Record<CadenceUnit, string> = { days: "days", weeks: "weeks", months: "months" };
