/** Chart capture for report export.
 *
 * WHY THIS IS TINY: every Plotly chart in the app renders through one
 * component (PlotlyChart.tsx, via ChartFrame), so registering the plot
 * element in one place makes all eight chart types capturable at once —
 * histogram, run, Pareto, scatter, box, I-MR, p-chart, 5S trend. The three
 * hand-drawn canvases are Konva Stages, which expose `.toDataURL()`
 * themselves and register through the same map.
 *
 * WHY THE HASH: the engine puts this image in a PDF whose footer says the
 * engine produced it. If the picture were captured from data that has since
 * changed, the page would carry a chart and a verdict that disagree, under
 * a signature implying they don't. So a capture is submitted with the
 * fingerprint of the series it was drawn from, and the engine refuses any
 * image whose fingerprint doesn't match the data it is rendering
 * (export/report_pdf.py check_chart). Fingerprints must be computed the
 * same way on both sides — see fingerprint() below and its Python twin
 * `data_fingerprint`.
 */

export interface Capture {
  png_base64: string;
  data_hash: string | null;
}

type Capturer = () => Promise<string | null>;

const registry = new Map<string, { capture: Capturer; hash: string | null }>();

/** Registered by the chart components themselves on mount. `key` names the
 * chart, not the tool — a tool can own more than one. */
export function registerChart(key: string, capture: Capturer, hash: string | null): () => void {
  registry.set(key, { capture, hash });
  return () => {
    // Only drop the entry if it is still ours: a remount registers the new
    // capturer before the old effect's cleanup runs, and an unconditional
    // delete would unregister the live chart and silently break export.
    const current = registry.get(key);
    if (current && current.capture === capture) registry.delete(key);
  };
}

export function hasChart(key: string): boolean {
  return registry.has(key);
}

/** Returns null when the chart was never mounted (the user has not opened
 * that screen). Callers must treat null as "no picture", never as an error
 * — the report still renders, saying why the chart is absent. */
export async function captureChart(key: string): Promise<Capture | null> {
  const entry = registry.get(key);
  if (!entry) return null;
  try {
    const dataUrl = await entry.capture();
    if (!dataUrl) return null;
    const comma = dataUrl.indexOf(",");
    return {
      png_base64: comma >= 0 ? dataUrl.slice(comma + 1) : dataUrl,
      data_hash: entry.hash,
    };
  } catch {
    return null; // a failed capture costs the picture, never the report
  }
}

/** The fingerprint both sides compute over the data behind a chart.
 *
 * MUST match engine `export/report_pdf.py::data_fingerprint`, which hashes
 * `json.dumps(list(values), separators=(",", ":"), sort_keys=True)`. That is
 * byte-identical to `JSON.stringify` for an array of numbers, with one
 * exception that matters: Python renders a whole float as `5.0` where
 * JavaScript renders `5`. The ENGINE normalises for it (whole floats are
 * emitted as ints there), so this side is plain JSON.stringify and the two
 * agree. test_report_pdf.py pins the equivalence by hashing the same list in
 * both languages — without that test the mismatch is invisible until a
 * dataset happens to contain a round number and the chart quietly vanishes.
 */
export async function fingerprint(values: readonly number[]): Promise<string> {
  const payload = JSON.stringify(values);
  const bytes = new TextEncoder().encode(payload);
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("");
}


/** The screen-side twin of report capture: the same registered capturer,
 * saved straight to the user as a file with a real name -- because the one
 * artifact either UAT tester actually shared was a chart, and the only
 * route was a hover toolbar producing "newplot.png". */
export async function downloadChartPng(key: string, filename: string): Promise<boolean> {
  const capture = await captureChart(key);
  if (!capture) return false;
  const bytes = atob(capture.png_base64);
  const buf = new Uint8Array(bytes.length);
  for (let i = 0; i < bytes.length; i++) buf[i] = bytes.charCodeAt(i);
  const { saveBlob } = await import("../api/saveBlob");
  saveBlob(new Blob([buf], { type: "image/png" }), filename);
  return true;
}
