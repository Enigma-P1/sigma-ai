import { useMemo, useState } from "react";
import { Modal, TextInput } from "../design/components";
import { GLOSSARY } from "./glossary";
import "./GlossaryButton.css";

/** "What does that word mean" — reachable from every screen.
 *
 * The right fix for jargon is to explain each term where it appears, and
 * several screens already do that well in their "How this tool works"
 * panels. What neither tester had was anywhere to look when a word arrived
 * without one -- and one of them met nineteen such words. This is that
 * place: one list, plain language, searchable, always one click away.
 *
 * It deliberately does NOT gate anything. Nobody should have to open a
 * glossary to use a tool; this is for the moment they want to, which is
 * usually just before they decide the software is not for them.
 */
export function GlossaryButton() {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");

  const matches = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return GLOSSARY;
    return GLOSSARY.filter(
      (e) => e.term.toLowerCase().includes(q) || e.short.toLowerCase().includes(q) || (e.where ?? "").toLowerCase().includes(q),
    );
  }, [query]);

  return (
    <>
      <button
        type="button"
        className="sigma-topbar__link"
        onClick={() => setOpen(true)}
        title="Plain-English meanings for the terms this app uses"
        data-testid="topbar-glossary"
      >
        What does that mean?
      </button>
      {open && (
        <Modal title="What does that mean?" onClose={() => setOpen(false)}>
          <p className="sigma-glossary__intro">
            Plain meanings for the words this app uses. You don't need any of them to use the tools — this is
            here for when one gets in your way.
          </p>
          <TextInput
            id="glossary-search"
            data-testid="glossary-search"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search — e.g. Cpk, vital few, DMAIC"
          />
          <dl className="sigma-glossary" data-testid="glossary-list">
            {matches.map((entry) => (
              <div key={entry.term} className="sigma-glossary__entry" data-testid={`glossary-entry-${entry.term}`}>
                <dt className="sigma-glossary__term">{entry.term}</dt>
                <dd className="sigma-glossary__def">
                  {entry.short}
                  {entry.where && <span className="sigma-glossary__where">You'll meet this on {entry.where}.</span>}
                </dd>
              </div>
            ))}
            {matches.length === 0 && (
              <p className="sigma-glossary__empty" data-testid="glossary-empty">
                Nothing here matches "{query}". If the app used a word and this list doesn't explain it, that's a
                gap worth reporting.
              </p>
            )}
          </dl>
        </Modal>
      )}
    </>
  );
}
