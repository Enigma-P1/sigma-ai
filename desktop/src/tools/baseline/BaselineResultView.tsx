import { Panel, StatusPill, VerdictBanner } from "../../design/components";
import { ImrChart } from "./ImrChart";
import {
  EXIT04_CELL_TEXT,
  MEASUREMENT_CHECK_FAILED_DETAIL,
  MEASUREMENT_CHECK_FAILED_HEADLINE,
  PP_ONE_SIDED_CELL_TEXT,
  exitExplanation,
  fmt,
  normalityText,
  sigmaLevelText,
} from "./baselineLogic";
import type { BaselineResponse } from "../../api/types";
import "./BaselineForm.css";

export interface BaselineResultViewProps {
  result: BaselineResponse;
  values: number[];
  unitLabel?: string;
}

/** Renders BaselineResult faithfully: no number here is computed client-
 * side, every field is read straight off the engine response (M2 brief).
 * gate_ok=false renders only the honest gate message, matching
 * baseline.py's own "every other field is then None" contract. */
export function BaselineResultView({ result, values, unitLabel = "" }: BaselineResultViewProps) {
  if (!result.gate_ok) {
    return (
      <div data-testid="baseline-gate-message">
        <VerdictBanner tone="flag" headline={result.gate_message ?? "Baseline could not run."} />
      </div>
    );
  }

  const { stability, stable, stability_note, capability, normality, percentile_capability, observed_yield, sigma, exits, measurement_check } = result;

  return (
    <div className="sigma-baseline-results">
      {measurement_check === "failed" && (
        <div data-testid="baseline-measurement-check-banner">
          <VerdictBanner tone="fail" headline={MEASUREMENT_CHECK_FAILED_HEADLINE} detail={MEASUREMENT_CHECK_FAILED_DETAIL} />
        </div>
      )}

      {stability && stable != null && stability_note && (
        <div data-testid="baseline-stability-verdict">
          <ImrChart values={values} stability={stability} stable={stable} stabilityNote={stability_note} unitLabel={unitLabel} />
        </div>
      )}

      {capability && (
        <Panel title="Capability vs. performance">
          <dl className="sigma-baseline-dl">
            <div><dt>Cp (within)</dt><dd>{capability.value.cp_index != null ? fmt(capability.value.cp_index) : EXIT04_CELL_TEXT}</dd></div>
            <div><dt>Cpk (within)</dt><dd>{capability.value.cpk_index != null ? fmt(capability.value.cpk_index) : EXIT04_CELL_TEXT}</dd></div>
            <div><dt>Pp (overall)</dt><dd>{capability.value.pp_index != null ? fmt(capability.value.pp_index) : PP_ONE_SIDED_CELL_TEXT}</dd></div>
            <div><dt>Ppk (overall)</dt><dd>{fmt(capability.value.ppk_index)}</dd></div>
          </dl>
          <VerdictBanner
            tone={capability.value.performance_not_capability ? "flag" : "pass"}
            headline={
              capability.value.performance_not_capability
                ? "Pp/Ppk only — performance, not capability (process not stable)"
                : "Cp/Cpk and Pp/Ppk both reported — process is stable"
            }
          />
        </Panel>
      )}

      {normality && (
        <Panel title="Normality advisory">
          <p>{normalityText(normality.value)}</p>
        </Panel>
      )}

      {percentile_capability && (
        <Panel title="EXIT-05 supplement">
          <VerdictBanner
            tone="exit" headline={percentile_capability.value.label}
            detail={`n=${percentile_capability.value.n}, Ppk (percentile) ${fmt(percentile_capability.value.ppk_percentile)}`}
          />
        </Panel>
      )}
      {observed_yield && (
        <Panel title="EXIT-05 supplement (n < 100 fallback)">
          <VerdictBanner
            tone="exit" headline={`Observed yield ${(observed_yield.value.in_spec_fraction * 100).toFixed(1)}% in spec`}
            detail={`DPMO ${fmt(observed_yield.value.dpmo, 0)} · no normality or stability assumption`}
          />
        </Panel>
      )}

      {sigma && (
        <div data-testid="baseline-sigma-level">
          <VerdictBanner tone="neutral" headline={`Sigma level ${sigmaLevelText(sigma.value.sigma_level)} (${sigma.value.convention})`} detail={`DPMO ${fmt(sigma.value.dpmo, 0)}`} />
        </div>
      )}

      {exits.length > 0 && (
        <div className="sigma-baseline-exits">
          {exits.map((id) => (
            <StatusPill key={id} tone="exit" label={id} title={exitExplanation(id)} />
          ))}
        </div>
      )}

      {result.dataset_provenance && (
        <p className="sigma-baseline-provenance">
          Dataset {result.dataset_provenance.dataset_id.slice(0, 8)}…, column "{result.dataset_provenance.column}", SHA-256{" "}
          {result.dataset_provenance.dataset_sha256.slice(0, 16)}… ({result.dataset_provenance.row_count_used} rows used)
        </p>
      )}
    </div>
  );
}
