import { useState } from "react";
import { Button, Field, TextArea, VerdictBanner } from "../design/components";
import { verdictToneForGateStatus } from "./statusTone";
import { overrideGate } from "../api/client";
import { ApiError } from "../api/errors";
import { getGateOverride, recordGateOverride } from "./gateOverrides";
import { toolById } from "./tools";
import type { CombinedGate } from "./gateLogic";
import type { Phase } from "../api/types";

export interface GateBannerProps {
  phase: Phase;
  projectId: string;
  gate: CombinedGate;
  /** Called after a successful override so the caller can bump its
   * refresh key and re-render. */
  onOverridden: () => void;
}

function missingLabel(missing: string[]): string {
  return missing.map((id) => toolById(id)?.name ?? id).join(", ");
}

/** Renders the gate state for one phase's entry gate(s) exactly as the
 * engine reports it (M1 brief): CLEAR renders nothing (no noise for the
 * normal case), SOFT_BLOCK shows the missing list plus an override
 * affordance requiring a reason, HARD_BLOCK shows the reason with no
 * override control at all, NOT_YET_BUILT shows the engine's own note. */
export function GateBanner({ phase, projectId, gate, onOverridden }: GateBannerProps) {
  const [reason, setReason] = useState("");
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (gate.status === "CLEAR") return null;

  const softGateIds = Object.entries(gate.byGateId)
    .filter(([, r]) => r.status === "SOFT_BLOCK")
    .map(([id]) => id);
  const alreadyOverridden = gate.status === "SOFT_BLOCK" && softGateIds.every((id) => getGateOverride(projectId, id));

  async function submitOverride() {
    if (!reason.trim()) return;
    setSubmitting(true);
    setError(null);
    const timestamp = new Date().toISOString();
    try {
      for (const gateId of softGateIds) {
        await overrideGate({ gate_id: gateId, project_id: projectId, reason, timestamp });
        recordGateOverride(projectId, gateId, reason, timestamp);
      }
      setShowOverrideForm(false);
      setReason("");
      onOverridden();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not log the override.");
    } finally {
      setSubmitting(false);
    }
  }

  if (gate.status === "HARD_BLOCK") {
    return (
      <VerdictBanner
        tone={verdictToneForGateStatus(gate.status)}
        headline={`${phase} is locked — HARD_BLOCK`}
        detail={gate.reasons.join(" ") || "This phase cannot be entered yet."}
      />
    );
  }

  if (gate.status === "NOT_YET_BUILT") {
    return (
      <VerdictBanner
        tone={verdictToneForGateStatus(gate.status)}
        headline={`${phase}'s entry gate isn't built yet — NOT_YET_BUILT`}
        detail={gate.reasons.join(" ") || "The engine doesn't check this transition yet."}
      />
    );
  }

  // SOFT_BLOCK
  if (alreadyOverridden) {
    const rec = getGateOverride(projectId, softGateIds[0]);
    return (
      <VerdictBanner
        tone="flag"
        headline={`${phase} — SOFT_BLOCK, overridden`}
        detail={`Missing: ${missingLabel(gate.missing)}. Reason logged: "${rec?.reason}"`}
      />
    );
  }

  return (
    <VerdictBanner
      tone={verdictToneForGateStatus(gate.status)}
      headline={`${phase} is missing something — SOFT_BLOCK`}
      detail={`Missing: ${missingLabel(gate.missing)}. You can still work here, but proceeding needs a logged reason.`}
      actions={
        showOverrideForm ? (
          <div style={{ width: "100%" }}>
            <Field label="Reason for proceeding anyway" required>
              <TextArea
                data-testid="gate-override-reason"
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. SIPOC and CTQ pending; unblocking to start Measure prep"
                rows={2}
              />
            </Field>
            {error && <VerdictBanner tone="fail" headline={error} />}
            <Button
              variant="danger"
              size="sm"
              disabled={submitting || !reason.trim()}
              onClick={() => void submitOverride()}
              data-testid="gate-override-submit"
            >
              {submitting ? "Logging…" : "Confirm override"}
            </Button>{" "}
            <Button variant="ghost" size="sm" onClick={() => setShowOverrideForm(false)}>
              Cancel
            </Button>
          </div>
        ) : (
          <Button variant="secondary" size="sm" onClick={() => setShowOverrideForm(true)} data-testid="gate-override-open">
            Override & proceed
          </Button>
        )
      }
    />
  );
}
