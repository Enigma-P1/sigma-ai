import { Button, Field, Panel, TextArea, TextInput, VerdictBanner } from "../../design/components";
import { MIN_PACKAGE_COMPONENTS, emptyDeclaredPackage } from "./pilotPlanLogic";
import type { PilotDeclaredPackage } from "../../api/types";

export interface DeclaredPackageSectionProps {
  value: PilotDeclaredPackage | null;
  onChange: (next: PilotDeclaredPackage | null) => void;
}

/** Rubric R-IMP-02 #1's "one honest carve-out": a genuinely inseparable
 * package -- components that cannot deploy apart -- may run as one pilot
 * when declared as the package up front, components listed, attribution
 * limited to the package as a whole, never a single component. Toggling
 * this ON replaces `changes` (Step 1's one-sentence statement + "add
 * another change" demo affordance) with one entry per listed component
 * below -- see pilotPlanLogic.ts's changesFromState, the single place
 * `changes` gets derived so the two views can't silently diverge. */
export function DeclaredPackageSection({ value, onChange }: DeclaredPackageSectionProps) {
  const active = value !== null;

  function updateComponent(index: number, text: string) {
    if (!value) return;
    onChange({ ...value, components: value.components.map((c, i) => (i === index ? text : c)) });
  }
  function addComponent() {
    if (!value) return;
    onChange({ ...value, components: [...value.components, ""] });
  }
  function removeComponent(index: number) {
    if (!value) return;
    onChange({ ...value, components: value.components.filter((_, i) => i !== index) });
  }

  return (
    <Panel title="Declared package (optional carve-out)" subtitle="Only for components that genuinely cannot deploy apart -- R-IMP-02's one honest exception">
      <label className="sigma-pilot-package-toggle">
        <input
          type="checkbox" data-testid="pilot-package-toggle" checked={active}
          onChange={(e) => onChange(e.target.checked ? emptyDeclaredPackage() : null)}
        />
        This pilot is a declared inseparable package, not a single change
      </label>

      {active && value && (
        <>
          <Field
            label="Rationale" htmlFor="pilot-package-rationale" required
            helper="Why can't these components be deployed apart? (e.g. they ship as one sealed cartridge, or one change is meaningless without the other already in place)"
          >
            <TextArea
              id="pilot-package-rationale" data-testid="pilot-package-rationale" rows={2}
              value={value.rationale} onChange={(e) => onChange({ ...value, rationale: e.target.value })}
            />
          </Field>

          <div className="sigma-pilot-package-components">
            {value.components.map((component, i) => (
              <div className="sigma-pilot-package-component-row" key={i}>
                <TextInput
                  data-testid={`pilot-package-component-${i}`} value={component}
                  onChange={(e) => updateComponent(i, e.target.value)}
                  placeholder={`Component ${i + 1} (e.g. "fixture head")`}
                />
                <Button
                  variant="ghost" size="sm" type="button" onClick={() => removeComponent(i)}
                  data-testid={`pilot-package-remove-component-${i}`}
                >
                  Remove
                </Button>
              </div>
            ))}
            <Button variant="ghost" size="sm" type="button" onClick={addComponent} data-testid="pilot-package-add-component">
              + Add component
            </Button>
          </div>

          {value.components.length < MIN_PACKAGE_COMPONENTS && (
            <div data-testid="pilot-package-too-few-banner">
              <VerdictBanner
                tone="flag" headline="One component is just a change, not a package"
                detail={`The carve-out names components, plural -- list at least ${MIN_PACKAGE_COMPONENTS} for this to read as a real package (a 1-component "package" saves, but prescore flags it).`}
              />
            </div>
          )}

          <div data-testid="pilot-package-attribution-note">
            <VerdictBanner
              tone="neutral" headline="Proof credit will be package-level only"
              detail="No single component below may claim this result on its own -- attribution goes to the package as a whole (rubric R-IMP-02's carve-out)."
            />
          </div>
        </>
      )}
    </Panel>
  );
}
