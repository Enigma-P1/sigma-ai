import { StatusPill, VerdictBanner } from "../design/components";
import type { VerdictTone } from "../design/components";
import { toneForPrescoreStatus } from "../app/statusTone";
import type { PrescoreResult } from "../api/types";
import "./PrescoreStrip.css";

export interface PrescoreStripProps {
  results: PrescoreResult[];
  /** check_id -> plain-English label (M1 brief: "a prescore results strip
   * mapping check ids to plain-English labels"). Falls back to the raw
   * check_id for anything not in the map, so nothing silently disappears. */
  labels: Record<string, string>;
}

function summarize(results: PrescoreResult[]): { headline: string; tone: VerdictTone } {
  const hardFlags = results.filter((r) => r.status === "hard_flag").length;
  const flags = results.filter((r) => r.status === "flag").length;
  if (hardFlags > 0) {
    return { headline: `${hardFlags} check${hardFlags === 1 ? "" : "s"} need real attention`, tone: "fail" };
  }
  if (flags > 0) {
    return { headline: `${flags} check${flags === 1 ? "" : "s"} worth a second look`, tone: "flag" };
  }
  return { headline: "All checks passed", tone: "pass" };
}

/** The prescore results strip: the plain-English verdict headline plus one
 * pill per check, each labeled in plain English and titled with the
 * engine's own detail string (M1 brief). */
export function PrescoreStrip({ results, labels }: PrescoreStripProps) {
  if (results.length === 0) return null;
  const { headline, tone } = summarize(results);

  return (
    <div className="sigma-prescore" data-testid="prescore-strip">
      <VerdictBanner tone={tone} headline={headline} />
      <ul className="sigma-prescore__list">
        {results.map((r) => (
          <li key={r.check_id} data-testid={`prescore-check-${r.check_id}`} data-status={r.status}>
            <StatusPill tone={toneForPrescoreStatus(r.status)} label={labels[r.check_id] ?? r.check_id} title={r.detail} />
          </li>
        ))}
      </ul>
    </div>
  );
}
