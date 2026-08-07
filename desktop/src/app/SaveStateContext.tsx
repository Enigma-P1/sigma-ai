import { createContext, useContext, useMemo, useState } from "react";
import type { ReactNode } from "react";

export type SaveState = "idle" | "saving" | "saved" | "error";

interface SaveStateContextValue {
  saveState: SaveState;
  setSaveState: (s: SaveState) => void;
}

const SaveStateContext = createContext<SaveStateContextValue | null>(null);

/** Lets any tool screen report its save-in-progress state up to the
 * TopBar (M1 brief: "top bar = project name + phase + save state") without
 * threading callbacks through every layer of the tree. */
export function SaveStateProvider({ children }: { children: ReactNode }) {
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const value = useMemo(() => ({ saveState, setSaveState }), [saveState]);
  return <SaveStateContext.Provider value={value}>{children}</SaveStateContext.Provider>;
}

export function useSaveState(): SaveStateContextValue {
  const ctx = useContext(SaveStateContext);
  if (!ctx) throw new Error("useSaveState must be used within a SaveStateProvider");
  return ctx;
}
