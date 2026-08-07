import type { InputHTMLAttributes, ReactNode, SelectHTMLAttributes, TextareaHTMLAttributes } from "react";
import "./Field.css";

type TextInputProps = InputHTMLAttributes<HTMLInputElement>;
type TextAreaProps = TextareaHTMLAttributes<HTMLTextAreaElement>;
type SelectProps = SelectHTMLAttributes<HTMLSelectElement> & { children: ReactNode };

/** Styled input primitives sharing the `.sigma-input` look, meant to sit
 * inside a <Field>. Thin wrappers, not a component-library import. */
export function TextInput(props: TextInputProps) {
  return <input {...props} className={["sigma-input", props.className ?? ""].join(" ")} />;
}

export function TextArea(props: TextAreaProps) {
  return <textarea {...props} className={["sigma-input", props.className ?? ""].join(" ")} />;
}

export function SelectInput({ children, ...props }: SelectProps) {
  return (
    <select {...props} className={["sigma-input", props.className ?? ""].join(" ")}>
      {children}
    </select>
  );
}
