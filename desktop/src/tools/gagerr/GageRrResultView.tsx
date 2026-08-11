import { Panel, VerdictBanner } from "../../design/components";
import { GageRrComponentsChart } from "./GageRrComponentsChart";
import { fmt, fmtPercent } from "./gageRrLogic";
import type { GageRRResult } from "../../api/types";
import { GRR_NDC_MINIMUM } from "../../api/types";
import type { VerdictTone } from "../../design/components";

export interface GageRrResultViewProps {
  result: GageRRResult;
}

const TONE: Record<string, VerdictTone> = { acceptable: "pass", marginal: "flag", unacceptable: "fail" };

/** Rows of the components table, in the order a reader works down them:
 * the two halves of measurement error, their total, then what the study
 * was trying to see. Mirrors the report's own COMPONENT_ORDER
 * (export/reports/gage_rr.py) so screen and PDF read identically. */
const COMPONENT_ROWS: [string, string][] = [
  ["repeatability", "Repeatability (equipment)"],
  ["reproducibility", "Reproducibility (operators)"],
  ["operator", "— operator"],
  ["operator_x_part", "— operator × part"],
  ["gage_rr", "Total Gage R&R"],
  ["part_to_part", "Part-to-part"],
  ["total_variation", "Total variation"],
];

const ANOVA_LABELS: Record<string, string> = {
  part: "Part",
  operator: "Operator",
  operator_x_part: "Operator × part",
  repeatability: "Repeatability (error)",
  total: "Total",
};

/** T-35's on-screen result: the same verdict, the same tables, and the
 * same chart the PDF prints. Nothing here is computed client-side — every
 * number is the engine's, rendered (same contract as MsaResultView). */
export function GageRrResultView({ result }: GageRrResultViewProps) {
  const basisWords = result.basis === "tolerance" ? "of tolerance" : "of study variation";
  const headline = result.basis === "tolerance" ? result.grr_percent_tolerance ?? 0 : result.grr_percent_study_variation;
  const hasTolerance = result.grr_percent_tolerance != null;

  return (
    <div className="sigma-grr-results" data-testid="grr-result">
      <VerdictBanner
        tone={TONE[result.verdict] ?? "neutral"}
        headline={`Gage R&R is ${headline.toFixed(1)}% ${basisWords} — ${result.verdict}`}
        detail={`${result.parts} parts × ${result.operators} operators × ${result.replicates} repeats · ${result.number_of_distinct_categories} distinct categories · ${result.interaction_pooled ? "interaction pooled into repeatability" : "interaction retained in the model"}`}
      />

      <dl className="sigma-grr-dl">
        <div>
          <dt>%GRR of study variation</dt>
          <dd data-testid="grr-percent-sv">{fmtPercent(result.grr_percent_study_variation)}</dd>
        </div>
        {hasTolerance && (
          <div>
            <dt>%GRR of tolerance</dt>
            <dd data-testid="grr-percent-tol">{fmtPercent(result.grr_percent_tolerance)}</dd>
          </div>
        )}
        <div>
          <dt>Distinct categories</dt>
          <dd data-testid="grr-ndc">
            {result.number_of_distinct_categories}
            {result.number_of_distinct_categories < GRR_NDC_MINIMUM && ` (below ${GRR_NDC_MINIMUM})`}
          </dd>
        </div>
      </dl>

      <GageRrComponentsChart result={result} testId="grr-components-chart" />

      <Panel title="Variance components">
        <div className="sigma-grr-grid-scroll">
          <table className="sigma-grr-table" data-testid="grr-components-table">
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">Variance</th>
                <th scope="col">Std dev</th>
                <th scope="col">% study var</th>
                {hasTolerance && <th scope="col">% tolerance</th>}
              </tr>
            </thead>
            <tbody>
              {COMPONENT_ROWS.map(([name, label]) => {
                const component = result.components.find((c) => c.name === name);
                if (!component) return null;
                return (
                  <tr key={name} data-testid={`grr-component-${name}`}>
                    <th scope="row">
                      {label}
                      {component.clamped_from_negative && (
                        <span className="sigma-grr-note" title="The raw estimator came out negative and was floored at zero — this component is smaller than the study can resolve, not absent.">
                          {" "}
                          (clamped)
                        </span>
                      )}
                    </th>
                    <td>{fmt(component.variance)}</td>
                    <td>{fmt(component.std_dev)}</td>
                    <td>{fmtPercent(component.percent_study_variation)}</td>
                    {hasTolerance && <td>{fmtPercent(component.percent_tolerance)}</td>}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="sigma-grr-note">
          Percentages are computed on standard deviations, not variances, which is why the columns do not add up
          to 100.
        </p>
      </Panel>

      <Panel title="ANOVA" collapsible defaultOpen={false}>
        <div className="sigma-grr-grid-scroll">
          <table className="sigma-grr-table" data-testid="grr-anova-table">
            <thead>
              <tr>
                <th scope="col">Source</th>
                <th scope="col">DF</th>
                <th scope="col">SS</th>
                <th scope="col">MS</th>
                <th scope="col">F</th>
                <th scope="col">p</th>
              </tr>
            </thead>
            <tbody>
              {result.anova.map((row) => (
                <tr key={row.source}>
                  <th scope="row">{ANOVA_LABELS[row.source] ?? row.source}</th>
                  <td>{row.df}</td>
                  <td>{fmt(row.ss)}</td>
                  <td>{fmt(row.ms)}</td>
                  <td>{fmt(row.f_statistic)}</td>
                  <td>{row.p_value == null ? "—" : row.p_value.toPrecision(4)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p className="sigma-grr-note">
          The operator × part row is what decides pooling: not significant at α = 0.25 and it is folded into
          repeatability, which is the model {result.interaction_pooled ? "used here" : "this study did not use"}.
        </p>
      </Panel>

      {result.warnings.length > 0 && (
        <ul className="sigma-grr-warnings" data-testid="grr-warnings">
          {result.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
    </div>
  );
}
