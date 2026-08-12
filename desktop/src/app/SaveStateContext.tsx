import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

// "draft" added alongside idle/saving/saved/error (PLAN Phase 4.2): before
// drafts existed, idle was the only truthful thing to say about unsaved
// typing -- it knew nothing had been saved and nothing more. Now that
// useToolDraft.ts autosaves in-progress typing, there is a real signal to
// report: not "saved" (no artifact exists yet, or the form doesn't pass
// its required-field gate), but not blind either.
export type SaveState = "idle" | "saving" | "saved" | "error" | "draft";

interface SaveStateContextValue {
  saveState: SaveState;
  setSaveState: (s: SaveState) => void;
  /** ISO timestamp of the most recent draft autosave reported by whichever
   * tool is mounted right now (useToolDraft.ts). Meaningful only when
   * saveState is "draft" -- TopBar reads it to render "Draft stored HH:MM"
   * rather than a bare label. Never set to a value nothing actually wrote:
   * useToolDraft only calls setDraftSavedAt alongside setSaveState("draft"),
   * so the two always change together. */
  draftSavedAt: string | null;
  setDraftSavedAt: (iso: string | null) => void;
}

const SaveStateContext = createContext<SaveStateContextValue | null>(null);

/** Lets any tool screen report its save-in-progress state up to the
 * TopBar (M1 brief: "top bar = project name + phase + save state") without
 * threading callbacks through every layer of the tree. */
export function SaveStateProvider({ children }: { children: ReactNode }) {
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [draftSavedAt, setDraftSavedAt] = useState<string | null>(null);
  const value = useMemo(
    () => ({ saveState, setSaveState, draftSavedAt, setDraftSavedAt }),
    [saveState, draftSavedAt],
  );
  return <SaveStateContext.Provider value={value}>{children}</SaveStateContext.Provider>;
}

export function useSaveState(): SaveStateContextValue {
  const ctx = useContext(SaveStateContext);
  if (!ctx) throw new Error("useSaveState must be used within a SaveStateProvider");
  return ctx;
}
