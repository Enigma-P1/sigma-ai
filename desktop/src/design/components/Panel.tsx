import { useState } from "react";
import type { ReactNode } from "react";
import "./Panel.css";

export interface PanelProps {
  title?: string;
  subtitle?: string;
  children: ReactNode;
  /** When set, the panel renders a toggle header and can be collapsed. */
  collapsible?: boolean;
  defaultOpen?: boolean;
  right?: ReactNode;
  className?: string;
  /** Optional data-testid for the collapsible header button, so a test can
   * open/close a specific panel (e.g. two collapsible panels on the same
   * screen) without a generic selector. No effect when collapsible is
   * false, or when omitted -- every existing caller renders unchanged. */
  headerTestId?: string;
}

/** Generic bordered container used for every grouped block in the app —
 * the helper frame, form sections, the prescore strip, etc. */
export function Panel({
  title,
  subtitle,
  children,
  collapsible = false,
  defaultOpen = true,
  right,
  className,
  headerTestId,
}: PanelProps) {
  const [open, setOpen] = useState(defaultOpen);
  const hasHeader = Boolean(title || subtitle || right);

  return (
    <section className={["sigma-panel", className ?? ""].filter(Boolean).join(" ")}>
      {hasHeader &&
        (collapsible ? (
          <button
            type="button"
            className="sigma-panel__header sigma-panel__header--collapsible"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            data-testid={headerTestId}
          >
            <span className="sigma-panel__title-group">
              {title && <span className="sigma-panel__title">{title}</span>}
              {subtitle && <span className="sigma-panel__subtitle">{subtitle}</span>}
            </span>
            <span className={`sigma-panel__chevron ${open ? "sigma-panel__chevron--open" : ""}`} aria-hidden="true">
              ▾
            </span>
          </button>
        ) : (
          <div className="sigma-panel__header">
            <span className="sigma-panel__title-group">
              {title && <span className="sigma-panel__title">{title}</span>}
              {subtitle && <span className="sigma-panel__subtitle">{subtitle}</span>}
            </span>
            {right}
          </div>
        ))}
      {(!collapsible || open) && (
        <div className={`sigma-panel__body ${!hasHeader ? "sigma-panel__body--no-header-padding" : ""}`}>
          {children}
        </div>
      )}
    </section>
  );
}
