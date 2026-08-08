import type { CheckSheetArtifact, CheckSheetCategory, CheckSheetEntry, StrataFieldDef } from "../../api/types";

let counter = 0;
/** Same counter-based id scheme as processMapLogic.ts's genId -- unique
 * for a session, not persisted identity. */
export function genId(prefix: string): string {
  counter += 1;
  return `${prefix}-${Date.now().toString(36)}-${counter}`;
}

export function emptyCategory(index: number): CheckSheetCategory {
  return { category_id: genId("cat"), label: `Category ${index + 1}` };
}

export function emptyStrataField(index: number): StrataFieldDef {
  return { key: genId("field"), label: `Field ${index + 1}` };
}

export function canSaveCheckSheet(categories: CheckSheetCategory[]): boolean {
  return categories.length > 0 && categories.every((c) => c.label.trim() !== "");
}

/** Client-side display tally only -- a plain count of already-loaded
 * entries, the same "not a computed result" distinction processMapLogic's
 * wasteTally draws (no provenance, nothing the engine needs to stamp).
 * The graded Pareto counts always come from /stats/pareto after
 * to_dataset, never from this. */
export function tallyCounts(entries: CheckSheetEntry[]): Record<string, number> {
  const out: Record<string, number> = {};
  for (const e of entries) out[e.category_id] = (out[e.category_id] ?? 0) + 1;
  return out;
}

export function makeTallyEntry(categoryId: string, strata: Record<string, string>): CheckSheetEntry {
  const activeOnly = Object.fromEntries(Object.entries(strata).filter(([, v]) => v.trim() !== ""));
  return { entry_id: genId("entry"), category_id: categoryId, timestamp: new Date().toISOString(), strata: activeOnly, note: "" };
}

export function buildCheckSheetBody(input: {
  artifactId: string;
  schemaVersion: number;
  categories: CheckSheetCategory[];
  strataFields: StrataFieldDef[];
  entries: CheckSheetEntry[];
}): Record<string, unknown> {
  const now = new Date().toISOString();
  return {
    schema_version: input.schemaVersion,
    artifact_id: input.artifactId,
    tool_id: "T-08",
    created_at: now,
    updated_at: now,
    categories: input.categories,
    strata_fields: input.strataFields,
    entries: input.entries,
  };
}

export function checkSheetStateFromArtifact(artifact: CheckSheetArtifact): {
  categories: CheckSheetCategory[];
  strataFields: StrataFieldDef[];
  entries: CheckSheetEntry[];
} {
  return { categories: artifact.categories, strataFields: artifact.strata_fields, entries: artifact.entries };
}

/** Removing a category cascades to its entries -- an entry referencing a
 * removed category_id would fail the engine's referential-integrity check
 * on save (same reasoning as useProcessMapForm.removeLane's doomedSteps). */
export function removeCategoryCascade(categories: CheckSheetCategory[], entries: CheckSheetEntry[], categoryId: string) {
  return {
    categories: categories.filter((c) => c.category_id !== categoryId),
    entries: entries.filter((e) => e.category_id !== categoryId),
  };
}

/** Removing a strata field strips that key from every entry rather than
 * leaving an "undeclared strata key" the engine would reject on save. */
export function removeStrataFieldCascade(strataFields: StrataFieldDef[], entries: CheckSheetEntry[], key: string) {
  return {
    strataFields: strataFields.filter((f) => f.key !== key),
    entries: entries.map((e) => {
      if (!(key in e.strata)) return e;
      const next = { ...e.strata };
      delete next[key];
      return { ...e, strata: next };
    }),
  };
}

/** Every value a strata field could be toggled to: values already used on
 * some entry, plus any added-but-not-yet-tapped manual options. */
export function deriveStrataOptions(
  strataFields: StrataFieldDef[], entries: CheckSheetEntry[], manualOptions: Record<string, string[]>,
): Record<string, string[]> {
  const out: Record<string, string[]> = {};
  for (const f of strataFields) {
    const fromEntries = entries.map((e) => e.strata[f.key]).filter((v): v is string => Boolean(v));
    out[f.key] = Array.from(new Set([...(manualOptions[f.key] ?? []), ...fromEntries]));
  }
  return out;
}
