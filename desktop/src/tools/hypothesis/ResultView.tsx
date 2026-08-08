import { Panel, VerdictBanner } from "../../design/components";
import { ContingencyResultTable } from "./ContingencyResultTable";
import { Exit13Panel } from "./Exit13Panel";
import { GroupsTable } from "./GroupsTable";
import { fmt, fmtCI, fmtPValue, ROUTE_LABELS } from "./hypothesisLogic";
import type { Computed, DatasetProvenance, HypothesisTestResult } from "../../api/types";
import "./HypothesisResults.css";

export interface ResultViewProps {
  result: Computed<HypothesisTestResult>;
  datasetProvenance?: DatasetProvenance[];
  derivedNotes?: string[];
}

/** Renders HypothesisTestResult faithfully -- every number here comes
 * straight off the engine response (build brief hard rule: no client-side
 * statistics). The plain_language block renders verbatim: comparison_summary
 * as the headline, the other three sentences (p-value meaning, effect size
 * in words, the practical-vs-statistical prompt) as the detail immediately
 * under it -- nothing paraphrased. */
export function ResultView({ result, datasetProvenance, derivedNotes }: ResultViewProps) {
  const v = result.value;
  const pl = v.plain_language;

  return (
    <div className="sigma-hyp-results" data-testid="hyp-result-view">
      <div data-testid="hyp-plain-language-headline">
        <VerdictBanner
          tone={v.significant ? "pass" : "neutral"}
          headline={pl.comparison_summary}
          detail={
            <>
              <p>{pl.p_value_meaning}</p>
              <p>{pl.effect_size_in_words}</p>
              <p><strong>{pl.practical_significance_prompt}</strong></p>
            </>
          }
        />
      </div>

      <Panel title={`${ROUTE_LABELS[v.test_name]} — the numbers`}>
        <dl className="sigma-hyp-dl">
          <div><dt>{v.statistic_name}</dt><dd>{fmt(v.statistic)}</dd></div>
          {v.df != null && <div><dt>df</dt><dd>{fmt(v.df, 1)}</dd></div>}
          {v.df_between != null && v.df_within != null && <div><dt>df (between, within)</dt><dd>{fmt(v.df_between, 0)}, {fmt(v.df_within, 0)}</dd></div>}
          <div><dt>p-value</dt><dd data-testid="hyp-p-value">{fmtPValue(v.p_value)} (α={v.alpha})</dd></div>
          <div><dt>{v.effect_size_name}</dt><dd>{fmt(v.effect_size_value)}</dd></div>
          <div><dt>95% CI</dt><dd>{fmtCI(v.effect_size_ci)}</dd></div>
          {v.hodges_lehmann_shift != null && (
            <div><dt>Hodges-Lehmann shift</dt><dd>{fmt(v.hodges_lehmann_shift)}, CI {fmtCI(v.hodges_lehmann_ci)}</dd></div>
          )}
        </dl>
        {v.equal_shape_caveat && <VerdictBanner tone="flag" headline="Equal-shape caveat" detail={v.equal_shape_caveat} />}
      </Panel>

      <GroupsTable groups={v.groups} />
      {v.contingency && v.contingency.length > 0 && <ContingencyResultTable cells={v.contingency} />}

      {v.assumptions_checked.length > 0 && (
        <Panel title="Assumptions checked" collapsible defaultOpen={false}>
          <ul className="sigma-hyp-list">{v.assumptions_checked.map((a) => <li key={a}>{a}</li>)}</ul>
        </Panel>
      )}
      {v.warnings.length > 0 && (
        <Panel title="Warnings">
          <ul className="sigma-hyp-list sigma-hyp-list--warn" data-testid="hyp-warnings">{v.warnings.map((w) => <li key={w}>{w}</li>)}</ul>
        </Panel>
      )}

      {v.exit13 && <Exit13Panel exit13={v.exit13} />}

      {(datasetProvenance?.length || derivedNotes?.length) ? (
        <div className="sigma-hyp-provenance">
          {datasetProvenance?.map((p, i) => (
            <p key={i}>Dataset {p.dataset_id.slice(0, 8)}…, column "{p.column}", SHA-256 {p.dataset_sha256.slice(0, 16)}… ({p.row_count_used} rows used)</p>
          ))}
          {derivedNotes?.map((n, i) => <p key={i}>{n}</p>)}
        </div>
      ) : null}
    </div>
  );
}
