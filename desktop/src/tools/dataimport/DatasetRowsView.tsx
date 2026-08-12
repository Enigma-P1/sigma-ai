import { useEffect, useMemo, useState } from "react";
import { deriveDataset, getDataset } from "../../api/client";
import { ApiError } from "../../api/errors";
import { Button, Panel, TextInput, VerdictBanner } from "../../design/components";
import { DERIVE_COLUMN_DEFAULT_SEPARATOR } from "../../api/types";
import type { CellEdit, DatasetDetail, DatasetMeta, Derivation } from "../../api/types";
import { derivationSummary, numericColumnTotals, repeatedHeaderRowIndices } from "./dataImportLogic";
import { DatasetQualityFindings } from "./DatasetQualityFindings";
import { RecodeControl } from "./RecodeControl";
import { AddRowForm } from "./AddRowForm";
import { DeriveColumnForm } from "./DeriveColumnForm";

export interface DatasetRowsViewProps {
  projectId: string;
  datasetId: string;
  onClose: () => void;
  /** Fires once with the freshly created DatasetMeta right after any
   * derivation succeeds. The parent owns which dataset id this view is
   * pointed at (the same "who owns viewingDatasetId" split as
   * useDataImportForm.ts's handleToggleRows) -- this view asks to switch by
   * calling back up, rather than tracking a second "which dataset am I
   * really showing" id locally that could drift from the parent's. The
   * parent is also the one that needs to know a new dataset now exists, so
   * its own "Previously imported" list picks it up. */
  onDerived: (meta: DatasetMeta) => void;
}

const PAGE_SIZE = 50;

type DeriveMode = "recode" | "edit_cells" | "add_row" | "delete_rows" | "derive_column";

const MODES: { id: DeriveMode; label: string }[] = [
  { id: "recode", label: "Recode" },
  { id: "edit_cells", label: "Edit cells" },
  { id: "add_row", label: "Add row" },
  { id: "delete_rows", label: "Delete rows" },
  { id: "derive_column", label: "Derive column" },
];

/** T-11's sharpest UAT finding, answered directly (docs/uat/README.md):
 * "the app never once showed either of them their own rows" -- a
 * supervisor could not confirm his own credit-amount total imported
 * correctly, because no total and no rows were ever shown, only five
 * sample values per column. This fetches the one saved dataset's full row
 * set (routes/datasets.py's GET .../datasets/{id} -- there is no
 * row-paging endpoint, it returns everything already) and pages it
 * client-side; PAGE_SIZE caps how much hits the DOM at once, not a second
 * network round trip.
 *
 * Also PLAN.md 1.2/1.3/1.4's five derivation controls, built onto this same
 * table: edit a cell, add a row, delete rows, recode a column's spellings,
 * and derive a new column from two existing ones. Every one of them POSTs
 * .../derive and gets back a NEW DatasetMeta -- never an in-place edit to
 * what is on screen (datasets.py module docstring: a chart computed last
 * week has to keep resolving to the exact bytes it was computed from). */
export function DatasetRowsView({ projectId, datasetId, onClose, onDerived }: DatasetRowsViewProps) {
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  const [mode, setMode] = useState<DeriveMode | null>(null);
  const [applying, setApplying] = useState(false);
  const [deriveError, setDeriveError] = useState<string | null>(null);
  // The result of the MOST RECENT successful derivation against whatever
  // dataset this view was showing -- survives the refetch that follows
  // switching to it (see the effect below), and is deliberately the only
  // piece of state that effect does NOT unconditionally clear.
  const [lastDerived, setLastDerived] = useState<DatasetMeta | null>(null);

  // -- edit_cells: pending, unsubmitted edits. An array of {row_index,
  // column, value}, not a Map<string,string> keyed by "row:col" -- column
  // names can contain anything, and this is the exact shape /derive wants
  // on submit, so there is nothing to encode or parse back out. --
  const [pendingEdits, setPendingEdits] = useState<CellEdit[]>([]);
  // -- delete_rows: absolute row indices checked for deletion. --
  const [selectedForDelete, setSelectedForDelete] = useState<Set<number>>(new Set());
  // -- add_row: one draft value per column. --
  const [addRowValues, setAddRowValues] = useState<Record<string, string>>({});
  // -- recode --
  const [recodeColumn, setRecodeColumn] = useState("");
  const [recodeSelected, setRecodeSelected] = useState<Set<string>>(new Set());
  const [recodeTarget, setRecodeTarget] = useState("");
  // -- derive_column --
  const [deriveNewName, setDeriveNewName] = useState("");
  const [deriveLeft, setDeriveLeft] = useState("");
  const [deriveRight, setDeriveRight] = useState("");
  const [deriveSeparator, setDeriveSeparator] = useState(DERIVE_COLUMN_DEFAULT_SEPARATOR);

  useEffect(() => {
    setDetail(null);
    setError(null);
    setPage(0);
    setLoading(true);
    // Switching which dataset this view shows invalidates every in-progress
    // draft below it -- a row index or a checked value from the PREVIOUS
    // dataset carried over silently would be a real correctness bug (e.g.
    // "delete row 4" applied to a dataset whose row 4 is a different
    // record). lastDerived is the one exception: if the id we're switching
    // TO is the dataset we ourselves just created, keep showing the banner
    // that explains it -- that is the derivation this whole screen is
    // mid-explaining, not a stale one from a different dataset.
    setMode(null);
    setDeriveError(null);
    setPendingEdits([]);
    setSelectedForDelete(new Set());
    setAddRowValues({});
    setRecodeColumn("");
    setRecodeSelected(new Set());
    setRecodeTarget("");
    setDeriveNewName("");
    setDeriveLeft("");
    setDeriveRight("");
    setDeriveSeparator(DERIVE_COLUMN_DEFAULT_SEPARATOR);
    setLastDerived((prev) => (prev && prev.dataset_id === datasetId ? prev : null));
    getDataset(projectId, datasetId)
      .then(setDetail)
      .catch((err) => setError(err instanceof ApiError ? err.message : "Could not load this dataset's rows."))
      .finally(() => setLoading(false));
  }, [projectId, datasetId]);

  const rows = detail?.rows ?? [];
  const columns = detail?.meta.columns ?? [];
  const totals = numericColumnTotals(columns, rows);
  const pageCount = Math.max(1, Math.ceil(rows.length / PAGE_SIZE));
  const clampedPage = Math.min(page, pageCount - 1);
  const start = clampedPage * PAGE_SIZE;
  const pageRows = rows.slice(start, start + PAGE_SIZE);

  // O(rows x columns), same cost class as the engine's own scan -- only
  // recomputed when the loaded dataset actually changes, not on every
  // keystroke in an unrelated form below. Reads straight off `detail`
  // (rather than the `columns`/`rows` locals derived from it) so the
  // dependency array is exactly what the calculation uses.
  const repeatedIndices = useMemo(() => (detail ? repeatedHeaderRowIndices(detail.meta.columns, detail.rows) : []), [detail]);

  function switchMode(next: DeriveMode) {
    setMode((cur) => (cur === next ? null : next));
    setDeriveError(null);
  }

  async function applyDerivation(derivation: Derivation) {
    setApplying(true);
    setDeriveError(null);
    try {
      const child = await deriveDataset(projectId, datasetId, { derivation, created_at: new Date().toISOString() });
      setLastDerived(child);
      setMode(null);
      setPendingEdits([]);
      setSelectedForDelete(new Set());
      setAddRowValues({});
      setRecodeColumn("");
      setRecodeSelected(new Set());
      setRecodeTarget("");
      onDerived(child);
    } catch (err) {
      setDeriveError(err instanceof ApiError ? err.message : "Could not apply that change.");
    } finally {
      setApplying(false);
    }
  }

  // -- edit_cells --
  function editedValue(rowIndex: number, column: string): string | undefined {
    return pendingEdits.find((e) => e.row_index === rowIndex && e.column === column)?.value;
  }
  function setEditedValue(rowIndex: number, column: string, value: string) {
    setPendingEdits((prev) => [...prev.filter((e) => !(e.row_index === rowIndex && e.column === column)), { row_index: rowIndex, column, value }]);
  }
  function submitEditCells() {
    if (pendingEdits.length === 0) return;
    void applyDerivation({ kind: "edit_cells", edits: pendingEdits });
  }

  // -- delete_rows --
  function toggleDeleteRow(rowIndex: number) {
    setSelectedForDelete((prev) => {
      const next = new Set(prev);
      if (next.has(rowIndex)) next.delete(rowIndex);
      else next.add(rowIndex);
      return next;
    });
  }
  function submitDeleteRows() {
    if (selectedForDelete.size === 0) return;
    void applyDerivation({ kind: "delete_rows", row_indices: [...selectedForDelete] });
  }

  // -- add_row --
  function submitAddRow() {
    void applyDerivation({ kind: "add_row", values: addRowValues });
  }

  // -- recode --
  function toggleRecodeValue(value: string) {
    setRecodeSelected((prev) => {
      const next = new Set(prev);
      if (next.has(value)) next.delete(value);
      else next.add(value);
      return next;
    });
  }
  function submitRecode() {
    if (!recodeColumn || recodeSelected.size === 0 || recodeTarget.trim() === "") return;
    const mapping: Record<string, string> = {};
    for (const v of recodeSelected) mapping[v] = recodeTarget;
    void applyDerivation({ kind: "recode", column: recodeColumn, mapping });
  }

  // -- derive_column --
  function submitDeriveColumn() {
    if (!deriveNewName.trim() || !deriveLeft || !deriveRight) return;
    void applyDerivation({
      kind: "derive_column",
      new_column_name: deriveNewName.trim(),
      left_column: deriveLeft,
      right_column: deriveRight,
      separator: deriveSeparator,
    });
  }

  // -- Quality findings "point at the fix" (docs/uat/README.md) --
  function fixNearDuplicate(column: string, variants: string[]) {
    setMode("recode");
    setDeriveError(null);
    setRecodeColumn(column);
    setRecodeSelected(new Set(variants));
    // The longest spelling is usually the most complete one ("J. Morales"
    // over "JM") -- a starting guess the user can still change, not a
    // silent decision (this screen's whole posture never makes one of
    // those): the target field stays a plain, editable text input.
    const longest = [...variants].sort((a, b) => b.length - a.length)[0] ?? "";
    setRecodeTarget(longest);
  }
  function fixRepeatedHeaderRows() {
    setMode("delete_rows");
    setDeriveError(null);
    setSelectedForDelete(new Set(repeatedIndices));
  }
  function fixMixedDateFormat() {
    setMode("edit_cells");
    setDeriveError(null);
  }

  const title = detail ? `Rows — ${detail.meta.source_filename}` : "Dataset rows";
  const subtitle = detail?.meta.derived_from_dataset_id
    ? `Derived from dataset ${detail.meta.derived_from_dataset_id.slice(0, 8)} — a new dataset, not an edit to it`
    : undefined;
  const hideButton = (
    <Button variant="ghost" size="sm" onClick={onClose} data-testid="dataimport-rows-hide">
      Hide rows
    </Button>
  );

  return (
    <div className="sigma-dataimport__rows-panel" data-testid="dataimport-rows-view">
      <Panel title={title} subtitle={subtitle} right={hideButton}>
        {loading && <p className="sigma-dataimport__status" data-testid="dataimport-rows-loading">Loading rows…</p>}
        {error && <VerdictBanner tone="fail" headline={error} />}

        {lastDerived && (
          <div data-testid="dataimport-derive-success">
            <VerdictBanner
              tone="pass"
              className="sigma-dataimport__derive-banner"
              headline={`Created a new dataset — ${lastDerived.row_count} row${lastDerived.row_count === 1 ? "" : "s"}, shown below`}
              detail={
                `The dataset you started from is untouched and still saved -- find it again from "Datasets saved in ` +
                `this project" below once you close this view. This one is derived from it: ${
                  lastDerived.derivation ? derivationSummary(lastDerived.derivation) : "a recorded change"
                }, kept as history, not applied in place.`
              }
              actions={
                <Button variant="ghost" size="sm" onClick={() => setLastDerived(null)} data-testid="dataimport-derive-dismiss">
                  Dismiss
                </Button>
              }
            />
          </div>
        )}

        {detail && (
          <>
            <div className="sigma-dataimport__rows-summary" data-testid="dataimport-rows-summary">
              <VerdictBanner
                tone="neutral"
                headline={`${detail.meta.row_count} row${detail.meta.row_count === 1 ? "" : "s"}`}
                detail={
                  totals.length > 0 ? (
                    <>
                      <ul className="sigma-dataimport__quality-list">
                        {totals.map((t) => (
                          <li key={t.column} data-testid={`dataimport-rows-total-${t.column}`}>
                            {t.column} total: {t.total.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                          </li>
                        ))}
                      </ul>
                      {/* An order number and a credit amount are both "numeric"
                        * to the type system, and only one of them has a
                        * meaningful sum -- "Order number total: 1,055,167" is
                        * a real number printed with exactly the authority of
                        * the one the user came to check. Nothing here can tell
                        * a measure from an identifier without guessing, and
                        * guessing wrong on someone's own data is worse than
                        * saying so. This screen's own rule: the scan names
                        * what it found, it never silently decides. */}
                      <p className="sigma-dataimport__totals-caveat" data-testid="dataimport-rows-totals-caveat">
                        Every numeric column is totalled. A total only means something for a column you
                        measure — summing an ID or a code gives a number, not a fact.
                      </p>
                    </>
                  ) : undefined
                }
              />
            </div>

            <DatasetQualityFindings
              quality={detail.meta.quality}
              onFixRepeatedHeader={fixRepeatedHeaderRows}
              onFixNearDuplicate={fixNearDuplicate}
              onFixMixedDateFormat={fixMixedDateFormat}
            />

            <div className="sigma-dataimport__mode-bar" role="tablist" aria-label="Fix this dataset" data-testid="dataimport-mode-bar">
              {MODES.map((m) => (
                <Button
                  key={m.id} type="button" role="tab" aria-selected={mode === m.id}
                  variant={mode === m.id ? "primary" : "secondary"} size="sm"
                  onClick={() => switchMode(m.id)} data-testid={`dataimport-mode-${m.id}`}
                >
                  {m.label}
                </Button>
              ))}
            </div>

            {deriveError && (
              <div data-testid="dataimport-derive-error">
                <VerdictBanner tone="fail" headline={deriveError} />
              </div>
            )}

            {mode === "recode" && (
              <RecodeControl
                columns={columns} rows={rows} column={recodeColumn} onColumnChange={(c) => { setRecodeColumn(c); setRecodeSelected(new Set()); setRecodeTarget(""); }}
                selected={recodeSelected} onToggleValue={toggleRecodeValue} target={recodeTarget} onTargetChange={setRecodeTarget}
                onApply={submitRecode} applying={applying}
              />
            )}
            {mode === "add_row" && (
              <AddRowForm
                columns={columns} values={addRowValues}
                onChange={(col, v) => setAddRowValues((prev) => ({ ...prev, [col]: v }))}
                onApply={submitAddRow} applying={applying}
              />
            )}
            {mode === "derive_column" && (
              <DeriveColumnForm
                columns={columns} newColumnName={deriveNewName} onNewColumnNameChange={setDeriveNewName}
                leftColumn={deriveLeft} onLeftColumnChange={setDeriveLeft}
                rightColumn={deriveRight} onRightColumnChange={setDeriveRight}
                separator={deriveSeparator} onSeparatorChange={setDeriveSeparator}
                onApply={submitDeriveColumn} applying={applying}
              />
            )}
            {mode === "edit_cells" && (
              <div className="sigma-dataimport__mode-actions" data-testid="dataimport-edit-cells-actions">
                <p className="sigma-dataimport__mode-helper">
                  Click into any cell below and type the corrected value. Nothing saves until you apply.
                </p>
                <span>{pendingEdits.length} cell edit{pendingEdits.length === 1 ? "" : "s"} pending</span>
                <Button variant="primary" size="sm" disabled={pendingEdits.length === 0 || applying} onClick={submitEditCells} data-testid="dataimport-edit-cells-apply">
                  {applying ? "Saving…" : `Apply ${pendingEdits.length} edit${pendingEdits.length === 1 ? "" : "s"} → new dataset`}
                </Button>
                {pendingEdits.length > 0 && (
                  <Button variant="ghost" size="sm" onClick={() => setPendingEdits([])} data-testid="dataimport-edit-cells-discard">
                    Discard
                  </Button>
                )}
              </div>
            )}
            {mode === "delete_rows" && (
              <div className="sigma-dataimport__mode-actions" data-testid="dataimport-delete-rows-actions">
                <p className="sigma-dataimport__mode-helper">Check off rows below, then delete them into a new dataset.</p>
                <span>{selectedForDelete.size} row{selectedForDelete.size === 1 ? "" : "s"} selected</span>
                <Button variant="danger" size="sm" disabled={selectedForDelete.size === 0 || applying} onClick={submitDeleteRows} data-testid="dataimport-delete-rows-apply">
                  {applying ? "Deleting…" : `Delete ${selectedForDelete.size} row${selectedForDelete.size === 1 ? "" : "s"} → new dataset`}
                </Button>
                {selectedForDelete.size > 0 && (
                  <Button variant="ghost" size="sm" onClick={() => setSelectedForDelete(new Set())} data-testid="dataimport-delete-rows-clear">
                    Clear selection
                  </Button>
                )}
              </div>
            )}

            <div className="sigma-dataimport__table-wrap" data-testid="dataimport-rows-table">
              <table className="sigma-dataimport__table">
                <thead>
                  <tr>
                    {mode === "delete_rows" && <th className="sigma-dataimport__select-cell" aria-label="Select for deletion"></th>}
                    <th>#</th>
                    {columns.map((c) => (
                      <th key={c.name}>{c.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pageRows.map((row, i) => {
                    const absoluteIndex = start + i;
                    return (
                      <tr key={absoluteIndex}>
                        {mode === "delete_rows" && (
                          <td className="sigma-dataimport__select-cell">
                            <input
                              type="checkbox" checked={selectedForDelete.has(absoluteIndex)}
                              onChange={() => toggleDeleteRow(absoluteIndex)}
                              data-testid={`dataimport-delete-select-${absoluteIndex}`}
                            />
                          </td>
                        )}
                        <td>{absoluteIndex + 1}</td>
                        {columns.map((c) => {
                          const original = row[c.name] ?? "";
                          const pending = editedValue(absoluteIndex, c.name);
                          if (mode === "edit_cells") {
                            return (
                              <td key={c.name}>
                                <TextInput
                                  className="sigma-dataimport__cell-input"
                                  value={pending ?? original}
                                  onChange={(e) => setEditedValue(absoluteIndex, c.name, e.target.value)}
                                  data-testid={`dataimport-cell-edit-${absoluteIndex}-${c.name}`}
                                />
                              </td>
                            );
                          }
                          return (
                            <td key={c.name} className={pending !== undefined ? "sigma-dataimport__cell--pending" : undefined} title={pending !== undefined ? "Edited, not yet applied" : undefined}>
                              {(pending ?? original) || "—"}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {pageCount > 1 && (
              <div className="sigma-dataimport__rows-pager">
                <Button
                  variant="ghost" size="sm" disabled={clampedPage === 0}
                  onClick={() => setPage(clampedPage - 1)} data-testid="dataimport-rows-prev"
                >
                  ← Prev
                </Button>
                <span data-testid="dataimport-rows-page-indicator">
                  Rows {start + 1}–{Math.min(start + PAGE_SIZE, rows.length)} of {rows.length} (page {clampedPage + 1} of {pageCount})
                </span>
                <Button
                  variant="ghost" size="sm" disabled={clampedPage >= pageCount - 1}
                  onClick={() => setPage(clampedPage + 1)} data-testid="dataimport-rows-next"
                >
                  Next →
                </Button>
              </div>
            )}
          </>
        )}
      </Panel>
    </div>
  );
}
