import { Button, Field, MissingHint, Panel, SelectInput, TextInput, VerdictBanner } from "../../design/components";
import { CustomersSection } from "./CustomersSection";
import { StatementsSection } from "./StatementsSection";
import { NeedsSection } from "./NeedsSection";
import { CtqsSection } from "./CtqsSection";
import { PrescoreStrip } from "../PrescoreStrip";
import { VOC_CTQ_CHECK_LABELS } from "./vocCtqChecks";
import { makeCtq, makeNeed, makeStatement, vocCtqMissingFields } from "./vocCtqLogic";
import { useVocCtqForm } from "./useVocCtqForm";
import type { ProjectMetadata } from "../../api/types";

export interface VocCtqFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-05 VoC -> CTQ Tree form: statements -> needs -> CTQs, each level
 * linked to its parent by picking from what already exists above rather
 * than free-typed IDs (rubric R-DEF-07). Composed the same way CharterForm
 * composes sections: this file owns state (via useVocCtqForm) and passes
 * it down; sections just render. */
export function VocCtqForm({ projectId, project, onSaved }: VocCtqFormProps) {
  const f = useVocCtqForm(projectId, project, onSaved);

  return (
    <div data-testid="voc-ctq-form">
      <Panel title="VoC → CTQ Tree" right={f.version != null && <span data-testid="voc-ctq-version-badge">v{f.version} saved</span>}>
        {f.version == null && <p style={{ fontSize: "var(--text-xs)", color: "var(--color-text-muted)" }}>Not saved yet.</p>}
      </Panel>

      <CustomersSection value={f.state.customers} onChange={(v) => f.update({ customers: v })} />

      <StatementsSection value={f.state.statements} onChange={(v) => f.update({ statements: v })} makeEmpty={() => makeStatement(f.state.statements.length)} />

      <NeedsSection value={f.state.needs} onChange={(v) => f.update({ needs: v })} makeEmpty={() => makeNeed(f.state.needs.length)} statements={f.state.statements} />

      <CtqsSection value={f.state.ctqs} onChange={(v) => f.update({ ctqs: v })} makeEmpty={() => makeCtq(f.state.ctqs.length)} needs={f.state.needs} />

      <Panel title="Primary CTQ and charter link">
        <Field label="Primary CTQ" required htmlFor="voc-primary-ctq" helper="Which CTQ is the charter's primary metric?">
          <SelectInput id="voc-primary-ctq" data-testid="voc-primary-ctq" value={f.state.primary_ctq_id} onChange={(e) => f.update({ primary_ctq_id: e.target.value })}>
            <option value="">Pick the primary CTQ…</option>
            {f.state.ctqs.map((c) => (
              <option key={c.ctq_id} value={c.ctq_id}>
                {c.ctq_id}: {c.measure || "(empty)"}
              </option>
            ))}
          </SelectInput>
        </Field>
        <Field label="Charter metric link" required htmlFor="voc-charter-link" helper="How this CTQ matches the charter's primary metric, or explains the mismatch.">
          <TextInput
            id="voc-charter-link"
            data-testid="voc-charter-link"
            value={f.state.charter_metric_link}
            onChange={(e) => f.update({ charter_metric_link: e.target.value })}
            placeholder="matches charter primary metric: line-2 scrap rate"
          />
        </Field>
      </Panel>

      <Panel title="Save">
        {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="voc-ctq-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={vocCtqMissingFields(f.state)} />}
        <PrescoreStrip results={f.prescore} labels={VOC_CTQ_CHECK_LABELS} />
      </Panel>
    </div>
  );
}
