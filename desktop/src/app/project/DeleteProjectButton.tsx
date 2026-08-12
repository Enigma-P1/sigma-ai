import { useState } from "react";
import { Button, Modal, TextInput, VerdictBanner } from "../../design/components";
import { deleteProject } from "../../api/client";
import { ApiError } from "../../api/errors";
import { forgetProject } from "./recentProjects";

export interface DeleteProjectButtonProps {
  projectId: string;
  name: string;
  /** How much work is in there, so the confirmation can say what is being
   * lost rather than asking "are you sure?" about an abstraction. Optional
   * because the recently-opened list is backed by localStorage and does not
   * know the count -- and inventing one there would be worse than omitting
   * it from the sentence. */
  artifactCount?: number;
  onDeleted: () => void;
}

/** Delete a project, for good.
 *
 * WHY: a tester swept the project list, diagnostics, advisor settings, and
 * tried hovering and right-clicking the card, looking for undo or delete.
 * There was none anywhere. His conclusion was not outrage, it was
 * arithmetic -- "if I keep using it I will eventually create junk" -- and
 * software you cannot tidy is software that slowly stops being usable.
 *
 * WHY THE TYPED CONFIRMATION. The same screen already has an "×" that
 * FORGETS a project (drops it from this machine's recently-opened list and
 * touches nothing on disk). Two controls one above the other, one
 * reversible and one not, is exactly the arrangement that gets somebody's
 * project deleted by muscle memory. So this one costs a deliberate act:
 * type the project's name. Not friction for its own sake -- it makes the
 * two impossible to confuse, and it puts the name of what you are about to
 * lose under your own fingers.
 */
export function DeleteProjectButton({ projectId, name, artifactCount, onDeleted }: DeleteProjectButtonProps) {
  const [open, setOpen] = useState(false);
  const [typed, setTyped] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const confirmed = typed.trim() === name.trim();

  async function run() {
    setBusy(true);
    setError(null);
    try {
      await deleteProject(projectId);
      // The recently-opened list lives in localStorage and knows nothing
      // about the filesystem, so a deleted project would sit in it as a
      // dead row pointing at a folder that no longer exists.
      forgetProject(projectId);
      setOpen(false);
      onDeleted();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not delete the project.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className="sigma-recent-list__delete"
        onClick={() => {
          setTyped("");
          setError(null);
          setOpen(true);
        }}
        title={`Permanently delete ${name} and everything in it`}
        data-testid={`ondisk-delete-${projectId}`}
      >
        Delete
      </button>
      {open && (
        <Modal title={`Delete "${name}"?`} onClose={() => setOpen(false)}>
          <VerdictBanner
            tone="fail"
            headline="This deletes the project folder and everything in it, permanently."
            detail={
              artifactCount != null && artifactCount > 0
                ? `${artifactCount} saved tool${artifactCount === 1 ? "" : "s"}, along with any imported data, drafts and reports, will be gone. There is no undo.`
                : "Everything saved in it — imported data, drafts, reports and any saved tools — will be gone. There is no undo."
            }
          />
          <p className="sigma-delete-project__note">
            The <strong>×</strong> next to a recent project only removes it from that list and leaves the files
            alone. This is not that. To confirm you meant this one, type its name:
          </p>
          <TextInput
            id="delete-project-confirm"
            data-testid="ondisk-delete-confirm-input"
            value={typed}
            onChange={(e) => setTyped(e.target.value)}
            placeholder={name}
          />
          {error && <VerdictBanner tone="fail" headline={error} />}
          <div className="sigma-delete-project__actions">
            <Button onClick={() => setOpen(false)} data-testid="ondisk-delete-cancel">
              Keep it
            </Button>
            <Button
              variant="primary"
              disabled={!confirmed || busy}
              onClick={() => void run()}
              data-testid="ondisk-delete-confirm"
            >
              {busy ? "Deleting…" : "Delete permanently"}
            </Button>
          </div>
        </Modal>
      )}
    </>
  );
}
