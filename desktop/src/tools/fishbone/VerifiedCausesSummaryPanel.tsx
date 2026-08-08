import { Panel, VerdictBanner } from "../../design/components";
import type { Computed, VerifiedCausesSummary } from "../../api/types";
import { BRANCH_LABELS, EVIDENCE_KIND_LABELS } from "./fishboneLogic";

export interface VerifiedCausesSummaryPanelProps {
  summary?: Computed<VerifiedCausesSummary> | null;
  saved: boolean;
}

/** The R-ANA-06 feed, rendered straight from the engine's own computed
 * summary -- never re-derived client-side (DemandPanel.tsx's "only trust
 * the server-echoed Computed<T>" convention). This is the list the
 * Improve phase's ranked fix list draws from. */
export function VerifiedCausesSummaryPanel({ summary, saved }: VerifiedCausesSummaryPanelProps) {
  return (
    <Panel title="Verified causes -- the Improve feed" subtitle="What Improve will rank and build on next">
      <div data-testid="fishbone-verified-summary">
        {summary ? (
          summary.value.count > 0 ? (
            <ul className="sigma-fishbone-verified-list">
              {summary.value.causes.map((c) => (
                <li key={c.cause_id} data-testid={`fishbone-verified-${c.cause_id}`}>
                  <span className="sigma-fishbone-verified-branch">{BRANCH_LABELS[c.branch]}</span>
                  <span>{c.text}</span>
                  <span className="sigma-fishbone-verified-evidence">
                    {EVIDENCE_KIND_LABELS[c.evidence.kind]}: {c.evidence.ref}
                  </span>
                </li>
              ))}
            </ul>
          ) : (
            <VerdictBanner tone="neutral" headline="No verified causes yet" detail="Attach evidence and mark a cause verified once the data ties it to the baseline gap." />
          )
        ) : (
          <VerdictBanner tone="neutral" headline={saved ? "Save again to refresh this summary." : "Save to see the engine's verified-causes summary."} />
        )}
      </div>
    </Panel>
  );
}
