import { Panel, StatusPill, VerdictBanner } from "../../design/components";
import type { Computed, RankedFixList } from "../../api/types";
import { QUADRANT_LABELS } from "./solutionMatrixLogic";

export interface RankedFixListPanelProps {
  rankedFixList?: Computed<RankedFixList> | null;
  saved: boolean;
}

/** The RANKED FIX LIST panel, rendering the engine's computed ranking
 * verbatim (PLAN §4.1: "output is a ranked fix list -- the queue the
 * improvement loop works through") -- never re-derived client-side
 * (VerifiedCausesSummaryPanel's "only trust the server-echoed Computed<T>"
 * convention). Unlinked solutions render in their own flagged section. */
export function RankedFixListPanel({ rankedFixList, saved }: RankedFixListPanelProps) {
  return (
    <Panel title="Ranked fix list" subtitle="What the Improve loop works through next">
      <div data-testid="solmatrix-ranked-list">
        {!rankedFixList ? (
          <VerdictBanner tone="neutral" headline={saved ? "Save again to refresh the ranking." : "Save to see the engine's ranked fix list."} />
        ) : rankedFixList.value.ranked.length === 0 ? (
          <VerdictBanner tone="neutral" headline="Nothing ranked yet" detail="Link a solution to a verified cause to put it in the queue." />
        ) : (
          <ol className="sigma-solmatrix-ranked">
            {rankedFixList.value.ranked.map((r) => (
              <li key={r.solution_id} data-testid={`solmatrix-ranked-${r.solution_id}`}>
                <span className="sigma-solmatrix-rank-number">#{r.rank}</span>
                <span className="sigma-solmatrix-rank-name">{r.name}</span>
                <StatusPill tone="accent" label={QUADRANT_LABELS[r.quadrant]} dot={false} />
                <span className="sigma-solmatrix-rank-detail">
                  {r.weighted_total != null ? `weighted total: ${r.weighted_total}` : `impact ${r.impact} / effort ${r.effort}`}
                </span>
              </li>
            ))}
          </ol>
        )}
      </div>

      {rankedFixList && rankedFixList.value.unlinked.length > 0 && (
        <div data-testid="solmatrix-unlinked-list">
          <VerdictBanner
            tone="flag"
            headline={`${rankedFixList.value.unlinked.length} solution(s) not yet linked to a cause`}
            detail={
              <ul>
                {rankedFixList.value.unlinked.map((u) => (
                  <li key={u.solution_id} data-testid={`solmatrix-unlinked-${u.solution_id}`}>
                    {u.name} -- {u.reason}
                  </li>
                ))}
              </ul>
            }
          />
        </div>
      )}
    </Panel>
  );
}
