import { Panel, StatusPill, VerdictBanner } from "../../design/components";
import type { GapResult } from "../../api/types";
import "./GapPanel.css";

export interface GapPanelProps {
  gap: GapResult;
}

/** The GAP BLOCK (task brief): recovered/remaining bars + the next-cause
 * card routing back to the Improve loop -- every number here is read
 * straight off GapResult, nothing recomputed client-side (rubric
 * R-IMP-04: a wrong number at the loop's decision point is an invalidator). */
export function GapPanel({ gap }: GapPanelProps) {
  const pct = Math.max(0, Math.min(100, gap.recovered_pct ?? 0));

  return (
    <Panel title="Remaining-gap check">
      <div className="sigma-proof-gap-bar" data-testid="proof-gap-recovered-bar">
        <div className="sigma-proof-gap-bar__fill" style={{ width: `${pct}%` }} />
      </div>
      <p>
        Original gap {gap.original_gap.toFixed(2)} — recovered{" "}
        <span data-testid="proof-gap-recovered">{gap.recovered.toFixed(2)}</span>
        {gap.recovered_pct != null && ` (${gap.recovered_pct.toFixed(1)}%)`} — remaining{" "}
        <span data-testid="proof-gap-remaining">{gap.remaining.toFixed(2)}</span>
      </p>

      <div data-testid="proof-loop-verdict">
        <VerdictBanner tone={gap.goal_met ? "pass" : "flag"} headline={gap.loop_verdict} />
      </div>

      {gap.next_cause_ref ? (
        <div data-testid="proof-next-cause-card">
          <StatusPill
            tone="flag" label={`Next: ${gap.next_cause_ref.cause_text}`}
            title={`via solution "${gap.next_cause_ref.via_solution_name}", rank #${gap.next_cause_ref.rank}`}
          />
        </div>
      ) : (
        <p data-testid="proof-no-next-cause">No further verified, not-yet-piloted cause available.</p>
      )}
    </Panel>
  );
}
