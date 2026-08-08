import { Button, Field, Panel, SelectInput, TextInput, VerdictBanner } from "../../design/components";
import { useSampleSizeForm } from "./useSampleSizeForm";
import type { CalculatorKind } from "./useSampleSizeForm";
import "./SampleSizePanel.css";

/** T-11's sample-size guidance panel (PLAN §4.1: "sample-size guidance as
 * a first-class output -- n-for-stable-baseline rules of thumb + a
 * calculator with plain-English framing, bias/convenience-sample
 * warnings"). The I-MR rule of thumb and bias warnings render as soon as
 * they're available; the margin-of-error calculator runs on demand. */
export function SampleSizePanel() {
  const f = useSampleSizeForm();

  return (
    <Panel title="Sample-size guidance">
      {f.result?.rule_of_thumb && (
        <div data-testid="samplesize-rule-of-thumb">
          <VerdictBanner
            tone="neutral"
            headline={`I-MR baseline rule of thumb: ${f.result.rule_of_thumb.minimum_n}-${f.result.rule_of_thumb.recommended_n} points`}
            detail={f.result.rule_of_thumb.rationale}
          />
        </div>
      )}

      <div className="sigma-samplesize-row">
        <Field label="What are you sizing?" htmlFor="samplesize-calculator">
          <SelectInput
            id="samplesize-calculator" data-testid="samplesize-calculator" value={f.calculator}
            onChange={(e) => f.setCalculator(e.target.value as CalculatorKind)}
          >
            <option value="mean">A mean (e.g. average cycle time)</option>
            <option value="proportion">A proportion (e.g. defect rate)</option>
          </SelectInput>
        </Field>
        <Field label="Confidence level" htmlFor="samplesize-confidence">
          <SelectInput
            id="samplesize-confidence" data-testid="samplesize-confidence" value={f.confidenceLevel}
            onChange={(e) => f.setConfidenceLevel(Number(e.target.value))}
          >
            <option value={0.9}>90%</option>
            <option value={0.95}>95%</option>
            <option value={0.99}>99%</option>
          </SelectInput>
        </Field>
      </div>

      <div className="sigma-samplesize-row">
        {f.calculator === "mean" ? (
          <Field
            label="Planning estimate of spread (SD)" required htmlFor="samplesize-sd"
            helper="From pilot data, history, or a stated guess -- your data's units."
          >
            <TextInput id="samplesize-sd" data-testid="samplesize-sd" type="number" value={f.planningSdText} onChange={(e) => f.setPlanningSdText(e.target.value)} />
          </Field>
        ) : (
          <Field label="Planning estimate (%)" required htmlFor="samplesize-p" helper="50% (the conservative default) if you have no prior estimate.">
            <TextInput id="samplesize-p" data-testid="samplesize-p" type="number" value={f.planningPPercentText} onChange={(e) => f.setPlanningPPercentText(e.target.value)} />
          </Field>
        )}
        <Field label={f.calculator === "mean" ? "Margin of error (± your units)" : "Margin of error (± %)"} required htmlFor="samplesize-margin">
          <TextInput id="samplesize-margin" data-testid="samplesize-margin" type="number" value={f.marginText} onChange={(e) => f.setMarginText(e.target.value)} />
        </Field>
      </div>

      <Button variant="primary" disabled={!f.canCalculate || f.loading} onClick={() => void f.handleCalculate()} data-testid="samplesize-calculate">
        {f.loading ? "Calculating…" : "Calculate"}
      </Button>

      {f.error && <VerdictBanner tone="fail" headline={f.error} />}

      {f.result?.calculator && (
        <div data-testid="samplesize-calculator-result">
          <VerdictBanner tone="pass" headline={`n = ${f.result.calculator.value.n}`} detail={f.result.calculator.value.plain_english} />
        </div>
      )}

      <div className="sigma-samplesize-bias">
        <p>Bias self-check — is this sample honestly representative?</p>
        <label className="sigma-samplesize-checkbox">
          <input type="checkbox" checked={f.isConvenienceSample} onChange={(e) => f.setIsConvenienceSample(e.target.checked)} /> This is a convenience sample
        </label>
        <label className="sigma-samplesize-checkbox">
          <input type="checkbox" checked={f.singleShiftOnly} onChange={(e) => f.setSingleShiftOnly(e.target.checked)} /> One shift only
        </label>
        <label className="sigma-samplesize-checkbox">
          <input type="checkbox" checked={f.singleOperatorOnly} onChange={(e) => f.setSingleOperatorOnly(e.target.checked)} /> One operator only
        </label>
        <label className="sigma-samplesize-checkbox">
          <input type="checkbox" checked={f.shortCollectionWindow} onChange={(e) => f.setShortCollectionWindow(e.target.checked)} /> Short collection window
        </label>
      </div>

      {f.result && f.result.warnings.length > 0 && (
        <div data-testid="samplesize-warnings">
          {f.result.warnings.map((w) => (
            <VerdictBanner key={w} tone="flag" headline={w} />
          ))}
        </div>
      )}
    </Panel>
  );
}
