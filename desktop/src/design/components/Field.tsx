import type { ReactNode } from "react";
import "./Field.css";

export type FieldFlagStatus = "pass" | "flag" | "hard_flag";

export interface FieldFlag {
  status: FieldFlagStatus;
  message: string;
}

export interface FieldProps {
  label: string;
  htmlFor?: string;
  helper?: ReactNode;
  required?: boolean;
  /** Field-level flag from the engine's validation or prescore response
   * (M1 brief: "render field-level flags"). Omit for an unflagged field. */
  flag?: FieldFlag;
  right?: ReactNode;
  children: ReactNode;
  className?: string;
}

/** Label + input + helper text + flag state — the one field wrapper every
 * form control in the app uses (M1 brief). Composes with the input
 * primitives in Inputs.tsx, or with any custom control as `children`. */
export function Field({ label, htmlFor, helper, required, flag, right, children, className }: FieldProps) {
  const flagClass = flag ? `sigma-field--${flag.status}` : "";
  return (
    <div className={["sigma-field", flagClass, className ?? ""].filter(Boolean).join(" ")}>
      <div className="sigma-field__label-row">
        <label className="sigma-field__label" htmlFor={htmlFor}>
          {label}
          {required && (
            <span className="sigma-field__required" aria-label="required">
              *
            </span>
          )}
        </label>
        {right}
      </div>
      {children}
      {helper && <div className="sigma-field__helper">{helper}</div>}
      {flag && <div className="sigma-field__flag-message">{flag.message}</div>}
    </div>
  );
}
