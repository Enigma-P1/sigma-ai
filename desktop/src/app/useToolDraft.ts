import { useCallback, useEffect, useRef, useState } from "react";
import { deleteDraft, loadDraft, saveDraft } from "../api/client";
import { useSaveState } from "./SaveStateContext";

// Dave typed a problem statement and a goal, navigated away, and lost
// both -- Save sat behind eleven other required fields he hadn't touched
// yet (docs/uat/PLAN.md Phase 4.1). This hook is the fix: it autosaves
// whatever a form has typed, on a debounce, to the engine's per-tool
// draft store (engine/sigma_engine/drafts.py) -- never on every
// character; a person mid-sentence doesn't need the last half-second of
// typing durable, just the last pause in it.
const DEBOUNCE_MS = 1500;

export interface StoredDraft<T> {
  payload: T;
  updatedAt: string;
}

export interface UseToolDraftOptions<T> {
  /** What this form would be showing right now if no draft existed -- the
   * freshly loaded artifact, or this form's own empty/default state.
   * Pass `undefined` while that is still being decided (an artifact load
   * in flight): the hook won't restore or autosave anything until it has
   * a real baseline to compare against, because "different from what?"
   * has no answer yet. */
  baseline: T | undefined;
  state: T;
  setState: (value: T) => void;
}

export interface UseToolDraftResult {
  /** Non-null exactly while a "restored your typing" banner should show.
   * The time the restored draft was stored -- frozen at the moment it
   * was applied, not a live clock, so the banner keeps saying what it
   * first said even as further edits advance the draft underneath it. */
  restoredAt: string | null;
  /** The most recently known-stored time for this tool's draft, in this
   * mount: seeded from a mount-time restore if one happened, then
   * advanced by every successful autosave after. Null once there is no
   * stored draft (fresh start, or after clearDraft()). */
  draftSavedAt: string | null;
  /** "Discard this restored draft": reverts the form back to `baseline`
   * and deletes the stored draft. Wire to the restored-draft banner's
   * discard action. */
  discardDraft: () => void;
  /** "This typing is now a real artifact": deletes the stored draft
   * without touching form state (the just-saved state is the new
   * baseline going forward; the caller's own load/reload effect is what
   * actually advances `baseline`). Call from a successful save. */
  clearDraft: () => void;
}

/** Formats an ISO timestamp as "HH:MM"-ish local time -- what a "draft
 * stored" notice reads. Shared by TopBar.tsx and any tool form's own
 * restored-draft banner so the two never disagree on format. */
export function formatDraftTime(iso: string): string {
  return new Date(iso).toLocaleTimeString(undefined, { hour: "numeric", minute: "2-digit" });
}

/** Structural equality for the plain JSON-shaped objects form state is
 * made of. Not a general-purpose deep-equal (no Date/Map/Set handling) --
 * a draft's payload (drafts.py's opaque `Any`) is always exactly what
 * JSON.stringify can already round-trip, and key order is not meaningful
 * (the engine's own store rewrites it sorted; see drafts.py), so a plain
 * `JSON.stringify(a) === JSON.stringify(b)` would false-positive on
 * "differs" for two objects with the same keys written in different
 * orders. */
function deepEqual(a: unknown, b: unknown): boolean {
  if (a === b) return true;
  if (typeof a !== "object" || typeof b !== "object" || a === null || b === null) return false;
  if (Array.isArray(a) || Array.isArray(b)) {
    if (!Array.isArray(a) || !Array.isArray(b) || a.length !== b.length) return false;
    return a.every((v, i) => deepEqual(v, b[i]));
  }
  const aRec = a as Record<string, unknown>;
  const bRec = b as Record<string, unknown>;
  const aKeys = Object.keys(aRec);
  const bKeys = Object.keys(bRec);
  return (
    aKeys.length === bKeys.length &&
    aKeys.every((k) => Object.prototype.hasOwnProperty.call(bRec, k) && deepEqual(aRec[k], bRec[k]))
  );
}

/** Per-tool draft autosave: restore-on-mount, debounced save, clear-on-save
 * (PLAN Phase 4.1). One call per mounted tool form -- CharterForm.tsx,
 * useA3Form.ts, and useFmeaForm.ts each own exactly one, keyed by that
 * tool's id.
 *
 * Owns the form's autosave *decision* (restore vs. not, save vs. not) by
 * comparing `state`/`baseline`, but never mutates the caller's state
 * except through the `setState` it was given, and never invents a shape
 * for the payload -- drafts.py's payload is opaque `Any` precisely so
 * this hook doesn't need to understand it, only compare and transport it.
 *
 * Also reports into SaveStateContext (guarded against a real save in
 * flight) so the top bar can say "draft stored HH:MM" without every form
 * having to wire that up itself.
 *
 * Restore and autosave are decided in ONE effect below, not two, on
 * purpose. Splitting "apply a restored draft" from "autosave on change"
 * into separate effects means the second can run, in the same commit,
 * before the first's setState has actually landed in `state` -- reading
 * a still-stale `state` and writing it right back as "the current draft,
 * saved just now," undoing the very restore that just happened. One
 * effect with an early return after applying a restore avoids that by
 * construction: the pass that restores never also evaluates autosave
 * against the pre-restore value.
 */
export function useToolDraft<T>(projectId: string, toolId: string, opts: UseToolDraftOptions<T>): UseToolDraftResult {
  const { baseline, state, setState } = opts;
  const { saveState, setSaveState, setDraftSavedAt: setSharedDraftSavedAt } = useSaveState();

  // Read inside async callbacks without a stale closure: those callbacks
  // are recreated per render, but the debounce timer's callback is not,
  // and needs the live value at the moment it actually fires.
  const saveStateRef = useRef(saveState);
  useEffect(() => {
    saveStateRef.current = saveState;
  }, [saveState]);

  const [storedDraft, setStoredDraft] = useState<StoredDraft<T> | null>(null);
  const [draftChecked, setDraftChecked] = useState(false);
  const [restoredAt, setRestoredAt] = useState<string | null>(null);
  const [draftSavedAt, setLocalDraftSavedAt] = useState<string | null>(null);

  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const pendingRef = useRef<T | undefined>(undefined);
  const hasPendingRef = useRef(false);
  const hydratedRef = useRef(false);

  // Mount-time GET: whatever this tool already had stored, if anything.
  useEffect(() => {
    let cancelled = false;
    loadDraft(projectId, toolId)
      .then((rec) => {
        if (cancelled || rec === null) return; // no draft for this tool -- the ordinary case
        setStoredDraft({ payload: rec.payload as T, updatedAt: rec.updated_at });
        setLocalDraftSavedAt(rec.updated_at);
        if (saveStateRef.current !== "saving") {
          setSaveState("draft");
          setSharedDraftSavedAt(rec.updated_at);
        }
      })
      .catch(() => {
        // 404 (no draft yet) is the common case here, not a failure; a
        // network/engine error degrades the same way -- either way there
        // is nothing to hand back, which is what the initial state
        // already says.
      })
      .finally(() => {
        if (!cancelled) setDraftChecked(true);
      });
    return () => {
      cancelled = true;
    };
    // setSaveState / setSharedDraftSavedAt are stable useState setters;
    // projectId/toolId are this effect's real inputs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, toolId]);

  const commit = useCallback(
    async (payload: T) => {
      try {
        const rec = await saveDraft(projectId, toolId, { updated_at: new Date().toISOString(), payload });
        setLocalDraftSavedAt(rec.updated_at);
        // A real save (handleSave in every *Form) sets "saving" for the
        // duration of its own request; an autosave landing in that
        // window must not flip the bar back to "draft" only to have the
        // real save's own "saved"/"error" land right after.
        if (saveStateRef.current !== "saving") {
          setSaveState("draft");
          setSharedDraftSavedAt(rec.updated_at);
        }
      } catch {
        // Best-effort: the next edit reschedules the same debounce and
        // tries again. A background autosave failing silently is correct
        // here -- surfacing it would mean interrupting someone's typing
        // to report on a save they never asked for.
      }
    },
    [projectId, toolId, setSaveState, setSharedDraftSavedAt],
  );

  const scheduleSave = useCallback(
    (payload: T) => {
      pendingRef.current = payload;
      hasPendingRef.current = true;
      if (timerRef.current != null) clearTimeout(timerRef.current);
      timerRef.current = setTimeout(() => {
        timerRef.current = null;
        hasPendingRef.current = false;
        void commit(pendingRef.current as T);
      }, DEBOUNCE_MS);
    },
    [commit],
  );

  // Flush on unmount. This is the exact bug report: typing gets lost by
  // *navigating away*, and navigating away is a tool form unmounting.
  // Without this, anything typed in the last 1.5s before the click would
  // be silently dropped along with the timer that was going to save it.
  useEffect(() => {
    return () => {
      if (timerRef.current != null) {
        clearTimeout(timerRef.current);
        timerRef.current = null;
        if (hasPendingRef.current) void commit(pendingRef.current as T);
      }
    };
  }, [commit]);

  // Restore-then-autosave, as one effect (see the function's doc comment
  // for why it must not be two).
  useEffect(() => {
    if (baseline === undefined || !draftChecked) return;

    if (!hydratedRef.current) {
      hydratedRef.current = true;
      // The `state === baseline` check guards a narrow race: if the user
      // already typed something before this mount-time check resolved,
      // `state` will have moved on from `baseline` by reference, and
      // their fresh typing wins over an old draft rather than being
      // silently overwritten by it.
      if (storedDraft && state === baseline && !deepEqual(storedDraft.payload, baseline)) {
        setState(storedDraft.payload);
        setRestoredAt(storedDraft.updatedAt);
        return; // `state` above is still pre-restore; the render this
        // setState produces re-enters this effect and correctly compares
        // the restored value against baseline then, not against itself.
      }
    }

    if (deepEqual(state, baseline)) return; // nothing beyond the saved/loaded truth -- no draft-worthy edit exists
    scheduleSave(state);
  }, [state, baseline, draftChecked, storedDraft, scheduleSave, setState]);

  const wipeLocalDraftState = useCallback(() => {
    if (timerRef.current != null) {
      clearTimeout(timerRef.current);
      timerRef.current = null;
    }
    hasPendingRef.current = false;
    pendingRef.current = undefined;
    setStoredDraft(null);
    setRestoredAt(null);
    setLocalDraftSavedAt(null);
    if (saveStateRef.current === "draft") {
      setSaveState("idle");
      setSharedDraftSavedAt(null);
    }
  }, [setSaveState, setSharedDraftSavedAt]);

  const clearDraft = useCallback(() => {
    wipeLocalDraftState();
    void deleteDraft(projectId, toolId).catch(() => {
      // Idempotent and advisory (drafts.py's delete_draft docstring): a
      // failed delete just leaves an inert file behind, never a reason
      // to tell the user their real save (or their discard click) failed.
    });
  }, [projectId, toolId, wipeLocalDraftState]);

  const discardDraft = useCallback(() => {
    if (baseline !== undefined) setState(baseline);
    clearDraft();
  }, [baseline, setState, clearDraft]);

  return { restoredAt, draftSavedAt, discardDraft, clearDraft };
}
