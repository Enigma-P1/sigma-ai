import { useState } from "react";
import { Button, Field, Panel, SelectInput, StatusPill, TextArea } from "../../design/components";
import type { PillTone } from "../../design/components";
import type { FishboneCause, FishboneEvidence, ProjectMetadata } from "../../api/types";
import { CAUSE_STATUSES, FISHBONE_BRANCHES } from "../../api/types";
import { BRANCH_LABELS, EVIDENCE_KIND_LABELS, STATUS_LABELS, isUnproven } from "./fishboneLogic";
import { EvidenceDrawer } from "./EvidenceDrawer";

export interface CauseInspectorProps {
  projectId: string;
  project: ProjectMetadata;
  cause: FishboneCause;
  parent: FishboneCause | null;
  onChange: (patch: Partial<FishboneCause>) => void;
  onAskWhy: (causeId: string) => void;
}

const TONE_FOR_STATUS: Record<FishboneCause["status"], PillTone> = {
  candidate: "neutral",
  investigating: "accent",
  verified: "pass",
  ruled_out: "flag",
};

/** Every field a selected cause carries: branch, text, status (color-coded
 * per canvasColors.ts's tokens), evidence (opens EvidenceDrawer -- the
 * schema requires a non-empty Evidence once status is set to verified),
 * and the "ask why again" 5-Whys affordance. */
export function CauseInspector({ projectId, project, cause, parent, onChange, onAskWhy }: CauseInspectorProps) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const blockedFromVerified = cause.status !== "verified" && !cause.evidence;

  function handleEvidenceConfirm(evidence: FishboneEvidence | null) {
    onChange({ evidence });
    setDrawerOpen(false);
  }

  function handleStatusChange(status: FishboneCause["status"]) {
    // Mirror the schema's own rule client-side: don't let the picker set
    // "verified" with no evidence attached -- the save would just be
    // rejected, so refuse the state change here and open the drawer.
    if (status === "verified" && !cause.evidence) {
      setDrawerOpen(true);
      return;
    }
    onChange({ status });
  }

  return (
    <Panel title="Cause inspector" subtitle={cause.cause_id}>
      {parent && <p className="sigma-fishbone-why-context">Why does &ldquo;{parent.text || "(parent cause)"}&rdquo; happen?</p>}

      <div className="sigma-fishbone-inspector-row">
        <Field label="Branch" htmlFor="fishbone-cause-branch">
          <SelectInput id="fishbone-cause-branch" data-testid="fishbone-cause-branch" value={cause.branch} onChange={(e) => onChange({ branch: e.target.value as FishboneCause["branch"] })}>
            {FISHBONE_BRANCHES.map((b) => (
              <option key={b} value={b}>{BRANCH_LABELS[b]}</option>
            ))}
          </SelectInput>
        </Field>
        <Field label="Status" htmlFor="fishbone-cause-status" right={<StatusPill tone={TONE_FOR_STATUS[cause.status]} label={STATUS_LABELS[cause.status]} />}>
          <SelectInput id="fishbone-cause-status" data-testid="fishbone-cause-status" value={cause.status} onChange={(e) => handleStatusChange(e.target.value as FishboneCause["status"])}>
            {CAUSE_STATUSES.map((s) => (
              <option key={s} value={s}>{STATUS_LABELS[s]}</option>
            ))}
          </SelectInput>
        </Field>
      </div>

      <Field label="Cause" required htmlFor="fishbone-cause-text" helper="A condition or mechanism ('labels applied before ink dries'), not an absent solution ('no barcode scanner').">
        <TextArea id="fishbone-cause-text" data-testid="fishbone-cause-text" rows={2} value={cause.text} onChange={(e) => onChange({ text: e.target.value })} />
      </Field>

      <Field
        label="Evidence" helper={blockedFromVerified ? "What data supports this? Required before this cause can be marked verified." : undefined}
        right={isUnproven(cause) ? <span className="sigma-fishbone-unproven-chip" data-testid="fishbone-inspector-unproven-chip">no evidence yet</span> : undefined}
      >
        {cause.evidence ? (
          <p className="sigma-fishbone-evidence-summary" data-testid="fishbone-evidence-summary">
            {EVIDENCE_KIND_LABELS[cause.evidence.kind]}: {cause.evidence.ref}
          </p>
        ) : (
          <p className="sigma-fishbone-evidence-summary sigma-fishbone-evidence-summary--empty">No evidence attached yet.</p>
        )}
        <Button variant="secondary" size="sm" type="button" onClick={() => setDrawerOpen(true)} data-testid="fishbone-evidence-open">
          {cause.evidence ? "Edit evidence" : "Set evidence"}
        </Button>
      </Field>

      <Button variant="ghost" size="sm" type="button" onClick={() => onAskWhy(cause.cause_id)} data-testid="fishbone-ask-why">
        Ask why again →
      </Button>

      {drawerOpen && (
        <EvidenceDrawer projectId={projectId} project={project} current={cause.evidence} onClose={() => setDrawerOpen(false)} onConfirm={handleEvidenceConfirm} />
      )}
    </Panel>
  );
}
