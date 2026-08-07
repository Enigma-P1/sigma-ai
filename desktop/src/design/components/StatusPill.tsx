import "./StatusPill.css";

/** The full palette of pill tones in the design system. Every domain status
 * (tool status, prescore status, gate status) maps down to one of these —
 * see src/app/statusTone.ts for the mapping tables, kept out of this file
 * so StatusPill itself stays a dumb, reusable primitive. */
export type PillTone = "pass" | "flag" | "fail" | "exit" | "accent" | "neutral";

export interface StatusPillProps {
  label: string;
  tone: PillTone;
  /** Show a small solid dot before the label. Default true. */
  dot?: boolean;
  title?: string;
}

export function StatusPill({ label, tone, dot = true, title }: StatusPillProps) {
  return (
    <span className={`sigma-pill sigma-pill--${tone}`} title={title}>
      {dot && <span className="sigma-pill__dot" aria-hidden="true" />}
      {label}
    </span>
  );
}
