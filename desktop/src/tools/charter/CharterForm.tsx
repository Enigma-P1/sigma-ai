import { useEffect, useState } from "react";
import { Button, Field, Panel, TextArea, VerdictBanner } from "../../design/components";
import type { FieldFlag } from "../../design/components";
import { ProblemStatementSection } from "./ProblemStatementSection";
import { GoalSection } from "./GoalSection";
import { ScopeTeamSection } from "./ScopeTeamSection";
import { TimelineImpactSection } from "./TimelineImpactSection";
import { RisksSection } from "./RisksSection";
import { PrescoreStrip } from "../PrescoreStrip";
import { CHARTER_CHECK_FIELD, CHARTER_CHECK_LABELS } from "./charterChecks";
import { downloadCharterPdf, loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type {
  BusinessImpact,
  PrescoreResult,
  ProblemStatement,
  ProjectMetadata,
  RiskRow,
  ScopeBlock,
  SmartGoal,
  TeamMember,
  TimelineMilestone,
} from "../../api/types";

const ARTIFACT_ID = "charter";
const SCHEMA_VERSION = 1;

interface CharterState {
  problem_statement: ProblemStatement;
  goal: SmartGoal;
  scope: ScopeBlock;
  team: TeamMember[];
  process_owner: TeamMember;
  timeline: TimelineMilestone[];
  business_impact: BusinessImpact;
  risks: RiskRow[];
  notes: string;
}

const EMPTY_STATE: CharterState = {
  problem_statement: { what: "", where: "", when: "", magnitude: { number: 0, unit: "", period: "" } },
  goal: { statement: "", metric_name: "", baseline_value: null, target_value: 0, unit: "", target_date: "", consequential_metrics: [] },
  scope: { in_scope: "", out_scope: "" },
  team: [{ name: "", role: "" }],
  process_owner: { name: "", role: "" },
  timeline: [{ name: "", date: "" }],
  business_impact: { amount: 0, unit: "", basis: "" },
  risks: [],
  notes: "",
};

export interface CharterFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-03 Project Charter form -- the second of the two proof screens (M1
 * brief). Composed from the section components in this directory; this
 * file owns the state, load/save wiring, and field-flag resolution. */
export function CharterForm({ projectId, project, onSaved }: CharterFormProps) {
  const { setSaveState } = useSaveState();
  const [state, setState] = useState<CharterState>(EMPTY_STATE);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [exporting, setExporting] = useState(false);
  const [exportError, setExportError] = useState<string | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as CharterState;
        setState({
          problem_statement: d.problem_statement,
          goal: d.goal,
          scope: d.scope,
          team: d.team,
          process_owner: d.process_owner,
          timeline: d.timeline,
          business_impact: d.business_impact,
          risks: d.risks,
          notes: (data as { notes?: string }).notes ?? "",
        });
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  /** Validation errors win (schema-level); otherwise surface the matching
   * prescore check, if any, on the field it's mapped to in charterChecks.ts. */
  function fieldFlag(path: string): FieldFlag | undefined {
    if (fieldErrors[path]) return { status: "hard_flag", message: fieldErrors[path] };
    const hit = prescore.find((r) => CHARTER_CHECK_FIELD[r.check_id] === path && r.status !== "pass");
    if (hit) return { status: hit.status === "hard_flag" ? "hard_flag" : "flag", message: hit.detail };
    return undefined;
  }

  const canSave =
    !saving &&
    state.problem_statement.what.trim() &&
    state.problem_statement.where.trim() &&
    state.problem_statement.when.trim() &&
    state.goal.statement.trim() &&
    state.goal.metric_name.trim() &&
    state.goal.unit.trim() &&
    state.goal.target_date.trim() &&
    state.scope.in_scope.trim() &&
    state.scope.out_scope.trim() &&
    state.process_owner.name.trim() &&
    state.process_owner.role.trim() &&
    state.team.length > 0 &&
    state.timeline.length > 0 &&
    state.business_impact.unit.trim() &&
    state.business_impact.basis.trim();

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const now = new Date().toISOString();
    const body = {
      schema_version: SCHEMA_VERSION,
      artifact_id: ARTIFACT_ID,
      tool_id: "T-03",
      created_at: now,
      updated_at: now,
      notes: state.notes.trim() || null,
      problem_statement: state.problem_statement,
      goal: state.goal,
      scope: state.scope,
      team: state.team,
      process_owner: state.process_owner,
      timeline: state.timeline,
      business_impact: state.business_impact,
      risks: state.risks,
    };

    try {
      const res = await saveArtifact(projectId, "T-03", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setPrescore(await runPrescore("T-03", body));
      } catch {
        /* prescore is a nice-to-have on top of a successful save, not a blocker */
      }
    } catch (err) {
      setSaveState("error");
      if (err instanceof ApiError && err.validation) {
        const grouped = groupValidationByField(err.validation);
        const flat: Record<string, string> = {};
        for (const [path, items] of Object.entries(grouped)) flat[path] = items[0]?.msg ?? "Invalid value.";
        setFieldErrors(flat);
        setGeneralError("Some fields need fixing before this can save.");
      } else {
        setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
      }
    } finally {
      setSaving(false);
    }
  }

  /** Downloads the currently-saved version as a PDF (routes/export.py).
   * Disabled until a version exists -- there is nothing on the server to
   * render yet (M1 brief: "disabled with reason when no saved version
   * exists"). Browser-side only: triggering a save-to-disk dialog from
   * here is Tauri's job, not this fetch-a-blob-and-click-an-anchor path. */
  async function handleExportPdf() {
    if (version == null) return;
    setExporting(true);
    setExportError(null);
    try {
      const blob = await downloadCharterPdf(projectId, version);
      const objectUrl = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = objectUrl;
      link.download = `charter-${projectId}-v${version}.pdf`;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      setExportError(err instanceof ApiError ? err.message : "Could not export PDF.");
    } finally {
      setExporting(false);
    }
  }

  return (
    <div data-testid="charter-form">
      <Panel
        title="Project Charter"
        right={
          <div style={{ display: "flex", alignItems: "center", gap: "var(--space-3)" }}>
            {version != null && <span data-testid="charter-version-badge">v{version} saved</span>}
            <Button
              variant="secondary"
              size="sm"
              disabled={version == null || exporting}
              title={version == null ? "Save the charter before exporting a PDF." : undefined}
              onClick={() => void handleExportPdf()}
              data-testid="charter-export-pdf"
            >
              {exporting ? "Exporting…" : "Export PDF"}
            </Button>
          </div>
        }
      >
        {version != null ? null : (
          <p style={{ fontSize: "var(--text-xs)", color: "var(--color-text-muted)" }}>Not saved yet.</p>
        )}
        {exportError && <VerdictBanner tone="fail" headline={exportError} />}
      </Panel>

      <ProblemStatementSection
        value={state.problem_statement}
        onChange={(v) => setState((s) => ({ ...s, problem_statement: v }))}
        whatFlag={fieldFlag("problem_statement.what")}
        magnitudeFlag={fieldFlag("problem_statement.magnitude")}
      />

      <GoalSection
        value={state.goal}
        onChange={(v) => setState((s) => ({ ...s, goal: v }))}
        statementFlag={fieldFlag("goal.statement")}
        consequentialFlag={fieldFlag("goal.consequential_metrics")}
      />

      <ScopeTeamSection
        scope={state.scope}
        onScopeChange={(v) => setState((s) => ({ ...s, scope: v }))}
        team={state.team}
        onTeamChange={(v) => setState((s) => ({ ...s, team: v }))}
        owner={state.process_owner}
        onOwnerChange={(v) => setState((s) => ({ ...s, process_owner: v }))}
        ownerFlag={fieldFlag("process_owner.name")}
      />

      <TimelineImpactSection
        timeline={state.timeline}
        onTimelineChange={(v) => setState((s) => ({ ...s, timeline: v }))}
        impact={state.business_impact}
        onImpactChange={(v) => setState((s) => ({ ...s, business_impact: v }))}
      />

      <RisksSection value={state.risks} onChange={(v) => setState((s) => ({ ...s, risks: v }))} flag={fieldFlag("risks")} />

      <Panel title="Notes">
        <Field label="Notes" htmlFor="charter-notes" helper="Optional free text.">
          <TextArea
            id="charter-notes"
            value={state.notes}
            onChange={(e) => setState((s) => ({ ...s, notes: e.target.value }))}
            rows={2}
          />
        </Field>

        {generalError && <VerdictBanner tone="fail" headline={generalError} />}

        <Button variant="primary" disabled={!canSave} onClick={() => void handleSave()} data-testid="charter-save">
          {saving ? "Saving…" : version != null ? "Save new version" : "Save"}
        </Button>

        <PrescoreStrip results={prescore} labels={CHARTER_CHECK_LABELS} />
      </Panel>
    </div>
  );
}
