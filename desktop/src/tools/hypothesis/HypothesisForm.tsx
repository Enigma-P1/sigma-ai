import { Button, Field, MissingHint, Panel, TextArea, VerdictBanner } from "../../design/components";
import { DataSourceFields } from "./DataSourceFields";
import { DecisionTree } from "./DecisionTree";
import { ExitPanel } from "./ExitPanel";
import { HYP_CHECK_LABELS } from "./hypothesisChecks";
import { PrescoreStrip } from "../PrescoreStrip";
import { QuestionIntakeFields } from "./QuestionIntakeFields";
import { ResultView } from "./ResultView";
import { useHypothesisForm } from "./useHypothesisForm";
import type { ProjectMetadata } from "../../api/types";
import "./HypothesisForm.css";

export interface HypothesisFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-17: the guided screen an untrained user asks a statistics question
 * through safely. Question first in plain words, then structured intake ->
 * Preview (the printed decision tree, /route) -> Run (/run, the canonical
 * saveable outcome, exit or result) -> a required reflection -> Save.
 * Nothing here computes a statistic client-side; every number comes
 * straight off the engine responses (build brief hard rule). */
export function HypothesisForm({ projectId, project, onSaved }: HypothesisFormProps) {
  const f = useHypothesisForm(projectId, project, onSaved);

  return (
    <Panel title="Hypothesis Testing" right={f.version != null && <span data-testid="hyp-version-badge">v{f.version} saved</span>}>
      <p>
        Say what you're asking first, in your own words. Then answer a few structured questions about your data --
        the engine picks the test by rule and shows the exact path it took, or names the reason it won't compute
        one rather than hand you a number it can't stand behind.
      </p>

      <QuestionIntakeFields state={f.state} patch={f.patch} />
      <DataSourceFields state={f.state} patch={f.patch} datasets={f.datasets} datasetDetails={f.datasetDetails} onNeedDatasetDetail={f.loadDatasetDetail} />

      <Button variant="primary" disabled={!f.canPreview} onClick={() => void f.handlePreview()} data-testid="hyp-preview">
        {f.previewing ? "Checking…" : "Preview decision tree"}
      </Button>
      {!f.previewing && <MissingHint fields={f.missingForPreview} />}
      {f.previewError && <VerdictBanner tone="fail" headline={f.previewError} />}

      {f.routing && (
        <>
          {f.routing.exit ? <ExitPanel exit={f.routing.exit} /> : <DecisionTree routing={f.routing} />}

          <Button variant="primary" disabled={!f.canRun} onClick={() => void f.handleRun()} data-testid="hyp-run">
            {f.running ? "Running…" : f.routing.exit ? "Record this outcome" : "Run"}
          </Button>
          {f.runError && <VerdictBanner tone="fail" headline={f.runError} />}
        </>
      )}

      {f.runResult && (
        <>
          {!f.runResult.refused && f.runResult.result && (
            <ResultView result={f.runResult.result} datasetProvenance={f.runResult.dataset_provenance} derivedNotes={f.derivedNotes} />
          )}

          <Field
            label="What does this mean for your project?" required htmlFor="hyp-reflection"
            helper="In your own words -- restating the headline above isn't a reflection. This is what R-ANA-05 grades."
          >
            <TextArea id="hyp-reflection" data-testid="hyp-reflection" rows={3} value={f.state.reflection} onChange={(e) => f.setReflection(e.target.value)} />
          </Field>

          <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="hyp-save">
            {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
          </Button>
          {!f.saving && <MissingHint fields={f.missingForReflection} />}
          {f.saveError && <VerdictBanner tone="fail" headline={f.saveError} />}
        </>
      )}

      <PrescoreStrip results={f.prescore} labels={HYP_CHECK_LABELS} />
    </Panel>
  );
}
