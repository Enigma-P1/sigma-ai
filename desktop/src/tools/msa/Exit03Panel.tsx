import { Panel, VerdictBanner } from "../../design/components";
import { EXIT03_EXAMPLES, EXIT03_ROUTES_TO } from "./msaLogic";

/** EXIT-03 self-service check (matrix §4 registry row): "is your question
 * beyond this narrow check?" -- named examples + the named route out, so
 * a user with a bigger measurement question doesn't mistake a passing
 * repeatability%/kappa read for an answer to it. Static content, mirrored
 * by hand from stats/msa.py's Exit03Payload defaults (same convention as
 * baseline/baselineLogic.ts's exitExplanation). */
export function Exit03Panel() {
  return (
    <Panel title="Is your question bigger than this check?" collapsible defaultOpen={false}>
      <p>
        This tool runs one narrow check: single-operator test/retest repeatability (continuous), or two-rater
        attribute agreement. If your real question is one of these, it's out of scope here — by design, not by
        accident:
      </p>
      <ul className="sigma-msa-reasons">
        {EXIT03_EXAMPLES.map((example) => (
          <li key={example}>{example}</li>
        ))}
      </ul>
      <VerdictBanner tone="exit" headline="EXIT-03 — route out" detail={EXIT03_ROUTES_TO} />
    </Panel>
  );
}
