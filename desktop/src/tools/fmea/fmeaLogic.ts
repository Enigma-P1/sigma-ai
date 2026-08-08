import type { FmeaAnchors, FmeaArtifact, FmeaRow } from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as processMapLogic.ts's genId -- unique
 * for a session, not persisted identity. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

/** Mirrors engine/sigma_engine/artifacts/fmea.py's SEVERITY_ANCHORS /
 * OCCURRENCE_ANCHORS / DETECTION_ANCHORS by hand (canvasColors.ts's
 * documented convention for mirroring engine/CSS constants client-side) --
 * this engine's own original wording, so the anchor text is available for
 * immediate display before the first save. Once a version is saved, the
 * server-echoed `anchors` field is what renders (FmeaWorksheet.tsx),
 * kept identical here on purpose. */
export const CLIENT_ANCHORS: FmeaAnchors = {
  severity: {
    "10": "Extreme -- safety hazard or a regulatory violation, with no warning before it happens.",
    "9": "Extreme -- safety hazard or a regulatory violation, but with some warning beforehand.",
    "8": "Very high -- the product or process becomes unusable; the customer is very dissatisfied.",
    "7": "High -- major function is lost; most customers are significantly dissatisfied.",
    "6": "Moderate-high -- performance is noticeably degraded; the customer is dissatisfied.",
    "5": "Moderate -- performance is reduced in a way most customers notice and dislike.",
    "4": "Low-moderate -- a minor loss of performance; many customers notice.",
    "3": "Low -- a slight, easily-tolerated effect; only a discerning customer notices.",
    "2": "Very low -- a minor nuisance most customers would never notice.",
    "1": "None -- no discernible effect on the customer or the process.",
  },
  occurrence: {
    "10": "Very high -- the cause is present on nearly every unit or cycle.",
    "9": "Very high -- frequent, roughly 1 in 3.",
    "8": "High -- repeated failures, roughly 1 in 8.",
    "7": "High -- roughly 1 in 20.",
    "6": "Moderate -- occasional failures, roughly 1 in 80.",
    "5": "Moderate -- roughly 1 in 400.",
    "4": "Moderate-low -- roughly 1 in 2,000.",
    "3": "Low -- relatively few failures, roughly 1 in 15,000.",
    "2": "Low -- rare, roughly 1 in 150,000.",
    "1": "Remote -- failure from this cause is unlikely; no known history of it.",
  },
  detection: {
    "10": "No current control could detect this cause or mode before it reaches the next step.",
    "9": "Very remote chance the current controls catch it in time.",
    "8": "Remote chance of detection with the current controls.",
    "7": "Very low chance of detection with the current controls.",
    "6": "Low chance of detection with the current controls.",
    "5": "Moderate chance the current controls catch it.",
    "4": "Moderately high chance the current controls catch it.",
    "3": "High chance the current controls catch it.",
    "2": "Very high chance the current controls catch it before it moves on.",
    "1": "Almost certain -- current controls will catch it before it ever leaves this step.",
  },
};

// Verbatim, short (build brief): the RPN-limitation banner every FMEA
// screen carries, whatever sort order the worksheet displays (rubric
// R-ANA-03 #3).
export const RPN_LIMITATION_TEXT = "Equal RPNs are not equal risks. High severity is never ignorable.";

export function emptyRow(): FmeaRow {
  return {
    row_id: genId("fmea-row"),
    process_step_ref: null,
    step_name: "",
    failure_mode: "",
    effect: "",
    cause: "",
    severity: 1,
    occurrence: 1,
    detection: 1,
    action: "",
    action_owner: "",
    action_due: null,
    action_status: "open",
    anchors_consulted: false,
  };
}

/** Client-side-only display value before the first save -- the engine's
 * computed_field is the authority once a row has round-tripped (row.rpn
 * is then present; see the FmeaRow.rpn doc comment in api/types.ts). */
export function draftRpn(row: FmeaRow): number {
  return row.severity * row.occurrence * row.detection;
}

/** Same severity-desc/rpn-desc/row_id tie-break as the engine's
 * compute_sorted_view -- used only before the first save (or for the
 * RPN-sort toggle, which the engine never computes since either order is
 * just a client reordering of already-trustworthy engine numbers once an
 * artifact has round-tripped). */
export function clientSeverityFirstOrder(rows: FmeaRow[]): string[] {
  return [...rows]
    .sort((a, b) => b.severity - a.severity || draftRpn(b) - draftRpn(a) || a.row_id.localeCompare(b.row_id))
    .map((r) => r.row_id);
}

export function clientRpnOrder(rows: FmeaRow[]): string[] {
  return [...rows]
    .sort((a, b) => {
      const rpnA = a.rpn ?? draftRpn(a);
      const rpnB = b.rpn ?? draftRpn(b);
      return rpnB - rpnA || a.row_id.localeCompare(b.row_id);
    })
    .map((r) => r.row_id);
}

export function orderedRows(rows: FmeaRow[], sortMode: "severity" | "rpn", engineSortedView: string[] | null): FmeaRow[] {
  const byId = new Map(rows.map((r) => [r.row_id, r]));
  const order =
    sortMode === "rpn" ? clientRpnOrder(rows)
    : engineSortedView && engineSortedView.length === rows.length ? engineSortedView
    : clientSeverityFirstOrder(rows);
  return order.map((id) => byId.get(id)).filter((r): r is FmeaRow => r != null);
}

export function fmeaMissingFields(rows: FmeaRow[]): string[] {
  if (rows.length === 0) return ["at least one row"];
  const missing: string[] = [];
  if (!rows.every((r) => r.step_name.trim() !== "")) missing.push("every row's step name");
  if (!rows.every((r) => r.failure_mode.trim() !== "")) missing.push("every row's failure mode");
  if (!rows.every((r) => r.effect.trim() !== "")) missing.push("every row's effect");
  if (!rows.every((r) => r.cause.trim() !== "")) missing.push("every row's cause");
  return missing;
}

export function canSaveFmea(rows: FmeaRow[]): boolean {
  return fmeaMissingFields(rows).length === 0;
}

export function buildFmeaBody(input: { artifactId: string; schemaVersion: number; rows: FmeaRow[] }): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-16",
    created_at: now,
    updated_at: now,
    rows: input.rows,
  };
}

export function fmeaStateFromArtifact(artifact: FmeaArtifact): { rows: FmeaRow[] } {
  return { rows: artifact.rows };
}
