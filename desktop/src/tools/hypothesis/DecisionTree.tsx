import { VerdictBanner } from "../../design/components";
import { whyThisTestSentence } from "./hypothesisLogic";
import { SwitchNotice } from "./SwitchNotice";
import type { HypRoutingDecision } from "../../api/types";
import "./HypothesisResults.css";

export interface DecisionTreeProps {
  routing: HypRoutingDecision;
}

/** The printed decision path (PLAN §4.2's "decision trees, visible"): real
 * nodes from the engine's own decision object, rendered as a vertical
 * flowchart -- each node is the question the rule asked, the answer read
 * off THIS question's own inputs, and the branch taken. The last node is
 * always the terminal step (a chosen route or a raised exit), styled to
 * stand out as the conclusion. */
export function DecisionTree({ routing }: DecisionTreeProps) {
  const why = whyThisTestSentence(routing);

  return (
    <div className="sigma-hyp-tree" data-testid="hyp-tree" data-node-count={routing.decision_path.length}>
      <ol className="sigma-hyp-tree__list">
        {routing.decision_path.map((node, i) => {
          const isLast = i === routing.decision_path.length - 1;
          return (
            <li key={i} className={`sigma-hyp-tree__node ${isLast ? "sigma-hyp-tree__node--terminal" : ""}`} data-testid={`hyp-tree-node-${i}`}>
              <div className="sigma-hyp-tree__q">{node.question}</div>
              <div className="sigma-hyp-tree__a">{node.answer}</div>
              <div className="sigma-hyp-tree__branch">→ {node.branch}</div>
            </li>
          );
        })}
      </ol>

      {why && (
        <VerdictBanner tone="neutral" className="sigma-hyp-tree__why" headline="Why this test?" detail={why} />
      )}

      {routing.recommend_nonparametric && <SwitchNotice routing={routing} />}
    </div>
  );
}
