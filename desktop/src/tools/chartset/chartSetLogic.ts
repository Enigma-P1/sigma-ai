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
