import { useEffect } from "react";
import type { ReactNode } from "react";
import "./Modal.css";

export interface ModalProps {
  title: string;
  onClose: () => void;
  children: ReactNode;
}

/** Minimal accessible dialog: overlay click and Escape both close it, focus
 * lands in the dialog. No portal library — a fixed-position overlay is
 * enough for a single-window desktop app. */
export function Modal({ title, onClose, children }: ModalProps) {
  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    document.addEventListener("keydown", onKeyDown);
    return () => document.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  return (
    <div
      className="sigma-modal-overlay"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div className="sigma-modal" role="dialog" aria-modal="true" aria-label={title}>
        <div className="sigma-modal__header">
          <span className="sigma-modal__title">{title}</span>
          <button type="button" className="sigma-modal__close" onClick={onClose} aria-label="Close" data-testid="modal-close">
            ×
          </button>
        </div>
        <div className="sigma-modal__body">{children}</div>
      </div>
    </div>
  );
}
