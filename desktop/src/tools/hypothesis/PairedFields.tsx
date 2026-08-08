import { ArraySourceInput } from "./ArraySourceInput";
import type { ArraySourceValue } from "./hypothesisFormState";
import type { DatasetDetail, DatasetMeta } from "../../api/types";

export interface PairedFieldsProps {
  before: ArraySourceValue;
  after: ArraySourceValue;
  onBeforeChange: (v: ArraySourceValue) => void;
  onAfterChange: (v: ArraySourceValue) => void;
  datasets: DatasetMeta[];
  datasetDetails: Record<string, DatasetDetail>;
  onNeedDatasetDetail: (datasetId: string) => void;
}

/** Before/after pairs -- same units, measured twice. Both arrays must end
 * up the same length (the engine's paired_t / Wilcoxon routes require it);
 * this form doesn't block on mismatched lengths itself, the engine's own
 * 422 does, since a same-dataset two-column pick is always aligned by row
 * and a paste mismatch is a real data problem worth surfacing honestly. */
export function PairedFields({ before, after, onBeforeChange, onAfterChange, datasets, datasetDetails, onNeedDatasetDetail }: PairedFieldsProps) {
  return (
    <>
      <ArraySourceInput
        value={before} onChange={onBeforeChange} datasets={datasets} datasetDetails={datasetDetails}
        onNeedDatasetDetail={onNeedDatasetDetail} testId="hyp-paired-before" labelText="Before"
      />
      <ArraySourceInput
        value={after} onChange={onAfterChange} datasets={datasets} datasetDetails={datasetDetails}
        onNeedDatasetDetail={onNeedDatasetDetail} testId="hyp-paired-after" labelText="After"
      />
    </>
  );
}
