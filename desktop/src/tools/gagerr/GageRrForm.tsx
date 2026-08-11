import { Button, Field, MissingHint, Panel, SelectInput, TextInput, VerdictBanner } from "../../design/components";
import { ReportButton } from "../../app/ReportButton";
import { GageRrGrid } from "./GageRrGrid";
import { GageRrResultView } from "./GageRrResultView";
import { PrescoreStrip } from "../PrescoreStrip";
import { GAGE_RR_CHECK_LABELS } from "./gageRrChecks";
import {
  MAX_OPERATORS,
  MAX_PARTS,
  MAX_TRIALS,
  MIN_OPERATORS,
  MIN_PARTS,
  MIN_TRIALS,
  cellsTotal,
  emptyCellLabels,
  readingCount,
} from "./gageRrLogic";
import { useGageRrForm } from "./useGageRrForm";
import type { PoolChoice } from "./useGageRrForm";
import type { ProjectMetadata } from "../../api/types";
import "./GageRrForm.css";

export interface GageRrFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-35 Gage R&R: study designer, the parts x operators x trials entry
 * grid, and the engine's own decomposition rendered back — verdict,
 * components of variation, ANOVA. Nothing is computed client-side; every
 * number on this screen came from the engine (same contract as
 * MsaResultView and BaselineResultView). */
export function GageRrForm({ projectId, project, onSaved }: GageRrFormProps) {
  const f = useGageRrForm(projectId, project, onSaved);
  const entered = readingCount(f.grid);
  const total = cellsTotal(f.grid);
  const empties = emptyCellLabels(f.grid);
  const result = f.serverArtifact?.result ?? null;

  return (
    <Panel
      title="Gage R&R — full crossed study"
      right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="grr-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-35"
            captureKey="T-35-components"
            disabled={f.version == null}
            disabledReason="Run the study before downloading its report."
          />
        </span>
      }
    >
      <p>
        Every operator measures every part, several times each, and the engine splits what you saw into the
        parts and the measuring. This is the study T-12 routes out of — use T-12 when only one person measures.
      </p>

      <div className="sigma-grr-row">
        <Field label="Gauge / instrument" htmlFor="grr-gauge-name" helper="What did the measuring?">
          <TextInput
            id="grr-gauge-name" data-testid="grr-gauge-name" value={f.gaugeName}
            onChange={(e) => f.setGaugeName(e.target.value)} placeholder="e.g. digital calipers, 0.001 mm"
          />
        </Field>
        <Field
          label="Tolerance width (optional)" htmlFor="grr-tolerance"
          helper="USL minus LSL, as one number. Given, the gauge is judged against the spec; left blank, against this study's own variation."
        >
          <TextInput
            id="grr-tolerance" data-testid="grr-tolerance" type="number" value={f.toleranceText}
            onChange={(e) => f.updateTolerance(e.target.value)}
          />
        </Field>
        <Field
          label="Operator x part interaction" htmlFor="grr-pooling"
          helper="Convention is to pool the interaction into repeatability when it is not significant at 0.25."
        >
          <SelectInput
            id="grr-pooling" data-testid="grr-pooling" value={f.poolChoice}
            onChange={(e) => f.updatePoolChoice(e.target.value as PoolChoice)}
          >
            <option value="auto">Let the engine decide (recommended)</option>
            <option value="always">Always pool into repeatability</option>
            <option value="never">Never pool — keep the interaction term</option>
          </SelectInput>
        </Field>
      </div>

      <div className="sigma-grr-row sigma-grr-row--sizes">
        <Field label="Parts" htmlFor="grr-parts-count" helper={`10 is the convention (${MIN_PARTS}-${MAX_PARTS}).`}>
          <TextInput
            id="grr-parts-count" data-testid="grr-parts-count" type="number" min={MIN_PARTS} max={MAX_PARTS}
            value={String(f.grid.parts.length)} onChange={(e) => f.resize({ parts: Number(e.target.value) })}
          />
        </Field>
        <Field label="Operators" htmlFor="grr-operators-count" helper={`3 is the convention (${MIN_OPERATORS}-${MAX_OPERATORS}).`}>
          <TextInput
            id="grr-operators-count" data-testid="grr-operators-count" type="number" min={MIN_OPERATORS} max={MAX_OPERATORS}
            value={String(f.grid.operators.length)} onChange={(e) => f.resize({ operators: Number(e.target.value) })}
          />
        </Field>
        <Field label="Trials" htmlFor="grr-trials-count" helper={`Repeats per person per part (${MIN_TRIALS}-${MAX_TRIALS}).`}>
          <TextInput
            id="grr-trials-count" data-testid="grr-trials-count" type="number" min={MIN_TRIALS} max={MAX_TRIALS}
            value={String(f.grid.trials)} onChange={(e) => f.resize({ trials: Number(e.target.value) })}
          />
        </Field>
      </div>

      <Field
        label="Readings"
        helper="Arrow keys and Enter move between cells. Pasting a block from a spreadsheet fills right across parts and down through trials. Part and operator names are editable — click a heading."
      >
        <GageRrGrid grid={f.grid} onChange={f.updateGrid} />
      </Field>

      <p className="sigma-grr-progress" data-testid="grr-progress">
        {entered} of {total} readings entered.
        {empties.more + empties.labels.length > 0 && (
          <>
            {" "}
            Still empty: {empties.labels.join("; ")}
            {empties.more > 0 && ` and ${empties.more} more`}. A crossed study needs every cell — the engine will
            say so rather than guess, and a part-finished study still saves.
          </>
        )}
      </p>

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}
      {Object.entries(f.fieldErrors).map(([path, msg]) => (
        <VerdictBanner key={path} tone="fail" headline={`${path}: ${msg}`} />
      ))}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="grr-run">
        {f.saving ? "Running…" : f.version != null ? "Re-run study" : "Run study"}
      </Button>
      {!f.saving && <MissingHint fields={f.missing} />}

      {f.serverArtifact?.design_error && (
        <VerdictBanner
          tone="flag"
          headline="Saved, but not computed yet"
          detail={f.serverArtifact.design_error}
          data-testid="grr-design-error"
        />
      )}

      {result && <GageRrResultView result={result} />}

      <PrescoreStrip results={f.prescore} labels={GAGE_RR_CHECK_LABELS} />
    </Panel>
  );
}
