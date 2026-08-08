import { VerdictBanner } from "../../design/components";
import { ROUTE_LABELS } from "./hypothesisLogic";
import type { HypRoutingDecision } from "../../api/types";

export interface SwitchNoticeProps {
  routing: HypRoutingDecision;
}

/** The nonparametric switch, shown as a confirmable choice (build brief):
 * default = the engine's own recommendation (switch_reason names exactly
 * why, never a silent normality pretest -- hypothesis_selector.py's module
 * docstring). There is no separate "override" input in the engine's
 * contract -- the route is a pure function of the declared inputs, so the
 * only honest way to get a different route is to change one of the inputs
 * that actually drives this decision (the shape-concern flag or the
 * declared data type, both above) and preview again -- never a client-side
 * toggle that pretends to change what already ran. */
export function SwitchNotice({ routing }: SwitchNoticeProps) {
  if (!routing.route) return null;
  return (
    <VerdictBanner
      tone="flag"
      className="sigma-hyp-switch-notice"
      headline={`Using the recommended rank-based route: ${ROUTE_LABELS[routing.route]}`}
      detail={
        <>
          <p data-testid="hyp-switch-reason">{routing.switch_reason}</p>
          <p>
            This is the default -- Run will use this route as shown. To use the standard (parametric) test instead,
            clear the &ldquo;my data looks skewed or has outliers&rdquo; box above (and check whether your data is really
            ordinal), then preview the tree again. The engine never swaps tests silently, so a different route only
            ever comes from a different declared input, not a button here.
          </p>
        </>
      }
    />
  );
}
