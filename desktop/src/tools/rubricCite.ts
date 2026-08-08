/** Pulls an embedded rubric-code citation (R-XXX-NN, e.g. "R-DEF-05") out
 * of a helper-panel or body-text string, so the text a user actually reads
 * stays free of internal rubric jargon (Jordan usability fix) while the
 * code itself survives as a `title` tooltip -- removed from the visible
 * screen, never silently dropped. Used by HelperFrame.tsx (every "good"/
 * "bad" example, "what good looks like" bullet, common mistake, and the
 * source citation) and DeleteReasonModal.tsx.
 *
 * Handles the two shapes this codebase's content actually uses: a
 * trailing "Acceptance checklist: rubric R-XXX-NN[, ...]." sentence (every
 * *Content.ts `source` field ends this way), and a bare code sitting
 * inside a parenthetical aside or a short "in rubric R-XXX-NN" clause
 * elsewhere in the prose. */

const CODE = "R-[A-Z]{3,4}-\\d{2}";
const CODE_RE = new RegExp(CODE, "g");
const TRAILING_CHECKLIST_RE = new RegExp(`\\s*Acceptance checklist:\\s*([^]*?)\\.?\\s*$`);
const PARENTHETICAL_WITH_CODE_RE = new RegExp(`\\s?\\([^()]*${CODE}[^()]*\\)\\.?`, "g");
const IN_RUBRIC_RE = new RegExp(`\\s*(?:in )?rubric\\s+${CODE}`, "gi");

export interface CiteSplit {
  /** The text to actually render -- rubric codes removed. */
  text: string;
  /** The removed code(s), comma-joined, or null if none were found --
   * pass straight through as a `title` attribute. */
  cite: string | null;
}

export function splitCite(raw: string): CiteSplit {
  let text = raw;
  const cites: string[] = [];

  const trailing = text.match(TRAILING_CHECKLIST_RE);
  if (trailing) {
    const found = trailing[1].match(CODE_RE);
    if (found) cites.push(...found);
    text = text.slice(0, trailing.index).trimEnd();
  }

  text = text.replace(PARENTHETICAL_WITH_CODE_RE, (m) => {
    const found = m.match(CODE_RE);
    if (found) cites.push(...found);
    return "";
  });

  text = text.replace(IN_RUBRIC_RE, (m) => {
    const found = m.match(CODE_RE);
    if (found) cites.push(...found);
    return "";
  });

  text = text.replace(CODE_RE, (m) => {
    cites.push(m);
    return "";
  });

  text = text
    .replace(/\s{2,}/g, " ")
    .replace(/\s+([.,;:)])/g, "$1")
    .replace(/\(\s*\)/g, "")
    .trim();

  return { text, cite: cites.length > 0 ? Array.from(new Set(cites)).join(", ") : null };
}
