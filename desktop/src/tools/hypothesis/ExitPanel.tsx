import { VerdictBanner } from "../../design/components";
import { HYP_EXIT_TITLES } from "./hypothesisLogic";
import type { HypExitPayload } from "../../api/types";
import "./HypothesisResults.css";

export interface ExitPanelProps {
  exit: HypExitPayload;
}

/** An honest refusal panel -- the exit name in plain words, why the
 * standard result would mislead, and the route out, all inside one banner
 * (the EXIT-04 pattern: next action inside the banner, not a separate
 * dead-end message). No statistic, p-value, or effect size is rendered
 * here, ever -- a raised exit means the engine never computed one. */
export function ExitPanel({ exit }: ExitPanelProps) {
  return (
    <div data-testid="hyp-exit-panel">
      <VerdictBanner
        tone="fail"
        headline={`${exit.exit_id} — ${HYP_EXIT_TITLES[exit.exit_id]}`}
        detail={
          <>
            <p>{exit.message}</p>
            <p><strong>What to do next:</strong> {exit.routes_to}</p>
            <p className="sigma-hyp-exit-detail">{exit.detail}</p>
          </>
        }
      />
    </div>
  );
}
