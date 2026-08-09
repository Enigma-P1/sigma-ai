import { Button, Field, Panel, SelectInput, StatusPill, TextInput, VerdictBanner } from "../../design/components";
import { BaselineResultView } from "./BaselineResultView";
import { useBaselineForm } from "./useBaselineForm";
import type { ProjectMetadata } from "../../api/types";
import "./BaselineForm.css";

export interface BaselineFormProps {
  projectId: string;
  project: ProjectMetadata;
  /** T-09's "send to baseline" deep link (ToolRouter's DatasetPreset) --
   * preselects the dataset (and its first numeric column) once it loads. */
  initialDatasetId?: string;
  /** Rail navigation to another tool (same callback the "I'm stuck"
   * button rides) -- the attribute-data notice uses it to hand off to
   * T-21/T-10. */
  onNavigateToTool?: (toolId: string) => void;
}

/** T-13: pick dataset + column, enter spec limits, confirm the
 * operational definition — in that visible order — then run. Renders
 * BaselineResult faithfully; nothing here is computed client-side.
 * Attribute (pass/fail) data has no path through this screen's I-MR +
 * capability math — the explicit toggle below routes it to the p-chart
 * (T-21, diagnostic) + DPMO/sigma (T-10) pairing instead of dead-ending. */
export function BaselineForm({ projectId, project, initialDatasetId, onNavigateToTool }: BaselineFormProps) {
  const f = useBaselineForm(projectId, project, initialDatasetId);

  return (
    <Panel title="Baseline: Stability then Capability">
      <p>
        Enforced order: pick your data, enter spec limits, confirm the operational definition — only then does the
        baseline run. Stability (I-MR) is assessed before capability, exactly as the engine requires.
      </p>

      <div className="sigma-baseline-section">
        <div className="sigma-baseline-section__title">1. Choose your data</div>
        <div className="sigma-baseline-row">
          <Field label="Dataset" htmlFor="baseline-dataset">
            <SelectInput
              id="baseline-dataset" data-testid="baseline-dataset-select" value={f.datasetId}
              onChange={(e) => { f.setDatasetId(e.target.value); f.setColumn(""); }}
            >
              <option value="">Select a dataset…</option>
              {f.datasets.map((d) => (
                <option key={d.dataset_id} value={d.dataset_id}>{d.source_filename} ({d.row_count} rows)</option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Column (numeric)" htmlFor="baseline-column">
            <SelectInput
              id="baseline-column" data-testid="baseline-column-select" value={f.column}
              disabled={!f.datasetId} onChange={(e) => f.setColumn(e.target.value)}
            >
              <option value="">Select a column…</option>
              {f.numericColumns.map((c) => (
                <option key={c.name} value={c.name}>{c.name}</option>
              ))}
            </SelectInput>
          </Field>
        </div>
        {f.datasetId && f.numericColumns.length === 0 && (
          <VerdictBanner tone="flag" headline="This dataset has no numeric columns — baseline needs one." />
        )}
        <label className="sigma-baseline-checkbox">
          <input
            type="checkbox" data-testid="baseline-attribute-toggle" checked={f.attributeData}
            onChange={(e) => f.setAttributeData(e.target.checked)}
          />
          My data is pass/fail counts (each unit either passes or fails — attribute data)
        </label>
        {f.attributeData && (
          <div data-testid="baseline-attribute-notice">
            <VerdictBanner
              tone="flag"
              headline="Attribute data baselines on the p-chart, not on this screen"
              detail={
                "This screen's stability-then-capability math (I-MR chart, Cp/Cpk) is for continuous " +
                "measurements. For pass/fail counts, the baseline lives in two tools: run a p-chart in Control " +
                "Charts (T-21) diagnostically — no freeze needed — to see the proportion and whether it is " +
                "stable, and use the Yield Calculator (T-10) for DPMO and sigma level. That pairing is the " +
                "traceability matrix's own attribute-capability path (§3a row 2.4.3)."
              }
              actions={
                onNavigateToTool ? (
                  <>
                    <Button
                      variant="secondary" size="sm" data-testid="baseline-attribute-open-t21"
                      onClick={() => onNavigateToTool("T-21")}
                    >
                      Open Control Charts (T-21)
                    </Button>{" "}
                    <Button
                      variant="secondary" size="sm" data-testid="baseline-attribute-open-t10"
                      onClick={() => onNavigateToTool("T-10")}
                    >
                      Open Yield Calculator (T-10)
                    </Button>
                  </>
                ) : undefined
              }
            />
          </div>
        )}
      </div>

      <div className={`sigma-baseline-section ${!f.dataReady ? "sigma-baseline-section--pending" : ""}`}>
        <div className="sigma-baseline-section__title">2. Spec limits (at least one, with a source)</div>
        <div className="sigma-baseline-row">
          <Field label="USL (upper spec limit)" htmlFor="baseline-usl">
            <TextInput id="baseline-usl" data-testid="baseline-usl-input" type="number" value={f.uslText} onChange={(e) => f.setUslText(e.target.value)} />
          </Field>
          <Field label="LSL (lower spec limit)" htmlFor="baseline-lsl">
            <TextInput id="baseline-lsl" data-testid="baseline-lsl-input" type="number" value={f.lslText} onChange={(e) => f.setLslText(e.target.value)} />
          </Field>
        </div>
      </div>

      <div className={`sigma-baseline-section ${!f.specsReady ? "sigma-baseline-section--pending" : ""}`}>
        <div className="sigma-baseline-section__title">3. Confirm the operational definition</div>
        <label className="sigma-baseline-checkbox">
          <input
            type="checkbox" data-testid="baseline-op-def-checkbox" checked={f.operationalDefinitionOk}
            onChange={(e) => f.setOperationalDefinitionOk(e.target.checked)}
          />
          Two different people measuring this the same way would get the same answer.
        </label>
        {f.collectionPlanEntry && (
          <div className="sigma-baseline-collection-plan-link" data-testid="baseline-collection-plan-chip">
            <StatusPill
              tone="accent" dot={false}
              label={`Linked: Data Collection Plan v${f.collectionPlanEntry.latest_version}`}
              title="From T-11 -- this project already has an operational definition on record there (display only)."
            />
          </div>
        )}
      </div>

      <details className="sigma-baseline-section">
        <summary className="sigma-baseline-section__title">Advanced (zone rules, sigma-shift convention)</summary>
        <label className="sigma-baseline-checkbox">
          <input type="checkbox" checked={f.enableRule2} onChange={(e) => f.setEnableRule2(e.target.checked)} />
          Rule 2 (2 of 3 beyond 2σ) — opt-in, raises the false-alarm rate
        </label>
        <label className="sigma-baseline-checkbox">
          <input type="checkbox" checked={f.enableRule3} onChange={(e) => f.setEnableRule3(e.target.checked)} />
          Rule 3 (4 of 5 beyond 1σ) — opt-in, raises the false-alarm rate
        </label>
        <label className="sigma-baseline-checkbox">
          <input type="checkbox" checked={f.applySigmaShift} onChange={(e) => f.setApplySigmaShift(e.target.checked)} />
          Apply the 1.5σ shift convention to the sigma level
        </label>
      </details>

      <Button variant="primary" disabled={!f.canRun} onClick={() => void f.handleRun()} data-testid="baseline-run">
        {f.running ? "Running…" : f.result ? "Re-run baseline" : "Run baseline"}
      </Button>

      {f.error && <VerdictBanner tone="fail" headline={f.error} />}

      {f.result && <BaselineResultView result={f.result} values={f.chartValues} />}
    </Panel>
  );
}
