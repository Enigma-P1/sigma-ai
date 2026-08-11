import { Button, Field, MissingHint, Panel, VerdictBanner } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { CopqRowFields } from "./CopqRowFields";
import { PrescoreStrip } from "../PrescoreStrip";
import { COPQ_CHECK_LABELS } from "./copqChecks";
import { copqMissingFields, copqRowsFlag, copqTotalDisplay, emptyCopqRow } from "./copqLogic";
import { useCopqForm } from "./useCopqForm";
import type { ProjectMetadata } from "../../api/types";
import { ReportButton } from "../../app/ReportButton";

export interface CopqFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-02 COPQ / Benefit Calculator form: category rows, each quantity x
 * rate, rolling up to a server-computed total (rubric R-DEF-05: "no
 * hand-typed totals anywhere"). Every row's amount and the grand total
 * always render from the engine's own response, never a client-side
 * number presented as authoritative -- see copqLogic.ts's draftCopqTotal
 * and useCopqForm's handleSave. */
export function CopqForm({ projectId, project, onSaved }: CopqFormProps) {
  const f = useCopqForm(projectId, project, onSaved);

  function rowError(i: number, field: string): string | undefined {
    return f.fieldErrors[`rows.${i}.${field}`];
  }

  return (
    <Panel title="COPQ / Benefit Calculator" right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="copq-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-02"
            disabled={f.version == null}
            disabledReason="Save this tool before downloading its report."
          />
        </span>
      }>
      <Field label="Cost rows" flag={copqRowsFlag(f.prescore)}>
        <DynamicList
          items={f.rows}
          onChange={f.updateRows}
          makeEmpty={emptyCopqRow}
          minItems={1}
          addLabel="+ Add cost row"
          renderRow={(row, i, update) => (
            <CopqRowFields
              index={i}
              row={row}
              serverAmount={f.serverArtifact?.rows[i]?.amount}
              onChange={(patch) => update({ ...row, ...patch })}
              errors={{
                custom_label: rowError(i, "custom_label"),
                quantity: rowError(i, "quantity"),
                rate: rowError(i, "rate"),
                period: rowError(i, "period"),
                basis: rowError(i, "basis"),
              }}
            />
          )}
        />
      </Field>

      <div data-testid="copq-total">
        <VerdictBanner
          tone={f.serverArtifact ? "pass" : "neutral"}
          headline={
            f.serverArtifact
              ? `Total: ${copqTotalDisplay(f.serverArtifact)}`
              : "Total not yet computed — save to get the engine's number"
          }
          detail={f.serverArtifact ? <span title="R-DEF-05">Computed by the engine, never typed in on this screen.</span> : undefined}
        />
      </div>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="copq-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>
      {!f.saving && <MissingHint fields={copqMissingFields(f.rows)} />}

      <PrescoreStrip results={f.prescore} labels={COPQ_CHECK_LABELS} />
    </Panel>
  );
}
