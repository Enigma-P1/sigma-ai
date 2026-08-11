import type { ClipboardEvent, KeyboardEvent } from "react";
import { cellKey, setCell } from "./gageRrLogic";
import type { GridValue } from "./gageRrLogic";

export interface GageRrGridProps {
  grid: GridValue;
  onChange: (grid: GridValue) => void;
}

const inputId = (p: number, o: number, t: number) => `grr-cell-${p}-${o}-${t}`;

/** The readings grid: operators down the page, trials within operator,
 * parts across the top — the layout of the paper form, so someone
 * transcribing from one doesn't have to transpose in their head.
 *
 * TWO THINGS MAKE THIS USABLE AT 90 CELLS, and without them the tool is
 * technically complete and practically unusable:
 *
 * ARROW KEYS AND ENTER move between cells, because a grid where the only
 * navigation is Tab forces the operator to count columns to get back to
 * where they were.
 *
 * PASTE FILLS A BLOCK. This data almost always already exists in a
 * spreadsheet. Pasting a rectangle of tab-separated values at the focused
 * cell fills right across parts and down through trials and operators,
 * which is the difference between one paste and ninety keystrokes.
 */
export function GageRrGrid({ grid, onChange }: GageRrGridProps) {
  const { parts, operators, trials } = grid;

  function focusCell(p: number, o: number, t: number) {
    document.getElementById(inputId(p, o, t))?.focus();
  }

  /** Vertical neighbours run trial-then-operator: down the last trial of
   * operator A lands on trial 1 of operator B, which is what the eye does
   * reading the column. */
  function step(p: number, o: number, t: number, dx: number, dy: number) {
    let part = p + dx;
    if (part < 0 || part >= parts.length) part = p;
    let flat = o * trials + t + dy;
    if (flat < 0) flat = 0;
    if (flat >= operators.length * trials) flat = operators.length * trials - 1;
    focusCell(part, Math.floor(flat / trials), flat % trials);
  }

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>, p: number, o: number, t: number) {
    if (e.key === "ArrowDown" || e.key === "Enter") {
      e.preventDefault();
      step(p, o, t, 0, 1);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      step(p, o, t, 0, -1);
    } else if (e.key === "ArrowRight" && e.currentTarget.selectionStart === e.currentTarget.value.length) {
      // Only when the caret is already at the end -- otherwise arrow keys
      // could not be used to edit the number in the cell.
      e.preventDefault();
      step(p, o, t, 1, 0);
    } else if (e.key === "ArrowLeft" && e.currentTarget.selectionStart === 0) {
      e.preventDefault();
      step(p, o, t, -1, 0);
    }
  }

  function onPaste(e: ClipboardEvent<HTMLInputElement>, p: number, o: number, t: number) {
    const text = e.clipboardData.getData("text/plain");
    if (!text || !/[\t\n\r]/.test(text)) return; // a single value pastes normally
    e.preventDefault();
    const rows = text.replace(/\r\n?/g, "\n").replace(/\n$/, "").split("\n");
    let next = grid;
    const startFlat = o * trials + t;
    rows.forEach((row, dy) => {
      const flat = startFlat + dy;
      if (flat >= operators.length * trials) return;
      row.split("\t").forEach((cell, dx) => {
        const part = p + dx;
        if (part >= parts.length) return;
        next = setCell(next, part, Math.floor(flat / trials), flat % trials, cell.trim());
      });
    });
    onChange(next);
  }

  function renameOperator(index: number, label: string) {
    const nextOperators = [...operators];
    nextOperators[index] = label;
    onChange({ ...grid, operators: nextOperators });
  }

  function renamePart(index: number, label: string) {
    const nextParts = [...parts];
    nextParts[index] = label;
    onChange({ ...grid, parts: nextParts });
  }

  return (
    <div className="sigma-grr-grid-scroll">
      <table className="sigma-grr-grid" data-testid="grr-grid">
        <thead>
          <tr>
            <th scope="col" className="sigma-grr-grid__corner">
              Operator
            </th>
            <th scope="col" className="sigma-grr-grid__corner">
              Trial
            </th>
            {parts.map((label, p) => (
              <th key={p} scope="col">
                <input
                  className="sigma-grr-grid__label"
                  data-testid={`grr-part-label-${p}`}
                  aria-label={`Part ${p + 1} name`}
                  value={label}
                  onChange={(e) => renamePart(p, e.target.value)}
                />
              </th>
            ))}
          </tr>
        </thead>
        {operators.map((operator, o) => (
          <tbody key={o} data-testid={`grr-operator-block-${o}`}>
            {Array.from({ length: trials }, (_, t) => (
              <tr key={t}>
                {t === 0 && (
                  <th scope="rowgroup" rowSpan={trials} className="sigma-grr-grid__operator">
                    <input
                      className="sigma-grr-grid__label"
                      data-testid={`grr-operator-label-${o}`}
                      aria-label={`Operator ${o + 1} name`}
                      value={operator}
                      onChange={(e) => renameOperator(o, e.target.value)}
                    />
                  </th>
                )}
                <th scope="row" className="sigma-grr-grid__trial">
                  {t + 1}
                </th>
                {parts.map((_, p) => (
                  <td key={p}>
                    <input
                      id={inputId(p, o, t)}
                      className="sigma-grr-grid__cell"
                      data-testid={`grr-cell-${p}-${o}-${t}`}
                      aria-label={`Part ${parts[p]}, operator ${operator}, trial ${t + 1}`}
                      inputMode="decimal"
                      value={grid.cells[cellKey(p, o, t)] ?? ""}
                      onChange={(e) => onChange(setCell(grid, p, o, t, e.target.value))}
                      onKeyDown={(e) => onKeyDown(e, p, o, t)}
                      onPaste={(e) => onPaste(e, p, o, t)}
                    />
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        ))}
      </table>
    </div>
  );
}
