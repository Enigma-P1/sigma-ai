/** Lightweight, localStorage-backed persistence for T-14's chart-screen
 * selections -- same convention as ../../app/toolVisitedStore.ts (one JSON
 * blob per project, best-effort, never fatal if storage is unavailable).
 * Before this, closing and reopening the chart screen threw away the
 * dataset and every column choice; both UAT testers had to rebuild their
 * chart from scratch on every visit (docs/uat/PLAN.md 2.1 -- Dave: "Nothing
 * in the app stores 'the chart I made.'").
 *
 * The filter (PLAN 2.5) is deliberately NOT part of this. A subset that
 * silently reappeared days later, without the user re-choosing it, is
 * exactly the "lie waiting to be quoted" 2.5 itself warns about -- a fresh
 * visit always starts from the whole dataset.
 */

const KEY_PREFIX = "sigma-ai:chartset-view:";

export interface ChartSetView {
  datasetId?: string;
  paretoColumn?: string;
  histogramColumn?: string;
  histogramUsl?: string;
  histogramLsl?: string;
  runChartColumn?: string;
  scatterX?: string;
  scatterY?: string;
  boxValueColumn?: string;
  boxGroupColumn?: string;
}

function storageKey(projectId: string): string {
  return `${KEY_PREFIX}${projectId}`;
}

export function loadChartSetView(projectId: string): ChartSetView {
  try {
    const raw = localStorage.getItem(storageKey(projectId));
    return raw ? (JSON.parse(raw) as ChartSetView) : {};
  } catch {
    return {};
  }
}

/** Read-modify-write so one panel's save can never clobber another's --
 * five independent panels (plus the screen itself, for the dataset) each
 * patch only the field(s) they own. */
export function saveChartSetView(projectId: string, patch: ChartSetView): void {
  try {
    const next = { ...loadChartSetView(projectId), ...patch };
    localStorage.setItem(storageKey(projectId), JSON.stringify(next));
  } catch {
    /* localStorage unavailable (private mode, etc.) -- selections just won't stick locally; not fatal */
  }
}
