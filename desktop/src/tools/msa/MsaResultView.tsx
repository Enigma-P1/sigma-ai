import { Panel, StatusPill, VerdictBanner } from "../../design/components";
import { fmt, fmtPercent, toneForVerdict, verdictHeadline } from "./msaLogic";
import type { MsaResult } from "../../api/types";

export interface MsaResultViewProps {
  result: MsaResult;
}

/** Renders MsaResult faithfully -- no number here is computed client-side.
 * The band, the named denominator, the repeatability-only caveat, and the
 * EXIT-02 stop panel (with its "fix measurement, re-run" routing) all
 * render straight off the engine response, matching BaselineResultView's
 * "no number here is computed client-side" contract. */
export function MsaResultView({ result }: MsaResultViewProps) {
  return (
    <div className="sigma-msa-results" data-testid="msa-result-view">
      <VerdictBanner
        tone={toneForVerdict(result.verdict)}
        headline={verdictHeadline(result.verdict, result.data_type)}
        detail={result.caveat ?? undefined}
      />

      {result.resolution_check && (
        <Panel title="Resolution pre-check" collapsible defaultOpen={!result.resolution_check.passed}>
          <dl className="sigma-msa-dl">
            <div><dt>Gauge increment</dt><dd>{fmt(result.resolution_check.gauge_increment)}</dd></div>
            <div><dt>Span ({result.resolution_check.span_basis.replace("_", " ")})</dt><dd>{fmt(result.resolution_check.span)}</dd></div>
            <div><dt>Distinct values seen</dt><dd>{result.resolution_check.distinct_value_count}</dd></div>
          </dl>
          <StatusPill tone={result.resolution_check.passed ? "pass" : "fail"} label={result.resolution_check.passed ? "Passed" : "Failed"} />
          {!result.resolution_check.passed && (
            <ul className="sigma-msa-reasons">
              {result.resolution_check.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </Panel>
      )}

      {result.repeatability && (
        <Panel title="Repeatability%">
          <dl className="sigma-msa-dl">
            <div><dt>Repeatability %</dt><dd data-testid="msa-ev-percent">{fmtPercent(result.repeatability.value.ev_percent)}</dd></div>
            <div><dt>Denominator</dt><dd data-testid="msa-denominator">{result.repeatability.value.denominator === "tolerance" ? "Tolerance width (USL−LSL)" : "6 × study variation"}</dd></div>
            <div><dt>s_repeat</dt><dd>{fmt(result.repeatability.value.s_repeat)}</dd></div>
            <div><dt>Items used</dt><dd>{result.repeatability.value.items_used}</dd></div>
          </dl>
          {result.repeatability.value.items_excluded.length > 0 && (
            <ul className="sigma-msa-reasons" data-testid="msa-exclusions">
              {result.repeatability.value.exclusion_reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          )}
        </Panel>
      )}

      {result.attribute_agreement && (
        <Panel title="Two-rater attribute agreement">
          <dl className="sigma-msa-dl">
            <div><dt>% agreement</dt><dd data-testid="msa-percent-agreement">{fmtPercent(result.attribute_agreement.value.percent_agreement)}</dd></div>
            <div><dt>Cohen's kappa</dt><dd data-testid="msa-kappa">{fmt(result.attribute_agreement.value.kappa)}</dd></div>
            <div><dt>n items</dt><dd>{result.attribute_agreement.value.n}</dd></div>
          </dl>
          <p className="sigma-msa-note">% agreement alone can flatter a low-defect process by chance — kappa corrects for that. Both are reported, never one alone.</p>
        </Panel>
      )}

      {result.exit02 && (
        <div data-testid="msa-exit02-panel">
          <VerdictBanner
            tone="fail"
            headline="EXIT-02 — stop, fix your measurement first"
            detail={
              <>
                <p>{result.exit02.message}</p>
                <p><strong>Next step:</strong> {result.exit02.routes_to}</p>
              </>
            }
          />
        </div>
      )}
    </div>
  );
}
