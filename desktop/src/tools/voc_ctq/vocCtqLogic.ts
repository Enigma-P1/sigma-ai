import type { Ctq, CtqDirection, CustomerNeed, VocCtqArtifact, VocCustomer, VocStatement, VocStatementSource } from "../../api/types";

export interface VocCtqState {
  customers: VocCustomer[];
  statements: VocStatement[];
  needs: CustomerNeed[];
  ctqs: Ctq[];
  primary_ctq_id: string;
  charter_metric_link: string;
}

export const emptyCustomer = (): VocCustomer => ({ role: "", is_internal: false });

/** IDs are assigned from the current list length, not typed by hand -- a
 * user can't mistype "S1" as "S-1" and silently orphan a need's reference
 * (prescore/voc_ctq.py's tree_completeness is what would catch a typo, but
 * removing the chance to typo is better). Callers pass the *current*
 * length at add-time (see each section's `makeEmpty` prop in VocCtqForm). */
export const makeStatement = (existingCount: number): VocStatement => ({
  statement_id: `S${existingCount + 1}`,
  customer_role: "",
  text: "",
  source: "interview",
  source_detail: "",
});

export const makeNeed = (existingCount: number): CustomerNeed => ({
  need_id: `N${existingCount + 1}`,
  statement_ids: [],
  text: "",
});

export const makeCtq = (existingCount: number): Ctq => ({
  ctq_id: `C${existingCount + 1}`,
  need_id: "",
  measure: "",
  direction: "lower_is_better",
  target: "",
  critical_vs_easy_check: "",
});

export const EMPTY_VOC_CTQ_STATE: VocCtqState = {
  customers: [emptyCustomer()],
  statements: [makeStatement(0)],
  needs: [makeNeed(0)],
  ctqs: [makeCtq(0)],
  primary_ctq_id: "",
  charter_metric_link: "",
};

export function vocCtqStateFromArtifact(artifact: VocCtqArtifact): VocCtqState {
  return {
    customers: artifact.customers,
    statements: artifact.statements,
    needs: artifact.needs,
    ctqs: artifact.ctqs,
    primary_ctq_id: artifact.primary_ctq_id,
    charter_metric_link: artifact.charter_metric_link,
  };
}

export function vocCtqCanSave(state: VocCtqState): boolean {
  return (
    state.customers.length > 0 &&
    state.customers.every((c) => c.role.trim()) &&
    state.statements.length > 0 &&
    state.statements.every((s) => s.customer_role.trim() && s.text.trim()) &&
    state.needs.length > 0 &&
    state.needs.every((n) => n.text.trim() && n.statement_ids.length > 0) &&
    state.ctqs.length > 0 &&
    state.ctqs.every((c) => c.need_id.trim() && c.measure.trim() && c.critical_vs_easy_check.trim()) &&
    state.primary_ctq_id.trim() !== "" &&
    state.charter_metric_link.trim() !== ""
  );
}

export const CTQ_DIRECTION_LABELS: Record<CtqDirection, string> = {
  higher_is_better: "Higher is better",
  lower_is_better: "Lower is better",
  target_is_best: "Target is best",
};

export const STATEMENT_SOURCE_LABELS: Record<VocStatementSource, string> = {
  interview: "Interview",
  complaint_log: "Complaint log",
  survey: "Survey",
  direct_observation: "Direct observation",
  other: "Other",
};
