import { useEffect, useState } from "react";
import { Button, Field, Panel, TextArea, VerdictBanner } from "../../design/components";
import { CriterionField } from "./CriterionField";
import { PrescoreStrip } from "../PrescoreStrip";
import { PICKER_CHECK_LABELS } from "./pickerChecks";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import { PICKER_CRITERIA_KEYS } from "../../api/types";
import type { PickerCriterionKey, PickerRoute, PrescoreResult, ProjectMetadata } from "../../api/types";

const ARTIFACT_ID = "picker";
const SCHEMA_VERSION = 1;

type CriteriaState = Record<PickerCriterionKey, { answer: boolean | null; detail: string }>;

const EMPTY_CRITERIA: CriteriaState = {
  scope_narrow: { answer: null, detail: "" },
  measurable_outcome: { answer: null, detail: "" },
  data_obtainable: { answer: null, detail: "" },
  process_owner_engaged: { answer: null, detail: "" },
  business_impact_plausible: { answer: null, detail: "" },
};

const CRITERIA_META: { key: PickerCriterionKey; label: string; helper: string }[] = [
  { key: "scope_narrow", label: "Is the scope narrow enough to actually finish?", helper: "One line, one shift, one product -- not the whole department." },
  { key: "measurable_outcome", label: "Is there a measurable outcome?", helper: "A number that goes up or down, tracked somewhere real." },
  { key: "data_obtainable", label: "Can you actually get the data?", helper: "Name the real source -- a log, a system export, a form." },
  { key: "process_owner_engaged", label: "Does a process owner care about this?", helper: "Someone who owns the process asked for this or backs it." },
  { key: "business_impact_plausible", label: "Is the business impact plausible?", helper: "Rough dollars or hours -- doesn't need to be exact yet." },
];

const ROUTES: { value: PickerRoute; label: string }[] = [
  { value: "full-DMAIC", label: "Full DMAIC" },
  { value: "PDCA", label: "PDCA quick path" },
  { value: "EXIT-01", label: "Not a good fit (EXIT-01)" },
];

/** Mirrors picker.py's route_is_consistent() for instant client-side
 * feedback. The engine's schema validator is still the final authority --
 * this just stops the user from ever submitting a combination it would
 * reject (matrix §4a, frozen rule). */
function routeIsConsistent(criteria: boolean[], route: PickerRoute): boolean {
  const anyNo = criteria.some((c) => !c);
  if (route === "full-DMAIC") return !anyNo;
  if (route === "EXIT-01") return anyNo;
  return true;
}

export interface PickerFormProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

/** T-01 Project Picker form -- one of the two proof screens (M1 brief). */
export function PickerForm({ projectId, project, onSaved }: PickerFormProps) {
  const { setSaveState } = useSaveState();
  const [criteria, setCriteria] = useState<CriteriaState>(EMPTY_CRITERIA);
  const [route, setRoute] = useState<PickerRoute | null>(null);
  const [notes, setNotes] = useState("");
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  // Load the saved artifact, if any, so revisiting the tool shows what's
  // already there instead of a blank form.
  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as Record<string, { answer: boolean; detail: string }> & {
          route: PickerRoute;
          notes?: string;
        };
        const next = { ...EMPTY_CRITERIA };
        for (const key of PICKER_CRITERIA_KEYS) {
          const c = d[key];
          if (c) next[key] = { answer: c.answer, detail: c.detail };
        }
        setCriteria(next);
        setRoute(d.route);
        setNotes(d.notes ?? "");
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  const answeredBooleans = PICKER_CRITERIA_KEYS.map((k) => criteria[k].answer);
  const allAnswered = answeredBooleans.every((a) => a !== null) && PICKER_CRITERIA_KEYS.every((k) => criteria[k].detail.trim());
  const routeValid = route !== null && routeIsConsistent(answeredBooleans.map(Boolean), route);
  const canSave = allAnswered && routeValid && !saving;

  function updateCriterion(key: PickerCriterionKey, patch: Partial<{ answer: boolean; detail: string }>) {
    setCriteria((prev) => ({ ...prev, [key]: { ...prev[key], ...patch } }));
  }

  async function handleSave() {
    if (!route) return;
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const now = new Date().toISOString();
    const body: Record<string, unknown> = {
      schema_version: SCHEMA_VERSION,
      artifact_id: ARTIFACT_ID,
      tool_id: "T-01",
      created_at: now,
      updated_at: now,
      route,
      notes: notes.trim() || null,
    };
    for (const key of PICKER_CRITERIA_KEYS) {
      body[key] = { answer: criteria[key].answer, detail: criteria[key].detail.trim() };
    }

    try {
      const res = await saveArtifact(projectId, "T-01", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setPrescore(await runPrescore("T-01", body));
      } catch {
        /* prescore is a nice-to-have on top of a successful save, not a blocker */
      }
    } catch (err) {
      setSaveState("error");
      if (err instanceof ApiError && err.validation) {
        const grouped = groupValidationByField(err.validation);
        const flat: Record<string, string> = {};
        for (const [path, items] of Object.entries(grouped)) flat[path] = items[0]?.msg ?? "Invalid value.";
        setFieldErrors(flat);
        setGeneralError("Some fields need fixing before this can save.");
      } else {
        setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Panel title="Is this a good first project?" right={version != null && (
      <span data-testid="picker-version-badge">v{version} saved</span>
    )}>
      {CRITERIA_META.map((meta) => (
        <CriterionField
          key={meta.key}
          fieldKey={meta.key}
          label={meta.label}
          helper={meta.helper}
          answer={criteria[meta.key].answer}
          detail={criteria[meta.key].detail}
          flag={
            fieldErrors[`${meta.key}.detail`] || fieldErrors[meta.key]
              ? { status: "hard_flag", message: fieldErrors[`${meta.key}.detail`] ?? fieldErrors[meta.key] }
              : undefined
          }
          onAnswerChange={(v) => updateCriterion(meta.key, { answer: v })}
          onDetailChange={(v) => updateCriterion(meta.key, { detail: v })}
        />
      ))}

      <Field label="Route" required helper="Which path fits, given your answers above?" flag={fieldErrors.route ? { status: "hard_flag", message: fieldErrors.route } : undefined}>
        <div style={{ display: "flex", gap: "var(--space-2)", flexWrap: "wrap" }}>
          {ROUTES.map((r) => {
            const disabled = !routeIsConsistent(answeredBooleans.map(Boolean), r.value) && answeredBooleans.every((a) => a !== null);
            return (
              <Button
                key={r.value}
                type="button"
                variant={route === r.value ? "primary" : "secondary"}
                size="sm"
                disabled={disabled}
                onClick={() => setRoute(r.value)}
                data-testid={`picker-route-${r.value}`}
                title={disabled ? "Inconsistent with your criteria answers (matrix §4a)" : undefined}
              >
                {r.label}
              </Button>
            );
          })}
        </div>
      </Field>

      <Field label="Notes" htmlFor="picker-notes" helper="Optional free text.">
        <TextArea id="picker-notes" value={notes} onChange={(e) => setNotes(e.target.value)} rows={2} />
      </Field>

      {generalError && <VerdictBanner tone="fail" headline={generalError} />}

      <Button variant="primary" disabled={!canSave} onClick={() => void handleSave()} data-testid="picker-save">
        {saving ? "Saving…" : version != null ? "Save new version" : "Save"}
      </Button>

      <PrescoreStrip results={prescore} labels={PICKER_CHECK_LABELS} />
    </Panel>
  );
}
