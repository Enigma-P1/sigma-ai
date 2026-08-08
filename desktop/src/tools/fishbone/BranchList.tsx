import { Button, Panel, StatusPill } from "../../design/components";
import type { PillTone } from "../../design/components";
import type { FishboneCause } from "../../api/types";
import { FISHBONE_BRANCHES } from "../../api/types";
import { BRANCH_LABELS, STATUS_LABELS, causeDepth, causesForBranch, isUnproven } from "./fishboneLogic";

export interface BranchListProps {
  causes: FishboneCause[];
  selectedCauseId: string | null;
  onSelect: (causeId: string) => void;
  onAdd: (branch: FishboneCause["branch"]) => void;
}

const TONE_FOR_STATUS: Record<FishboneCause["status"], PillTone> = {
  candidate: "neutral",
  investigating: "accent",
  verified: "pass",
  ruled_out: "flag",
};

/** Non-canvas branch overview, one section per 6M branch: every cause on
 * that branch (sub-causes indented under their parent, the 5-Whys chain
 * made readable as a list) plus a "+ Add cause" button per branch --
 * Konva nodes are canvas-drawn and can't carry DOM test ids, so this is
 * the reliable control surface (StepsList.tsx's convention). */
export function BranchList({ causes, selectedCauseId, onSelect, onAdd }: BranchListProps) {
  return (
    <Panel title="Branches" subtitle="Select a cause to edit it in the inspector">
      {FISHBONE_BRANCHES.map((branch, branchIndex) => {
        const onBranch = causesForBranch(causes, branch).sort((a, b) => causeDepth(causes, a.cause_id) - causeDepth(causes, b.cause_id));
        return (
          <div key={branch} className="sigma-fishbone-branch">
            <div className="sigma-fishbone-branch__name">{BRANCH_LABELS[branch]}</div>
            <ul className="sigma-fishbone-cause-list">
              {onBranch.map((cause) => (
                <li key={cause.cause_id} style={{ paddingLeft: `${causeDepth(causes, cause.cause_id) * 14}px` }}>
                  <button
                    type="button"
                    data-testid={`fishbone-cause-row-${cause.cause_id}`}
                    className={`sigma-fishbone-cause-row ${cause.cause_id === selectedCauseId ? "sigma-fishbone-cause-row--selected" : ""}`}
                    onClick={() => onSelect(cause.cause_id)}
                  >
                    <StatusPill tone={TONE_FOR_STATUS[cause.status]} label={STATUS_LABELS[cause.status]} />
                    <span>{cause.text || "(new cause)"}</span>
                    {isUnproven(cause) && (
                      <span className="sigma-fishbone-unproven-chip" data-testid={`fishbone-unproven-chip-${cause.cause_id}`}>
                        no evidence yet
                      </span>
                    )}
                  </button>
                </li>
              ))}
            </ul>
            <Button variant="ghost" size="sm" type="button" onClick={() => onAdd(branch)} data-testid={`fishbone-add-cause-${branchIndex}`}>
              + Add cause to {BRANCH_LABELS[branch]}
            </Button>
          </div>
        );
      })}
    </Panel>
  );
}
