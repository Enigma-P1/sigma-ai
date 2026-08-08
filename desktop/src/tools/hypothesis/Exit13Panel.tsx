import { Panel, VerdictBanner } from "../../design/components";
import { GroupsTable } from "./GroupsTable";
import type { HypExit13Payload } from "../../api/types";
import "./HypothesisResults.css";

export interface Exit13PanelProps {
  exit13: HypExit13Payload;
}

/** matrix §4 EXIT-13: ANOVA came back significant -- the canned honest
 * next step (guided pairwise comparisons ship in v1.1) plus the interim
 * read, exactly as the engine returns them: group means/medians and a
 * descriptive largest-vs-smallest, no pairwise p-value anywhere. */
export function Exit13Panel({ exit13 }: Exit13PanelProps) {
  return (
    <div data-testid="hyp-exit13-panel">
      <Panel title="EXIT-13 — which groups differ?">
        <VerdictBanner tone="exit" headline="These groups differ overall" detail={exit13.message} />
        <p className="sigma-hyp-exit13-largest-smallest" data-testid="hyp-exit13-largest-smallest">{exit13.largest_vs_smallest}</p>
        <GroupsTable groups={exit13.interim_read} testId="hyp-exit13-interim-read" />
        <p className="sigma-hyp-exit13-routes-to"><strong>Next:</strong> {exit13.routes_to}</p>
      </Panel>
    </div>
  );
}
