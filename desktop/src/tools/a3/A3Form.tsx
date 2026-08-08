import { useState } from "react";
import { Button, MissingHint, Panel, TextInput, VerdictBanner } from "../../design/components";
import { PrescoreStrip } from "../PrescoreStrip";
import { A3_CHECK_LABELS } from "./a3Checks";
import { ClosurePanel } from "./ClosurePanel";
import { CompletenessRail } from "./CompletenessRail";
import { PanelEditor } from "./PanelEditor";
import { TollgateChecklistView } from "./TollgateChecklistView";
import { useA3Form } from "./useA3Form";
import type { A3PanelKind, ProjectMetadata } from "../../api/types";
import { A3_PANEL_ORDER, TOLLGATE_PHASES } from "../../api/types";
import "./A3Form.css";

export interface A3FormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-25 A3 Final Report + Tollgate Checklists: a guided narrative builder,
 * panel by panel -- each pre-seeded from its source artifact and
 * editable, plus tollgate checklists per phase and the closure block. */
export function A3Form({ projectId, project, onSaved }: A3FormProps) {
  const f = useA3Form(projectId, project, onSaved);
  const [activePanel, setActivePanel] = useState<A3PanelKind>("background");
  const panel = f.state.panels.find((p) => p.panel === activePanel)!;
  const serverPanel = f.serverArtifact?.panels.find((p) => p.panel === activePanel);

  return (
    <Panel title="A3 Final Report" right={f.version != null && <span data-testid="a3-version-badge">v{f.version} saved</span>}>
      <p>One argument, panel by panel -- problem, baseline, causes, countermeasures, proof, control. Not a field dump.</p>

      <div className="sigma-a3-layout">
        <CompletenessRail panels={f.state.panels} activePanel={activePanel} onSelect={(p) => setActivePanel(p as A3PanelKind)} />
        <div className="sigma-a3-main">
          <PanelEditor
            panel={panel} seeding={f.seeding === activePanel}
            onNarrativeChange={(narrative) => f.setPanelNarrative(activePanel, narrative)}
            onReseed={() => void f.reseedPanel(activePanel)}
          />

          {activePanel === "results" && (
            <Panel title="Realized benefits" subtitle="The COPQ re-run's own before/after money">
              <TextInput placeholder="COPQ re-run artifact id" data-testid="a3-rb-copq-ref" value={f.state.realizedBenefits.copq_rerun_artifact_id} onChange={(e) => f.update({ realizedBenefits: { ...f.state.realizedBenefits, copq_rerun_artifact_id: e.target.value } })} />
              <TextInput placeholder="window (e.g. 6 weeks post-rollout)" data-testid="a3-rb-window" value={f.state.realizedBenefits.window} onChange={(e) => f.update({ realizedBenefits: { ...f.state.realizedBenefits, window: e.target.value } })} />
              <TextInput type="number" placeholder="before amount" value={f.state.realizedBenefits.before_amount} onChange={(e) => f.update({ realizedBenefits: { ...f.state.realizedBenefits, before_amount: Number(e.target.value) } })} />
              <TextInput type="number" placeholder="after amount" value={f.state.realizedBenefits.after_amount} onChange={(e) => f.update({ realizedBenefits: { ...f.state.realizedBenefits, after_amount: Number(e.target.value) } })} />
              <TextInput type="number" placeholder="fix cost" value={f.state.realizedBenefits.fix_cost} onChange={(e) => f.update({ realizedBenefits: { ...f.state.realizedBenefits, fix_cost: Number(e.target.value) } })} />
              {f.serverArtifact?.realized_benefits?.result && (
                <div data-testid="a3-realized-to-date">Realized to date: {f.serverArtifact.realized_benefits.result.value.realized_to_date.toFixed(2)}, net of fix cost: {f.serverArtifact.realized_benefits.result.value.net_of_fix_cost.toFixed(2)}</div>
              )}
            </Panel>
          )}
          {serverPanel?.seeded_at && <p className="sigma-a3-seeded-at">seeded {serverPanel.seeded_at}</p>}
        </div>
      </div>

      <Panel title="Tollgate checklists" collapsible defaultOpen={false}>
        {TOLLGATE_PHASES.map((phase) => (
          <TollgateChecklistView
            key={phase} phase={phase} serverQuestions={f.serverArtifact?.tollgates.find((t) => t.phase === phase)?.questions ?? null}
            answers={f.state.tollgateAnswers[phase] ?? []} onAnswer={(a) => f.setTollgateAnswer(phase, a)}
          />
        ))}
      </Panel>

      <ClosurePanel closure={f.state.closure} onUpdate={(patch) => f.update({ closure: { ...f.state.closure, ...patch } })} onLoadFmea={() => void f.loadFmeaForClose()} />

      {f.closeBlockedError && <div data-testid="a3-close-blocked-error"><VerdictBanner tone="fail" headline={f.closeBlockedError} /></div>}
      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <div className="sigma-a3-save-row">
        <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="a3-save">
          {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
        </Button>
        {!f.saving && <MissingHint fields={f.missing} />}
      </div>

      <PrescoreStrip results={f.prescore} labels={A3_CHECK_LABELS} />
      <p className="sigma-a3-panel-list-hidden" data-testid="a3-panel-order">{A3_PANEL_ORDER.join(",")}</p>
    </Panel>
  );
}
