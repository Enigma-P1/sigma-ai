import type { CopqArtifact, CopqCategory, PrescoreResult } from "../../api/types";
import type { CopqRowValue } from "./CopqRowFields";

export const CATEGORY_LABELS: Record<CopqCategory, string> = {
  scrap: "Scrap",
  rework: "Rework",
  overtime: "Overtime",
  expediting: "Expediting",
  lost_business: "Lost business",
  custom: "Custom…",
};

export function flagFor(message?: string) {
  return message ? { status: "hard_flag" as const, message } : undefined;
}

export function emptyCopqRow(): CopqRowValue {
  return { category: "scrap", custom_label: "", quantity: 0, rate: 0, period: "", basis: "", is_estimate: false };
}

/** Rebuild row state from a loaded/saved artifact (T-01/T-03's load effect
 * does the equivalent inline; pulled into a function here since useCopqForm
 * and CopqForm's tests both want it). */
export function copqRowsFromArtifact(artifact: CopqArtifact): CopqRowValue[] {
  return artifact.rows.map((r) => ({
    category: r.category,
    custom_label: r.custom_label ?? "",
    quantity: r.quantity,
    rate: r.rate,
    period: r.period,
    basis: r.basis,
    is_estimate: r.is_estimate,
  }));
}

export function copqRowsToBody(rows: CopqRowValue[]) {
  return rows.map((r) => ({
    category: r.category,
    custom_label: r.category === "custom" ? r.custom_label.trim() : null,
    quantity: r.quantity,
    rate: r.rate,
    period: r.period.trim(),
    basis: r.basis.trim(),
    is_estimate: r.is_estimate,
  }));
}

export function copqCanSave(rows: CopqRowValue[]): boolean {
  return (
    rows.length > 0 &&
    rows.every(
      (r) => r.quantity >= 0 && r.rate >= 0 && r.period.trim() && r.basis.trim() && (r.category !== "custom" || r.custom_label.trim()),
    )
  );
}

/** A placeholder Computed[float] shape so the request body satisfies the
 * schema (CopqArtifact.total is a required field, not a computed_field --
 * artifacts/copq.py). `value` is real client arithmetic (so prescore's
 * total_matches_rows check has something correct to confirm against);
 * `provenance` is a submission stub, never displayed -- what the form
 * renders as "the total" always comes from a fresh loadArtifact() after
 * save, never this draft (see useCopqForm's handleSave). */
export function draftCopqTotal(rows: CopqRowValue[]) {
  return {
    value: rows.reduce((sum, r) => sum + r.quantity * r.rate, 0),
    provenance: {
      input_hash: "pending-server-save",
      method: "client draft pending engine save",
      engine_version: "pending",
      assumptions_checked: [] as string[],
      warnings: [] as string[],
    },
  };
}

/** Worst-status-first summary of the prescore checks that read on the row
 * collection as a whole (both of T-02's checks do -- copqChecks.ts). */
export function copqRowsFlag(results: PrescoreResult[]) {
  const notPassing = results.filter((r) => r.status !== "pass");
  if (notPassing.length === 0) return undefined;
  const status = notPassing.some((r) => r.status === "hard_flag") ? ("hard_flag" as const) : ("flag" as const);
  return { status, message: notPassing.map((r) => r.detail).join(" ") };
}
