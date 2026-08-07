import { Field, Panel, TextInput } from "../../design/components";
import type { FieldFlag } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { emptyProcessStep } from "./sipocLogic";

export interface ProcessStepsSectionProps {
  steps: { description: string }[];
  onStepsChange: (v: { description: string }[]) => void;
  scopeStart: string;
  onScopeStartChange: (v: string) => void;
  scopeEnd: string;
  onScopeEndChange: (v: string) => void;
  /** The three-tier step_count_range read (4-7 pass, 8-9 flag, outside 4-9
   * hard_flag -- prescore/sipoc.py), rendered here AND in the PrescoreStrip
   * (same dual-rendering charter uses: strip = overview, field = where to
   * fix it). Validation errors win over this when both exist (SipocForm's
   * fieldFlag()). */
  stepCountFlag?: FieldFlag;
  scopeStartFlag?: FieldFlag;
  scopeEndFlag?: FieldFlag;
}

/** Process column: the high-level step list plus the boundary fields the
 * step-count range check and the charter-scope cross-check hang off
 * (rubric R-DEF-06). */
export function ProcessStepsSection({
  steps, onStepsChange, scopeStart, onScopeStartChange, scopeEnd, onScopeEndChange, stepCountFlag, scopeStartFlag, scopeEndFlag,
}: ProcessStepsSectionProps) {
  return (
    <Panel title="Process" subtitle="4-7 high-level steps -- task-level detail belongs in the process map (T-06).">
      <Field label="Process steps" required flag={stepCountFlag} helper={`${steps.length} step${steps.length === 1 ? "" : "s"} so far -- 4-7 is the workable range.`}>
        <DynamicList
          items={steps}
          onChange={onStepsChange}
          makeEmpty={emptyProcessStep}
          minItems={1}
          addLabel="+ Add step"
          renderRow={(step, i, update) => (
            <TextInput data-testid={`sipoc-step-${i}`} value={step.description} onChange={(e) => update({ description: e.target.value })} placeholder={`Step ${i + 1}`} />
          )}
        />
      </Field>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "var(--space-2)" }}>
        <Field label="Scope start" required htmlFor="sipoc-scope-start" helper="Matches the charter's scope in/out." flag={scopeStartFlag}>
          <TextInput id="sipoc-scope-start" data-testid="sipoc-scope-start" value={scopeStart} onChange={(e) => onScopeStartChange(e.target.value)} placeholder="Order received" />
        </Field>
        <Field label="Scope end" required htmlFor="sipoc-scope-end" flag={scopeEndFlag}>
          <TextInput id="sipoc-scope-end" data-testid="sipoc-scope-end" value={scopeEnd} onChange={(e) => onScopeEndChange(e.target.value)} placeholder="Order handed off" />
        </Field>
      </div>
    </Panel>
  );
}
