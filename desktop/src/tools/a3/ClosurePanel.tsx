import { Button, Field, Panel, TextInput, VerdictBanner } from "../../design/components";
import type { ClosureBlock, LessonEntry, ObjectivesInput, OpenItem, PilotDirection } from "../../api/types";

export interface ClosurePanelProps {
  closure: ClosureBlock;
  onUpdate: (patch: Partial<ClosureBlock>) => void;
  onLoadFmea: () => void;
}

let counter = 0;
function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

const EMPTY_OBJECTIVES: ObjectivesInput = { charter_baseline_value: 0, charter_goal_value: 0, achieved_value: 0, direction: "lower_is_better" };

/** Closure block: objectives-vs-charter (reuses T-20's own gap arithmetic
 * server-side), lessons (>=2, at least one went-wrong), open items with
 * owners, and the close_blocked banner naming the linked FMEA's own
 * blocking rows -- honoring the engine's hard refusal to mark the project
 * closed while blocked (R-WRAP-03/R-ANA-03). */
export function ClosurePanel({ closure, onUpdate, onLoadFmea }: ClosurePanelProps) {
  const gap = closure.objectives_verdict?.value ?? null;
  const closeCheck = closure.close_check?.value ?? null;
  const obj = closure.objectives_input ?? EMPTY_OBJECTIVES;

  function updateObjectives(patch: Partial<ObjectivesInput>) {
    onUpdate({ objectives_input: { ...obj, ...patch } });
  }
  function addLesson(wentWrong: boolean) {
    onUpdate({ lessons: [...closure.lessons, { lesson_id: genId("lesson"), text: "", went_wrong: wentWrong }] });
  }
  function updateLesson(id: string, patch: Partial<LessonEntry>) {
    onUpdate({ lessons: closure.lessons.map((l) => (l.lesson_id === id ? { ...l, ...patch } : l)) });
  }
  function addOpenItem() {
    onUpdate({ open_items: [...closure.open_items, { item_id: genId("open"), description: "", owner: "" }] });
  }
  function updateOpenItem(id: string, patch: Partial<OpenItem>) {
    onUpdate({ open_items: closure.open_items.map((o) => (o.item_id === id ? { ...o, ...patch } : o)) });
  }

  return (
    <Panel title="Closure & Lessons">
      <Panel title="Objectives vs. charter" collapsible defaultOpen={Boolean(gap)}>
        <div className="sigma-a3-objectives-inputs">
          <Field label="Charter baseline" htmlFor="a3-obj-baseline"><TextInput id="a3-obj-baseline" type="number" value={obj.charter_baseline_value} onChange={(e) => updateObjectives({ charter_baseline_value: Number(e.target.value) })} /></Field>
          <Field label="Charter goal" htmlFor="a3-obj-goal"><TextInput id="a3-obj-goal" type="number" value={obj.charter_goal_value} onChange={(e) => updateObjectives({ charter_goal_value: Number(e.target.value) })} /></Field>
          <Field label="Achieved" htmlFor="a3-obj-achieved"><TextInput id="a3-obj-achieved" data-testid="a3-obj-achieved" type="number" value={obj.achieved_value} onChange={(e) => updateObjectives({ achieved_value: Number(e.target.value) })} /></Field>
          <Field label="Direction" htmlFor="a3-obj-direction">
            <select id="a3-obj-direction" className="sigma-input" value={obj.direction} onChange={(e) => updateObjectives({ direction: e.target.value as PilotDirection })}>
              <option value="lower_is_better">Lower is better</option>
              <option value="higher_is_better">Higher is better</option>
            </select>
          </Field>
        </div>
        {gap && (
          <div data-testid="a3-objectives-verdict">
            <VerdictBanner tone={gap.goal_met ? "pass" : "flag"} headline={gap.loop_verdict} detail={`goal ${gap.charter_goal_value}, achieved ${gap.after_value}, remaining ${gap.remaining.toFixed(2)}`} />
          </div>
        )}
      </Panel>

      <Panel title="Lessons" subtitle="At least two, including something that went wrong">
        {closure.lessons.map((l) => (
          <div key={l.lesson_id} className="sigma-a3-lesson-row">
            <TextInput data-testid={`a3-lesson-${l.lesson_id}`} value={l.text} onChange={(e) => updateLesson(l.lesson_id, { text: e.target.value })} />
            <label><input type="checkbox" checked={l.went_wrong} onChange={(e) => updateLesson(l.lesson_id, { went_wrong: e.target.checked })} /> Went wrong</label>
          </div>
        ))}
        <Button variant="ghost" size="sm" onClick={() => addLesson(false)} data-testid="a3-add-lesson">+ Add lesson</Button>
        <Button variant="ghost" size="sm" onClick={() => addLesson(true)} data-testid="a3-add-lesson-went-wrong">+ Add a went-wrong lesson</Button>
      </Panel>

      <Panel title="Open items" subtitle="The remaining gap, pending check-ins, unverified causes -- each with an owner">
        {closure.open_items.map((o) => (
          <div key={o.item_id} className="sigma-a3-openitem-row">
            <TextInput value={o.description} onChange={(e) => updateOpenItem(o.item_id, { description: e.target.value })} placeholder="description" />
            <TextInput value={o.owner} onChange={(e) => updateOpenItem(o.item_id, { owner: e.target.value })} placeholder="owner" />
          </div>
        ))}
        <Button variant="ghost" size="sm" onClick={addOpenItem} data-testid="a3-add-open-item">+ Add open item</Button>
      </Panel>

      <Panel title="Project close -- the FMEA sev-block + standing-hard-flag check">
        <Button variant="ghost" size="sm" onClick={onLoadFmea} data-testid="a3-load-fmea-check">Load latest FMEA</Button>
        {closeCheck && (
          <div data-testid="a3-close-check-banner">
            <VerdictBanner
              tone={closeCheck.close_blocked ? "fail" : "pass"}
              headline={
                !closeCheck.close_blocked
                  ? "Close check clear -- no FMEA block, no standing hard flags"
                  : closeCheck.blocking_rows.length > 0 && (closeCheck.standing_hard_flags ?? []).length > 0
                    ? "Project may NOT close -- unaddressed severity-9/10 row(s) + standing prescore hard flag(s)"
                    : closeCheck.blocking_rows.length > 0
                      ? "Project may NOT close -- unaddressed severity-9/10 row(s)"
                      : "Project may NOT close -- standing prescore hard flag(s) on saved artifacts"
              }
              detail={
                [
                  ...closeCheck.blocking_rows.map((r) => `${r.row_id}: ${r.failure_mode} (sev ${r.severity}) -- ${r.reason}`),
                  ...(closeCheck.standing_hard_flags ?? []).map((f) => `${f.artifact_id}: ${f.check_id} -- ${f.detail}`),
                ].join("; ") || closeCheck.reason
              }
            />
          </div>
        )}
        <label>
          <input
            type="checkbox" data-testid="a3-project-status-closed" checked={closure.project_status === "closed"}
            onChange={(e) => onUpdate({ project_status: e.target.checked ? "closed" : "open" })}
          />
          {" "}Mark project closed
        </label>
      </Panel>
    </Panel>
  );
}
