import { useState } from "react";
import { Button, Field, Modal, TextInput } from "../design/components";
import { splitCite } from "./rubricCite";
import "./DeleteReasonModal.css";

export interface DeleteReasonModalProps {
  title: string;
  bodyText: string;
  onConfirm: (reason: string) => void;
  onClose: () => void;
  /** Prefixes every data-testid this modal renders, e.g. "timestudy-delete-reason"
   * -> "timestudy-delete-reason-input" / "-confirm". */
  testIdPrefix: string;
}

/** Shared "delete this row, but only with a logged, non-empty reason"
 * prompt (rubric R-MEA-04, generalized to every soft-deletable row: T-09
 * cycles, T-08 entries -- see CyclesTable.tsx / EntriesTable.tsx). Confirm
 * stays disabled until a reason is actually typed; the caller decides what
 * "delete" means (a soft-delete marker, never a hard removal). */
export function DeleteReasonModal({ title, bodyText, onConfirm, onClose, testIdPrefix }: DeleteReasonModalProps) {
  const [reason, setReason] = useState("");

  function confirm() {
    if (!reason.trim()) return;
    onConfirm(reason.trim());
  }

  const body = splitCite(bodyText);

  return (
    <Modal title={title} onClose={onClose}>
      <p title={body.cite ?? undefined}>{body.text}</p>
      <Field label="Reason for deleting this row" required htmlFor={`${testIdPrefix}-input`}>
        <TextInput
          id={`${testIdPrefix}-input`} data-testid={`${testIdPrefix}-input`} autoFocus
          value={reason} onChange={(e) => setReason(e.target.value)}
        />
      </Field>
      <div className="sigma-delete-reason-modal__actions">
        <Button variant="danger" disabled={!reason.trim()} onClick={confirm} data-testid={`${testIdPrefix}-confirm`}>
          Delete
        </Button>{" "}
        <Button variant="ghost" onClick={onClose}>
          Cancel
        </Button>
      </div>
    </Modal>
  );
}
