import { Panel, VerdictBanner } from "../../design/components";
import type { Computed, ValueAddRatioResult } from "../../api/types";

export interface ValueAddPanelProps {
  valueAddRatio?: Computed<ValueAddRatioResult> | null;
  saved: boolean;
}

function minutes(value: number): string {
  return `${Number.isInteger(value) ? value : value.toFixed(2)} min`;
}

/** The timeline readout a value-stream map exists to produce.
 *
 * T-06 has always tagged steps value-add / non-value-add / enabling and
 * timed them; it never summed them, so the one number that makes people
 * change their mind — how little of the lead time is actually work — was
 * absent. "2.6 minutes of work inside 8.4 minutes of elapsed time" lands
 * differently from either figure on its own.
 *
 * Three bars rather than two: enabling work is neither waste nor value-add,
 * and folding it either way misleads. Shown as a proportion of the same
 * total so the split reads at a glance. */
export function ValueAddPanel({ valueAddRatio, saved }: ValueAddPanelProps) {
  if (!saved || !valueAddRatio) {
    return (
      <Panel title="Value-add ratio">
        <p style={{ fontSize: "var(--text-sm)", color: "var(--color-text-muted)" }}>
          Time each step and save — this shows how much of the total elapsed time is actually work.
        </p>
      </Panel>
    );
  }

  const r = valueAddRatio.value;
  const pct = (r.value_add_ratio * 100).toFixed(1);
  const share = (value: number) =>
    r.total_lead_time_minutes > 0 ? `${(value / r.total_lead_time_minutes) * 100}%` : "0%";

  const tone = r.value_add_ratio < 0.05 ? "flag" : "pass";

  return (
    <Panel title="Value-add ratio">
      <VerdictBanner
        tone={tone}
        headline={`${pct}% of the elapsed time is value-add — ${minutes(r.value_add_minutes)} of work inside ${minutes(
          r.total_lead_time_minutes,
        )}.`}
        detail={
          <>
            The rest is waiting, handling, and required-but-not-valuable work. A low number is normal and
            is where the opportunity usually is — attack the waiting before speeding up the working.
          </>
        }
      />

      <div
        aria-hidden
        style={{
          display: "flex",
          height: "1.5rem",
          borderRadius: "var(--radius-sm)",
          overflow: "hidden",
          border: "1px solid var(--color-border)",
          margin: "var(--space-3) 0",
        }}
      >
        <div style={{ width: share(r.value_add_minutes), background: "var(--color-pass)" }} />
        <div style={{ width: share(r.enabling_minutes), background: "var(--color-flag)" }} />
        <div style={{ width: share(r.non_value_add_minutes), background: "var(--color-neutral-soft)" }} />
      </div>

      <dl style={{ display: "grid", gridTemplateColumns: "auto 1fr", gap: "var(--space-1) var(--space-3)", margin: 0, fontSize: "var(--text-sm)" }}>
        <dt>Value-add</dt>
        <dd data-testid="va-value-add">{minutes(r.value_add_minutes)}</dd>
        <dt>Enabling</dt>
        <dd data-testid="va-enabling">{minutes(r.enabling_minutes)} — required, but the customer would not pay for it</dd>
        <dt>Non-value-add</dt>
        <dd data-testid="va-non-value-add">{minutes(r.non_value_add_minutes)}</dd>
        <dt>Total lead time</dt>
        <dd data-testid="va-total">{minutes(r.total_lead_time_minutes)}</dd>
      </dl>

      {r.steps_untimed > 0 && (
        <VerdictBanner
          tone="flag"
          headline={`${r.steps_untimed} step${r.steps_untimed === 1 ? "" : "s"} carry no time, so ${
            r.steps_untimed === 1 ? "it is" : "they are"
          } excluded from this ratio.`}
          detail="The percentage above is computed over the timed steps only. Time the rest before quoting it."
        />
      )}
    </Panel>
  );
}
