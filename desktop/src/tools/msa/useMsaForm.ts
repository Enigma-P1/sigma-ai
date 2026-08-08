import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError, groupValidationByField } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type { MsaArtifact, MsaDataType, PrescoreResult, ProjectMetadata } from "../../api/types";
import {
  attributeCanSave,
  attributeItemsFromArtifact,
  attributeItemsToBody,
  continuousCanSave,
  continuousItemsFromArtifact,
  continuousItemsToBody,
  emptyAttributeItem,
  emptyContinuousItem,
} from "./msaLogic";
import type { AttributeItemValue, ContinuousItemValue } from "./msaLogic";

const ARTIFACT_ID = "msa";
const SCHEMA_VERSION = 1;

/** T-12's state + engine wiring -- same shape as useCopqForm.ts (load on
 * open, save re-validates + recomputes server-side, reload for the fresh
 * result, then prescore). One artifact carries either path; switching
 * data_type clears the stale server result rather than showing a result
 * for the path no longer being edited. */
export function useMsaForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [dataType, setDataTypeRaw] = useState<MsaDataType>("continuous");
  const [operator, setOperator] = useState("");
  const [gaugeName, setGaugeName] = useState("");
  const [gaugeIncrementText, setGaugeIncrementText] = useState("");
  const [uslText, setUslText] = useState("");
  const [lslText, setLslText] = useState("");
  const [continuousItems, setContinuousItems] = useState<ContinuousItemValue[]>([emptyContinuousItem(0)]);
  const [attributeItems, setAttributeItems] = useState<AttributeItemValue[]>([emptyAttributeItem(0)]);
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);
  const [serverArtifact, setServerArtifact] = useState<MsaArtifact | null>(null);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const d = data as unknown as MsaArtifact;
        setDataTypeRaw(d.data_type);
        setOperator(d.operator);
        setGaugeName(d.gauge_name ?? "");
        setGaugeIncrementText(d.gauge_increment != null ? String(d.gauge_increment) : "");
        setUslText(d.usl != null ? String(d.usl) : "");
        setLslText(d.lsl != null ? String(d.lsl) : "");
        if (d.continuous_items.length) setContinuousItems(continuousItemsFromArtifact(d));
        if (d.attribute_items.length) setAttributeItems(attributeItemsFromArtifact(d));
        setServerArtifact(d);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  function setDataType(next: MsaDataType) {
    setDataTypeRaw(next);
    setServerArtifact(null); // the loaded result is for the other path -- stop showing it as current
  }
  function updateContinuousItems(next: ContinuousItemValue[]) {
    setContinuousItems(next);
    setServerArtifact(null);
  }
  function updateAttributeItems(next: AttributeItemValue[]) {
    setAttributeItems(next);
    setServerArtifact(null);
  }

  const canSave =
    !saving &&
    (dataType === "continuous"
      ? continuousCanSave(continuousItems, gaugeIncrementText, operator)
      : attributeCanSave(attributeItems, operator));

  async function handleSave() {
    if (!canSave) return;
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    setFieldErrors({});
    const now = new Date().toISOString();
    const body: Record<string, unknown> = {
      schema_version: SCHEMA_VERSION,
      artifact_id: ARTIFACT_ID,
      tool_id: "T-12",
      created_at: now,
      updated_at: now,
      data_type: dataType,
      operator: operator.trim(),
      gauge_name: dataType === "continuous" ? gaugeName.trim() || null : null,
      gauge_increment: dataType === "continuous" ? Number(gaugeIncrementText) : null,
      usl: uslText.trim() === "" ? null : Number(uslText),
      lsl: lslText.trim() === "" ? null : Number(lslText),
      continuous_items: dataType === "continuous" ? continuousItemsToBody(continuousItems) : [],
      attribute_items: dataType === "attribute" ? attributeItemsToBody(attributeItems) : [],
    };

    try {
      const res = await saveArtifact(projectId, "T-12", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setServerArtifact((await loadArtifact(projectId, ARTIFACT_ID)) as unknown as MsaArtifact);
      } catch {
        /* the save itself succeeded; a failed re-load just leaves the result display blank */
      }
      try {
        setPrescore(await runPrescore("T-12", body));
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

  return {
    dataType, setDataType, operator, setOperator, gaugeName, setGaugeName,
    gaugeIncrementText, setGaugeIncrementText, uslText, setUslText, lslText, setLslText,
    continuousItems, updateContinuousItems, attributeItems, updateAttributeItems,
    version, saving, canSave, generalError, fieldErrors, prescore, serverArtifact, handleSave,
  };
}
