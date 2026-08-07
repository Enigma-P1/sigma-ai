import type { ReactNode } from "react";
import "./VerdictBanner.css";

export type VerdictTone = "pass" | "flag" | "fail" | "exit" | "neutral";

const GLYPH: Record<VerdictTone, string> = {
  pass: "✓",
  flag: "!",
  fail: "✕",
  exit: "→",
  neutral: "·",
};

export interface VerdictBannerProps {
  /** The one-line plain-English verdict (research §F: "stable but not
   * capable: Cpk 0.87 vs target 1.33" is the pattern this renders). */
  headline: string;
  detail?: ReactNode;
  tone: VerdictTone;
  actions?: ReactNode;
  className?: string;
}

/** The plain-English verdict headline pattern (PLAN §4.5 / research §F),
 * reused for prescore summaries, gate status, and (later) chart verdicts. */
export function VerdictBanner({ headline, detail, tone, actions, className }: VerdictBannerProps) {
  return (
    <div className={["sigma-verdict", `sigma-verdict--${tone}`, className ?? ""].filter(Boolean).join(" ")} role="status">
      <span className="sigma-verdict__icon" aria-hidden="true">
        <span className="sigma-verdict__icon-glyph">{GLYPH[tone]}</span>
      </span>
      <div className="sigma-verdict__body">
        <div className="sigma-verdict__headline">{headline}</div>
        {detail && <div className="sigma-verdict__detail">{detail}</div>}
        {actions && <div className="sigma-verdict__actions">{actions}</div>}
      </div>
    </div>
  );
}
