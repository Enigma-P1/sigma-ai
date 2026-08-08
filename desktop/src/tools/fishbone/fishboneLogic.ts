import type {
  CausePosition,
  FishboneArtifact,
  FishboneBranch,
  FishboneCause,
  FishboneEvidence,
} from "../../api/types";
import { FISHBONE_BRANCHES } from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as processMapLogic.ts's genId -- unique
 * for a session, not persisted identity; kept local rather than imported
 * so this tool folder stays self-contained (checkSheetLogic.ts/
 * timeStudyLogic.ts's convention, not spaghettiLogic.ts's cross-import). */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export const BRANCH_LABELS: Record<FishboneBranch, string> = {
  people: "People",
  method: "Method",
  machine: "Machine",
  material: "Material",
  measurement: "Measurement",
  environment: "Environment",
};

export const STATUS_LABELS: Record<FishboneCause["status"], string> = {
  candidate: "Candidate",
  investigating: "Investigating",
  verified: "Verified",
  ruled_out: "Ruled out",
};

export const EVIDENCE_KIND_LABELS: Record<NonNullable<FishboneEvidence["kind"]>, string> = {
  dataset: "A saved dataset",
  hypothesis_run: "A hypothesis-test result (T-17)",
  check_sheet: "A check sheet (T-08)",
  observation_note: "An observation note (written here)",
};

// ---- Canvas layout: a spine with three branches above, three below. ----
export const CANVAS_WIDTH = 1040;
export const CANVAS_HEIGHT = 560;
export const SPINE_Y = CANVAS_HEIGHT / 2;
export const SPINE_START_X = 80;
export const HEAD_X = CANVAS_WIDTH - 150;
export const CARD_WIDTH = 148;
export const CARD_HEIGHT = 40;

// Top branches (even index) run left-to-right; bottom branches (odd index)
// mirror them -- three slots per side, evenly spaced along the spine.
const BRANCH_SLOT_X = [260, 480, 700];

export function branchSide(branch: FishboneBranch): "top" | "bottom" {
  const i = FISHBONE_BRANCHES.indexOf(branch);
  return i % 2 === 0 ? "top" : "bottom";
}

export function branchSlotX(branch: FishboneBranch): number {
  const i = FISHBONE_BRANCHES.indexOf(branch);
  return BRANCH_SLOT_X[Math.floor(i / 2)];
}

/** Where a branch's outer label sits -- the diagonal line's far end. */
export function branchLabelPoint(branch: FishboneBranch): { x: number; y: number } {
  const x = branchSlotX(branch);
  const dy = 170;
  return { x: x - 90, y: branchSide(branch) === "top" ? SPINE_Y - dy : SPINE_Y + dy };
}

/** Auto-arranged default position for a new cause on its branch --
 * evenly stepped out along the branch line by how many causes (any
 * status) already sit there, so cards don't stack on top of each other. */
export function defaultCausePosition(branch: FishboneBranch, indexOnBranch: number, depth: number): CausePosition {
  const label = branchLabelPoint(branch);
  const slot = { x: branchSlotX(branch), y: branchSide(branch) === "top" ? SPINE_Y - 170 : SPINE_Y + 170 };
  const t = 0.35 + Math.min(indexOnBranch, 4) * 0.14; // spread along the branch line, capped
  const baseX = slot.x + (label.x - slot.x) * t;
  const baseY = slot.y + (label.y - slot.y) * t;
  // A why-chain sub-cause indents further out along the same direction --
  // the "indented card stack" the build brief asks for.
  const indentX = branchSide(branch) === "top" ? depth * 18 : depth * 18;
  const indentY = branchSide(branch) === "top" ? -depth * 34 : depth * 34;
  return { x: baseX + indentX, y: baseY + indentY };
}

export function emptyCause(branch: FishboneBranch, parentCauseId: string | null, whyChainPosition: number | null): FishboneCause {
  return {
    cause_id: genId("cause"),
    branch,
    text: "",
    parent_cause_id: parentCauseId,
    status: "candidate",
    evidence: null,
    why_chain_position: whyChainPosition,
  };
}

export function causesForBranch(causes: FishboneCause[], branch: FishboneBranch): FishboneCause[] {
  return causes.filter((c) => c.branch === branch);
}

export function childrenOf(causes: FishboneCause[], causeId: string): FishboneCause[] {
  return causes.filter((c) => c.parent_cause_id === causeId);
}

/** Chain depth: 0 for a root (top-level) cause, 1 for its first why, etc.
 * Walks parent_cause_id -- causes with a cycle can't reach this UI (the
 * engine rejects a cycle at save), so a hard cap just prevents a runaway
 * loop on bad in-progress client state. */
export function causeDepth(causes: FishboneCause[], causeId: string): number {
  const byId = new Map(causes.map((c) => [c.cause_id, c]));
  let depth = 0;
  let current = byId.get(causeId);
  while (current?.parent_cause_id) {
    depth += 1;
    current = byId.get(current.parent_cause_id);
    if (depth > 20) break;
  }
  return depth;
}

/** The "no evidence yet" chip: a candidate cause carrying no evidence at
 * all -- the unproven-flag visual the build brief calls for. */
export function isUnproven(cause: FishboneCause): boolean {
  return cause.status === "candidate" && !cause.evidence;
}

export function fishboneMissingFields(effectText: string, causes: FishboneCause[]): string[] {
  const missing: string[] = [];
  if (effectText.trim() === "") missing.push("the effect statement");
  if (!causes.every((c) => c.text.trim() !== "")) missing.push("every cause's text");
  return missing;
}

export function canSaveFishbone(effectText: string, causes: FishboneCause[]): boolean {
  return fishboneMissingFields(effectText, causes).length === 0;
}

export function buildFishboneBody(input: {
  artifactId: string;
  schemaVersion: number;
  effectText: string;
  charterRef: string | null;
  causes: FishboneCause[];
  layout: Record<string, CausePosition>;
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-15",
    created_at: now,
    updated_at: now,
    effect: { text: input.effectText, charter_ref: input.charterRef || null },
    causes: input.causes,
    layout: input.layout,
  };
}

export function fishboneStateFromArtifact(artifact: FishboneArtifact): {
  effectText: string;
  charterRef: string;
  causes: FishboneCause[];
  layout: Record<string, CausePosition>;
} {
  return {
    effectText: artifact.effect.text,
    charterRef: artifact.effect.charter_ref ?? "",
    causes: artifact.causes,
    layout: artifact.layout ?? {},
  };
}
