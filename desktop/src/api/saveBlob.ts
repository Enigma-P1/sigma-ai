/** Hand a fetched Blob to the user as a file.
 *
 * Extracted from CharterForm's inline copy when the whole-project export
 * arrived and needed the identical dance: object URL, synthetic anchor,
 * click, revoke. Two copies of this would drift, and the way it drifts is
 * a leaked object URL -- the revoke is the step that looks optional and
 * is not.
 *
 * The packaged app reaches this path too: a download inside the Tauri
 * webview is cancelled outright unless the window was built with a
 * download handler, which src-tauri/src/lib.rs sets via .on_download().
 * Without it this function appears to work and silently produces no file.
 */
export function saveBlob(blob: Blob, filename: string): void {
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(objectUrl);
}

/** A project name is free text and becomes a filename here, so the same
 * characters the engine strips server-side (routes/export.py
 * _safe_filename) get stripped client-side. Kept deliberately in sync with
 * it: the engine sets Content-Disposition, but `link.download` wins in
 * Chromium for same-origin blob URLs, so an unsanitised name here undoes
 * the server's care. */
export function safeFilename(name: string, fallback: string): string {
  const cleaned = Array.from(name)
    .map((c) => (/[a-zA-Z0-9 \-_]/.test(c) ? c : "-"))
    .join("")
    .trim()
    .split(/\s+/)
    .join("-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 60);
  return cleaned || fallback;
}
