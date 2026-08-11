import { Button, MissingHint, Panel, VerdictBanner } from "../../design/components";
import type { FieldFlag } from "../../design/components";
import { SupplierInputSection } from "./SupplierInputSection";
import { ProcessStepsSection } from "./ProcessStepsSection";
import { OutputCustomerSection } from "./OutputCustomerSection";
import { PrescoreStrip } from "../PrescoreStrip";
import { SIPOC_CHECK_FIELD, SIPOC_CHECK_LABELS } from "./sipocChecks";
import { sipocMissingFields } from "./sipocLogic";
import { useSipocForm } from "./useSipocForm";
import type { ProjectMetadata } from "../../api/types";
import { ReportButton } from "../../app/ReportButton";

export interface SipocFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-04 SIPOC form -- five columns as three schema-paired sections (rubric
 * R-DEF-06). Composed the same way CharterForm composes its sections: this
 * file owns state (via useSipocForm) and field-flag resolution; sections
 * just render. */
export function SipocForm({ projectId, project, onSaved }: SipocFormProps) {
  const f = useSipocForm(projectId, project, onSaved);

  /** Validation errors win (schema-level); otherwise surface the matching
   * prescore check on the field it's mapped to (sipocChecks.ts) -- same
   * precedence rule as CharterForm's fieldFlag(). */
  function fieldFlag(path: string): FieldFlag | undefined {
    if (f.fieldErrors[path]) return { status: "hard_flag", message: f.fieldErrors[path] };
    const hit = f.prescore.find((r) => SIPOC_CHECK_FIELD[r.check_id] === path && r.status !== "pass");
    if (hit) return { status: hit.status === "hard_flag" ? "hard_flag" : "flag", message: hit.detail };
    return undefined;
  }

  return (
    <div data-testid="sipoc-form">
      <Panel title="SIPOC" right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="sipoc-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-04"
            disabled={f.version == null}
            disabledReason="Save this tool before downloading its report."
          />
        </span>
      }>
        {f.version == null && <p style={{ fontSize: "var(--text-xs)", color: "var(--color-text-muted)" }}>Not saved yet.</p>}
      </Panel>

      <SupplierInputSection value={f.state.supplier_input_pairs} onChange={(v) => f.update({ supplier_input_pairs: v })} />

      <ProcessStepsSection
        steps={f.state.process_steps}
        onStepsChange={(v) => f.update({ process_steps: v })}
        scopeStart={f.state.scope_start}
        onScopeStartChange={(v) => f.update({ scope_start: v })}
        scopeEnd={f.state.scope_end}
        onScopeEndChange={(v) => f.update({ scope_end: v })}
        stepCountFlag={fieldFlag("process_steps")}
        scopeStartFlag={fieldFlag("scope_start")}
        scopeEndFlag={fieldFlag("scope_end")}
      />

      <OutputCustomerSection value={f.state.output_customer_pairs} onChange={(v) => f.update({ output_customer_pairs: v })} />

      <Panel title="Save">
        {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="sipoc-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={sipocMissingFields(f.state)} />}
        <PrescoreStrip results={f.prescore} labels={SIPOC_CHECK_LABELS} />
      </Panel>
    </div>
  );
}
