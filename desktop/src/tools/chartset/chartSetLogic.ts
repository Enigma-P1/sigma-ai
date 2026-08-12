import type { BoxGroup } from "../../charts";
import type { ColumnInfo, DatasetMeta } from "../../api/types";

export function numericColumns(meta: DatasetMeta): ColumnInfo[] {
  return meta.columns.filter((c) => c.type === "numeric");
}

export function textColumns(meta: DatasetMeta): ColumnInfo[] {
  return meta.columns.filter((c) => c.type === "text");
}

/** Raw column values as stored — reading them back out is data plumbing,
 * not a computed statistic (the actual statistics shown in a chart
 * headline still come from /stats/descriptive or /stats/pareto). */
export function numericColumnValues(rows: Record<string, string>[], column: string): number[] {
  return rows.map((r) => Number(r[column])).filter((n) => Number.isFinite(n));
}

export function textColumnValues(rows: Record<string, string>[], column: string): string[] {
  return rows.map((r) => r[column] ?? "").filter((v) => v.trim() !== "");
}

export function buildBoxGroups(rows: Record<string, string>[], groupColumn: string, valueColumn: string): BoxGroup[] {
  const byLabel = new Map<string, number[]>();
  for (const row of rows) {
    const label = row[groupColumn] ?? "";
    const value = Number(row[valueColumn]);
    if (label.trim() === "" || !Number.isFinite(value)) continue;
    const existing = byLabel.get(label);
    if (existing) existing.push(value);
    else byLabel.set(label, [value]);
  }
  return Array.from(byLabel.entries()).map(([label, values]) => ({ label, values }));
}

/** Picks the column a picker should show selected right after a dataset
 * (re)loads: `preferred` (a remembered choice from chartSetViewStore.ts,
 * or the panel's own prior selection) if it is still a real column on
 * THIS dataset, else `fallback` if that is real, else the first column
 * available. One rule shared by every panel so "restore the saved view"
 * and "the previous dataset's column doesn't exist here" (switching
 * datasets mid-session) collapse into the same code path instead of five
 * slightly different ones. */
export function resolveColumn(preferred: string | undefined, columns: ColumnInfo[], fallback?: string): string {
  if (preferred && columns.some((c) => c.name === preferred)) return preferred;
  if (fallback && columns.some((c) => c.name === fallback)) return fallback;
  return columns[0]?.name ?? "";
}

export interface ColumnValueCount {
  value: string;
  count: number;
}

/** Every distinct, non-blank value a column takes across `rows`, with how
 * many rows carry it -- the pick-list for the chart screen's filter (PLAN
 * 2.5). Sorted with `numeric: true` so aisle "3", "7", "12" reads in
 * count order rather than lexicographic ("12", "19", "3", "7"). */
export function distinctColumnValues(rows: Record<string, string>[], column: string): ColumnValueCount[] {
  const counts = new Map<string, number>();
  for (const row of rows) {
    const value = (row[column] ?? "").trim();
    if (value === "") continue;
    counts.set(value, (counts.get(value) ?? 0) + 1);
  }
  return [...counts.entries()]
    .map(([value, count]) => ({ value, count }))
    .sort((a, b) => a.value.localeCompare(b.value, undefined, { numeric: true, sensitivity: "base" }));
}

/** Rows whose `column` value is one of `values` -- the one filter every
 * chart on the screen recomputes over (PLAN 2.5). An empty column or an
 * empty value set means "no filter yet," not "match nothing": landing on
 * the column picker must never blank out every chart before a value is
 * actually chosen. */
export function applyRowFilter(
  rows: Record<string, string>[],
  column: string,
  values: string[],
): Record<string, string>[] {
  if (!column || values.length === 0) return rows;
  const wanted = new Set(values);
  return rows.filter((row) => wanted.has((row[column] ?? "").trim()));
}
