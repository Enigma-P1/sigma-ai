import { Button, Field, MissingHint, Panel, VerdictBanner, YesNoToggle } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { PrescoreStrip } from "../PrescoreStrip";
import { DpmoBlockFields } from "./DpmoBlockFields";
import { YieldStepFields } from "./YieldStepFields";
import { YIELD_CALC_CHECK_LABELS } from "./yieldCalcChecks";
import { emptyYieldStep, fmt, percent, sectionFlag, sigmaLevelText, yieldCalcMissingFields } from "./yieldCalcLogic";
import { useYieldCalcForm } from "./useYieldCalcForm";
import type { ProjectMetadata } from "../../api/types";
import "./YieldCalcForm.css";
import { ReportButton } from "../../app/ReportButton";

export interface YieldCalcFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

const STEPS_CHECK_IDS = ["rty_only_claimed_in_series", "rty_matches_recomputed"];
const DPMO_CHECK_IDS = ["dpmo_result_matches_recomputed", "opportunity_inflation_justified"];

/** T-10 Yield Calculator: an ordered process-steps table (direct-ratio FPY
 * per step, RTY rollup -- only under the explicit steps_in_series claim)
 * plus an independent, optional DPMO/sigma-level block. Every computed
 * number (defective units/FPY per step, RTY, DPMO, sigma level) always
 * renders from the engine's own response, never a client-side number
 * presented as authoritative -- CopqForm's exact contract, extended to two
 * blocks. */
export function YieldCalcForm({ projectId, project, onSaved }: YieldCalcFormProps) {
  const f = useYieldCalcForm(projectId, project, onSaved);

  function stepError(i: number, field: string): string | undefined {
    return f.fieldErrors[`steps.${i}.${field}`];
  }
  function dpmoError(field: string): string | undefined {
    return f.fieldErrors[`dpmo_block.${field}`];
  }

  const rty = f.serverArtifact?.rty_result;
  const dpmo = f.serverArtifact?.dpmo_result;

  return (
    <Panel title="Yield Calculator (FPY/RTY + DPMO)" right={
        <span style={{ display: "inline-flex", alignItems: "center", gap: "var(--space-3)" }}>
          {f.version != null && <span data-testid="yieldcalc-version-badge">v{f.version} saved</span>}
          <ReportButton
            projectId={projectId}
            projectName={project.name}
            toolId="T-10"
            disabled={f.version == null}
            disabledReason="Save this tool before downloading its report."
          />
        </span>
      }>
      <Field label="Process steps" flag={sectionFlag(f.prescore, STEPS_CHECK_IDS)}>
        <DynamicList
          items={f.steps}
          onChange={f.updateSteps}
          makeEmpty={emptyYieldStep}
          minItems={1}
          addLabel="+ Add process step"
          renderRow={(step, i, update) => (
            <YieldStepFields
              index={i}
              step={step}
              serverStep={f.serverArtifact?.steps[i]}
              onChange={(patch) => update({ ...step, ...patch })}
              errors={{
                name: stepError(i, "name"),
                units_in: stepError(i, "units_in"),
                first_pass_correct: stepError(i, "first_pass_correct"),
              }}
            />
          )}
        />
      </Field>

      <Field
        label="Are these steps in series?"
        helper="RTY (rolled throughput yield) is only computed when the steps run one after another as a serial line. If they don't, mark No -- the steps table still records each step's own FPY, RTY just won't be claimed."
      >
        <YesNoToggle name="yieldcalc-series" value={f.stepsInSeries} onChange={f.setSeries} />
      </Field>

      <div data-testid="yieldcalc-rty">
        {f.stepsInSeries === false ? (
          <VerdictBanner tone="neutral" headline="RTY not computed -- steps are not declared in series" />
        ) : rty ? (
          <VerdictBanner
            tone="pass"
            headline={`RTY: ${percent(rty.value, 2)}`}
            detail={<span title="R-MEA-09">Rolled throughput yield -- the product of every step's own FPY, computed by the engine.</span>}
          />
        ) : (
          <VerdictBanner tone="neutral" headline="RTY not yet computed -- save to get the engine's number" />
        )}
      </div>

      <Field label="Include a DPMO / sigma-level calculation?" helper="Independent of the steps table above -- a separate defect-count DPMO block.">
        <YesNoToggle name="yieldcalc-include-dpmo" value={f.includeDpmo} onChange={f.toggleIncludeDpmo} />
      </Field>

      {f.includeDpmo && (
        <Field label="DPMO block" flag={sectionFlag(f.prescore, DPMO_CHECK_IDS)}>
          <DpmoBlockFields
            block={f.dpmoBlock}
            onChange={f.updateDpmoBlock}
            errors={{
              defects: dpmoError("defects"),
              units: dpmoError("units"),
              opportunities_per_unit: dpmoError("opportunities_per_unit"),
              opportunity_justification: dpmoError("opportunity_justification"),
            }}
          />
        </Field>
      )}

      {f.includeDpmo && (
        <div data-testid="yieldcalc-dpmo-sigma">
          {dpmo ? (
            <VerdictBanner
              tone="neutral"
              headline={`Sigma level ${sigmaLevelText(dpmo.value.sigma_level)} (${dpmo.value.convention})`}
              detail={`DPMO ${fmt(dpmo.value.dpmo, 0)}`}
            />
          ) : (
            <VerdictBanner tone="neutral" headline="DPMO / sigma level not yet computed -- save to get the engine's numbers" />
          )}
        </div>
      )}

      {f.serverArtifact && (
        <p className="sigma-yieldcalc-provenance">
          {rty && <>RTY method: {rty.provenance.method}. </>}
          {dpmo && <>DPMO/sigma method: {dpmo.provenance.method}.</>}
        </p>
      )}

      {f.generalError && <VerdictBanner tone="fail" headline={f.generalError} />}

      <Button variant="primary" disabled={!f.canSave} onClick={() => void f.handleSave()} data-testid="yieldcalc-save">
        {f.saving ? "Saving…" : f.version != null ? "Save new version" : "Save"}
      </Button>
      {!f.saving && <MissingHint fields={yieldCalcMissingFields(f.steps, f.stepsInSeries, f.includeDpmo, f.dpmoBlock)} />}

      <PrescoreStrip results={f.prescore} labels={YIELD_CALC_CHECK_LABELS} />
    </Panel>
  );
}
