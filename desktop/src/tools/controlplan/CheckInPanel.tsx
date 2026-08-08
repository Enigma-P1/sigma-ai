import { useState } from "react";
import { Button, Field, Panel, StatusPill, TextInput, VerdictBanner } from "../../design/components";
import type { CompletedCheckIn, FrozenLimitsRef } from "../../api/types";

export interface CheckInPanelProps {
  frozenLimits: FrozenLimitsRef | null;
  nextDue: string | null;
  completed: CompletedCheckIn[];
  onEnter: (value: number, note: string) => void;
}

function bandText(limits: FrozenLimitsRef): string {
  if (limits.chart_type === "imr") return `[${limits.lcl?.toFixed(2)}, ${limits.ucl?.toFixed(2)}]`;
  return `p_bar = ${limits.p_bar?.toFixed(3)}`;
}

/** "week 3: is the fix holding?" -- the due list, the enter-numbers flow,
 * and engine pass/fail rendered with the frozen-limit context it was
 * judged against (task brief). Only offered once a T-21 chart has frozen
 * (frozenLimits non-null); otherwise this panel explains what's missing. */
export function CheckInPanel({ frozenLimits, nextDue, completed, onEnter }: CheckInPanelProps) {
  const [value, setValue] = useState("");
  const [note, setNote] = useState("");

  return (
    <Panel title="Scheduled Check-ins" subtitle='"Is the fix holding?" -- entered numbers judged against the frozen control limits'>
      {!frozenLimits ? (
        <VerdictBanner tone="flag" headline="No frozen control chart yet" detail="Freeze a T-21 control chart first -- check-ins are judged against its frozen limits." />
      ) : (
        <div data-testid="controlplan-frozen-limits-context">
          <VerdictBanner
            tone="neutral" headline={`Frozen band: ${bandText(frozenLimits)}`}
            detail={`${frozenLimits.chart_type.toUpperCase()} chart, frozen ${frozenLimits.frozen_at}`}
          />
        </div>
      )}

      {nextDue && <p data-testid="controlplan-next-due">Next due: {nextDue}</p>}

      {frozenLimits && (
        <div className="sigma-controlplan-checkin-entry">
          <Field label="This check-in's value" htmlFor="controlplan-checkin-value">
            <TextInput id="controlplan-checkin-value" data-testid="controlplan-checkin-value" type="number" value={value} onChange={(e) => setValue(e.target.value)} />
          </Field>
          <Field label="Note" htmlFor="controlplan-checkin-note">
            <TextInput id="controlplan-checkin-note" data-testid="controlplan-checkin-note" value={note} onChange={(e) => setNote(e.target.value)} />
          </Field>
          <Button
            variant="primary" disabled={value.trim() === ""} data-testid="controlplan-checkin-enter"
            onClick={() => { onEnter(Number(value), note); setValue(""); setNote(""); }}
          >
            Enter this check-in
          </Button>
        </div>
      )}

      <ul className="sigma-controlplan-checkin-list">
        {completed.map((c) => (
          <li key={c.check_in_id} data-testid={`controlplan-checkin-${c.check_in_id}`}>
            <span>{c.label}</span>
            {c.result && (
              <StatusPill
                tone={c.result.value.verdict === "pass" ? "pass" : "fail"} label={c.result.value.verdict}
                title={c.result.value.detail}
              />
            )}
          </li>
        ))}
      </ul>
    </Panel>
  );
}
