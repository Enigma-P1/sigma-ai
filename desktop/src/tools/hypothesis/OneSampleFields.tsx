import { ArraySourceInput } from "./ArraySourceInput";
import { Field, TextInput } from "../../design/components";
import type { ArraySourceValue } from "./hypothesisFormState";
import type { DatasetDetail, DatasetMeta } from "../../api/types";

export interface OneSampleFieldsProps {
  sample: ArraySourceValue;
  onSampleChange: (v: ArraySourceValue) => void;
  targetText: string;
  onTargetChange: (v: string) => void;
  datasets: DatasetMeta[];
  datasetDetails: Record<string, DatasetDetail>;
  onNeedDatasetDetail: (datasetId: string) => void;
}

/** One group vs. a fixed target -- a spec, a historical baseline, a
 * customer requirement (matrix A-1's one-sample routes). */
export function OneSampleFields({ sample, onSampleChange, targetText, onTargetChange, datasets, datasetDetails, onNeedDatasetDetail }: OneSampleFieldsProps) {
  return (
    <>
      <ArraySourceInput
        value={sample} onChange={onSampleChange} datasets={datasets} datasetDetails={datasetDetails}
        onNeedDatasetDetail={onNeedDatasetDetail} testId="hyp-sample" labelText="Sample"
      />
      <Field
        label="Target value" required htmlFor="hyp-target"
        helper="The fixed value you're testing against -- a spec limit, a historical baseline, a customer requirement."
      >
        <TextInput id="hyp-target" data-testid="hyp-target" type="number" value={targetText} onChange={(e) => onTargetChange(e.target.value)} />
      </Field>
    </>
  );
}
