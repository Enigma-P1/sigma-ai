import { useEffect, useState } from "react";
import { getDataset } from "../../api/client";
import { ApiError } from "../../api/errors";
import { Button, Panel, VerdictBanner } from "../../design/components";
import type { DatasetDetail } from "../../api/types";
import { numericColumnTotals } from "./dataImportLogic";

export interface DatasetRowsViewProps {
  projectId: string;
  datasetId: string;
  onClose: () => void;
}

const PAGE_SIZE = 50;

/** T-11's sharpest UAT finding, answered directly (docs/uat/README.md):
 * "the app never once showed either of them their own rows" -- a
 * supervisor could not confirm his own credit-amount total imported
 * correctly, because no total and no rows were ever shown, only five
 * sample values per column. This fetches the one saved dataset's full row
 * set (routes/datasets.py's GET .../datasets/{id} -- there is no
 * row-paging endpoint, it returns everything already) and pages it
 * client-side; PAGE_SIZE caps how much hits the DOM at once, not a second
 * network round trip. Read-only: editing a saved dataset is a separate,
 * later piece of work and replaces nothing here. */
export function DatasetRowsView({ projectId, datasetId, onClose }: DatasetRowsViewProps) {
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState(0);

  useEffect(() => {
    setDetail(null);
    setError(null);
    setPage(0);
    setLoading(true);
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

  const title = detail ? `Rows — ${detail.meta.source_filename}` : "Dataset rows";
  const hideButton = (
    <Button variant="ghost" size="sm" onClick={onClose} data-testid="dataimport-rows-hide">
      Hide rows
    </Button>
  );

  return (
    <div className="sigma-dataimport__rows-panel" data-testid="dataimport-rows-view">
      <Panel title={title} right={hideButton}>
        {loading && <p className="sigma-dataimport__status" data-testid="dataimport-rows-loading">Loading rows…</p>}
        {error && <VerdictBanner tone="fail" headline={error} />}

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

            <div className="sigma-dataimport__table-wrap" data-testid="dataimport-rows-table">
              <table className="sigma-dataimport__table">
                <thead>
                  <tr>
                    <th>#</th>
                    {columns.map((c) => (
                      <th key={c.name}>{c.name}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {pageRows.map((row, i) => (
                    <tr key={start + i}>
                      <td>{start + i + 1}</td>
                      {columns.map((c) => (
                        <td key={c.name}>{row[c.name] || "—"}</td>
                      ))}
                    </tr>
                  ))}
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
