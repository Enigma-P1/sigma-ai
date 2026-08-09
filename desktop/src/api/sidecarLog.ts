/** Thin wrappers over the two Rust sidecar-log commands (see
 * desktop/src-tauri/src/lib.rs). Only meaningful inside the Tauri runtime;
 * in browser/dev mode there is no sidecar and no Rust to invoke, so both
 * return "" without ever calling `invoke` (which would throw with no
 * __TAURI_INTERNALS__). Every call is additionally try/caught so a missing
 * command or IPC error degrades to "" rather than surfacing an exception. */
import { invoke } from "@tauri-apps/api/core";
import { isTauriRuntime } from "./runtime";

/** Absolute path of the sidecar log file, for showing the user where to look
 * when the engine doesn't come up. "" outside Tauri or on any error. */
export async function getSidecarLogPath(): Promise<string> {
  if (!isTauriRuntime()) return "";
  try {
    return await invoke<string>("sidecar_log_path");
  } catch {
    return "";
  }
}

/** Last ~4000 chars of the sidecar log, for showing the failure reason
 * inline. "" outside Tauri or on any error. */
export async function getSidecarLogTail(): Promise<string> {
  if (!isTauriRuntime()) return "";
  try {
    return await invoke<string>("sidecar_log_tail");
  } catch {
    return "";
  }
}
