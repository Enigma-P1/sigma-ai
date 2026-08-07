import type { OutputCustomerPair, ProcessStep, SipocArtifact, SupplierInputPair } from "../../api/types";

export interface SipocState {
  supplier_input_pairs: SupplierInputPair[];
  process_steps: { description: string }[]; // step_number is derived from position, never hand-entered
  output_customer_pairs: OutputCustomerPair[];
  scope_start: string;
  scope_end: string;
}

export const EMPTY_SIPOC_STATE: SipocState = {
  supplier_input_pairs: [{ supplier: "", input: "" }],
  process_steps: [{ description: "" }],
  output_customer_pairs: [{ output: "", customer: "" }],
  scope_start: "",
  scope_end: "",
};

export const emptySupplierInputPair = (): SupplierInputPair => ({ supplier: "", input: "" });
export const emptyProcessStep = (): { description: string } => ({ description: "" });
export const emptyOutputCustomerPair = (): OutputCustomerPair => ({ output: "", customer: "" });

export function sipocStateFromArtifact(artifact: SipocArtifact): SipocState {
  return {
    supplier_input_pairs: artifact.supplier_input_pairs,
    process_steps: [...artifact.process_steps].sort((a, b) => a.step_number - b.step_number).map((s) => ({ description: s.description })),
    output_customer_pairs: artifact.output_customer_pairs,
    scope_start: artifact.scope_start,
    scope_end: artifact.scope_end,
  };
}

/** step_number is 1-based position in the list -- never a field the user
 * types, so it can't drift from the list's own order (ProcessStep,
 * artifacts/sipoc.py). */
export function processStepsToBody(steps: { description: string }[]): ProcessStep[] {
  return steps.map((s, i) => ({ step_number: i + 1, description: s.description.trim() }));
}

export function sipocCanSave(state: SipocState): boolean {
  return (
    state.supplier_input_pairs.length > 0 &&
    state.supplier_input_pairs.every((p) => p.supplier.trim() && p.input.trim()) &&
    state.process_steps.length > 0 &&
    state.process_steps.every((s) => s.description.trim()) &&
    state.output_customer_pairs.length > 0 &&
    state.output_customer_pairs.every((p) => p.output.trim() && p.customer.trim()) &&
    state.scope_start.trim() !== "" &&
    state.scope_end.trim() !== ""
  );
}
