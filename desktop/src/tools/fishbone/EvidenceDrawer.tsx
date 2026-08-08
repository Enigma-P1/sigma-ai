import { useEffect, useState } from "react";
import { listDatasets } from "../../api/client";
import { Button, Field, Modal, SelectInput, TextArea, VerdictBanner } from "../../design/components";
import type { DatasetMeta, FishboneEvidence, EvidenceKind, ProjectMetadata } from "../../api/types";
import { EVIDENCE_KINDS } from "../../api/types";
import { EVIDENCE_KIND_LABELS } from "./fishboneLogic";

export interface EvidenceDrawerProps {
  projectId: string;
  project: ProjectMetadata;
  current: FishboneEvidence | null | undefined;
  onClose: () => void;
  onConfirm: (evidence: FishboneEvidence | null) => void;
}

const ARTIFACT_KIND_TOOL_ID: Partial<Record<EvidenceKind, string>> = { hypothesis_run: "T-17", check_sheet: "T-08" };

/** "What data supports this?" (PLAN §4.1) -- pick a dataset/hypothesis-run/
 * check-sheet artifact already saved in this project, or write an
 * observation note directly. Enforces the same schema the engine does:
 * confirm is disabled until `ref` is non-blank, matching artifacts/
 * fishbone.py's Evidence.ref requirement. */
export function EvidenceDrawer({ projectId, project, current, onClose, onConfirm }: EvidenceDrawerProps) {
  const [kind, setKind] = useState<EvidenceKind>(current?.kind ?? "observation_note");
  const [ref, setRef] = useState(current?.ref ?? "");
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);

  useEffect(() => {
    let cancelled = false;
    listDatasets(projectId).then((d) => {
      if (!cancelled) setDatasets(d);
    }).catch(() => {
      /* dataset picker just stays empty; observation notes still work */
    });
    return () => {
      cancelled = true;
    };
  }, [projectId]);

  const artifactOptions = Object.entries(project.artifact_index)
    .filter(([, entry]) => entry.tool_id === ARTIFACT_KIND_TOOL_ID[kind])
    .map(([artifactId]) => artifactId);

  return (
    <Modal title="Evidence" onClose={onClose}>
      <p>What data supports this cause? Team consensus alone is not evidence (rubric R-ANA-02).</p>

      <Field label="Kind" htmlFor="evidence-kind">
        <SelectInput id="evidence-kind" data-testid="fishbone-evidence-kind" value={kind} onChange={(e) => { setKind(e.target.value as EvidenceKind); setRef(""); }}>
          {EVIDENCE_KINDS.map((k) => (
            <option key={k} value={k}>{EVIDENCE_KIND_LABELS[k]}</option>
          ))}
        </SelectInput>
      </Field>

      {kind === "observation_note" ? (
        <Field label="Observation note" required htmlFor="evidence-note" helper="A dated gemba observation, a stratified split, whatever a reasonable person would accept as showing the cause operates.">
          <TextArea id="evidence-note" data-testid="fishbone-evidence-note" rows={4} value={ref} onChange={(e) => setRef(e.target.value)} />
        </Field>
      ) : kind === "dataset" ? (
        <Field label="Dataset" required htmlFor="evidence-dataset">
          <SelectInput id="evidence-dataset" data-testid="fishbone-evidence-dataset" value={ref} onChange={(e) => setRef(e.target.value)}>
            <option value="">-- choose a saved dataset --</option>
            {datasets.map((d) => (
              <option key={d.dataset_id} value={d.dataset_id}>{d.source_filename} ({d.row_count} rows)</option>
            ))}
          </SelectInput>
        </Field>
      ) : (
        <Field label={EVIDENCE_KIND_LABELS[kind]} required htmlFor="evidence-artifact">
          <SelectInput id="evidence-artifact" data-testid="fishbone-evidence-artifact" value={ref} onChange={(e) => setRef(e.target.value)}>
            <option value="">-- choose a saved artifact --</option>
            {artifactOptions.map((id) => (
              <option key={id} value={id}>{id}</option>
            ))}
          </SelectInput>
          {artifactOptions.length === 0 && (
            <VerdictBanner tone="neutral" headline={`No ${ARTIFACT_KIND_TOOL_ID[kind]} artifact saved in this project yet.`} />
          )}
        </Field>
      )}

      <div className="sigma-fishbone-evidence-actions">
        {current && (
          <Button variant="ghost" type="button" onClick={() => onConfirm(null)} data-testid="fishbone-evidence-clear">
            Clear evidence
          </Button>
        )}
        <Button variant="primary" type="button" disabled={!ref.trim()} onClick={() => onConfirm({ kind, ref: ref.trim() })} data-testid="fishbone-evidence-confirm">
          Save evidence
        </Button>
      </div>
    </Modal>
  );
}
