import { useEffect, useState } from "react";
import { loadArtifact, runPrescore, saveArtifact } from "../../api/client";
import { ApiError } from "../../api/errors";
import { useSaveState } from "../../app/SaveStateContext";
import type {
  CollectionLogistics, DataCollectionDataType, DataCollectionPlanArtifact, OperationalDefinition,
  PrescoreResult, ProjectMetadata, StratificationFactor,
} from "../../api/types";
import {
  buildCollectionPlanBody, canSaveCollectionPlan, collectionPlanStateFromArtifact,
  emptyLogistics, emptyOperationalDefinition,
} from "./collectionPlanLogic";

const ARTIFACT_ID = "collection-plan";
const SCHEMA_VERSION = 1;

/** T-11's PLAN-half state + engine wiring -- same load/save/prescore shape
 * as usePickerForm/useCopqForm (no server-computed fields to reload, so
 * this skips the load-artifact-again-after-save round trip those tools
 * with computed fields need). The import and sample-size tabs are
 * separate, independently engine-backed forms -- T11Screen composes all
 * three; this hook only owns the plan. */
export function useCollectionPlanForm(projectId: string, project: ProjectMetadata, onSaved: () => void) {
  const { setSaveState } = useSaveState();
  const [metricName, setMetricName] = useState("");
  const [charterMetricId, setCharterMetricId] = useState("");
  const [operationalDefinition, setOperationalDefinition] = useState<OperationalDefinition>(emptyOperationalDefinition());
  const [dataType, setDataType] = useState<DataCollectionDataType | null>(null);
  const [stratificationFactors, setStratificationFactors] = useState<StratificationFactor[]>([]);
  const [noStratificationReason, setNoStratificationReason] = useState("");
  const [logistics, setLogistics] = useState<CollectionLogistics>(emptyLogistics());
  const [biasNote, setBiasNote] = useState("");
  const [version, setVersion] = useState<number | null>(null);
  const [saving, setSaving] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);
  const [prescore, setPrescore] = useState<PrescoreResult[]>([]);

  const existingVersion = project.artifact_index[ARTIFACT_ID]?.latest_version;

  useEffect(() => {
    if (!existingVersion) return;
    let cancelled = false;
    loadArtifact(projectId, ARTIFACT_ID)
      .then((data) => {
        if (cancelled) return;
        const s = collectionPlanStateFromArtifact(data as unknown as DataCollectionPlanArtifact);
        setMetricName(s.metricName);
        setCharterMetricId(s.charterMetricId);
        setOperationalDefinition(s.operationalDefinition);
        setDataType(s.dataType);
        setStratificationFactors(s.stratificationFactors);
        setNoStratificationReason(s.noStratificationReason);
        setLogistics(s.logistics);
        setBiasNote(s.biasNote);
        setVersion(existingVersion);
      })
      .catch(() => {
        /* best-effort prefill; an empty form is still usable */
      });
    return () => {
      cancelled = true;
    };
  }, [projectId, existingVersion]);

  async function handleSave() {
    setSaving(true);
    setSaveState("saving");
    setGeneralError(null);
    const body = buildCollectionPlanBody({
      artifactId: ARTIFACT_ID, schemaVersion: SCHEMA_VERSION, metricName, charterMetricId,
      operationalDefinition, dataType, stratificationFactors, noStratificationReason, logistics, biasNote,
    });
    try {
      const res = await saveArtifact(projectId, "T-11", body);
      setVersion(res.version);
      setSaveState("saved");
      onSaved();
      try {
        setPrescore(await runPrescore("T-11", body));
      } catch {
        /* prescore is a nice-to-have on top of a successful save, not a blocker */
      }
    } catch (err) {
      setSaveState("error");
      setGeneralError(err instanceof ApiError ? err.message : "Could not save.");
    } finally {
      setSaving(false);
    }
  }

  return {
    metricName, setMetricName, charterMetricId, setCharterMetricId,
    operationalDefinition, setOperationalDefinition, dataType, setDataType,
    stratificationFactors, setStratificationFactors, noStratificationReason, setNoStratificationReason,
    logistics, setLogistics, biasNote, setBiasNote,
    version, saving, canSave: canSaveCollectionPlan(stratificationFactors) && !saving,
    generalError, prescore, handleSave,
  };
}
