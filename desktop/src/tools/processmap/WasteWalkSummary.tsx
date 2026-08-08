import { StatusPill } from "../../design/components";
import { WASTE_CATALOG, wasteTally } from "./processMapLogic";
import type { ProcessMapStep } from "../../api/types";

export interface WasteWalkSummaryProps {
  steps: ProcessMapStep[];
}

/** Counts per waste across the map (rubric R-MEA-02) -- a plain client-side
 * tally over already-loaded step data, the same kind of display reduction
 * PrescoreStrip does over server results; not a stamped "computed result"
 * (see processMapLogic.wasteTally's docstring). */
export function WasteWalkSummary({ steps }: WasteWalkSummaryProps) {
  const tally = wasteTally(steps);
  const total = Object.values(tally).reduce((a, b) => a + b, 0);
  return (
    <div className="sigma-processmap-waste-summary" data-testid="processmap-waste-summary">
      <span className="sigma-processmap-waste-summary__label">Waste walk: {total} observation{total === 1 ? "" : "s"}</span>
      <div className="sigma-processmap-waste-summary__pills">
        {WASTE_CATALOG.map(({ id, label }) => (
          <StatusPill key={id} tone={tally[id] > 0 ? "flag" : "neutral"} label={`${label}: ${tally[id]}`} dot={false} />
        ))}
      </div>
    </div>
  );
}
