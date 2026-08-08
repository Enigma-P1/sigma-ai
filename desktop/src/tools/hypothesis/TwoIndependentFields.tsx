import { ArraySourceInput } from "./ArraySourceInput";
import { emptyArraySource } from "./hypothesisFormState";
import type { ArraySourceValue } from "./hypothesisFormState";
import type { DatasetDetail, DatasetMeta } from "../../api/types";

export interface TwoIndependentFieldsProps {
  groups: ArraySourceValue[];
  onGroupsChange: (groups: ArraySourceValue[]) => void;
  datasets: DatasetMeta[];
  datasetDetails: Record<string, DatasetDetail>;
  onNeedDatasetDetail: (datasetId: string) => void;
}

/** Exactly two independent groups -- fixed, no add/remove (that's
 * multi_group's job). The coffee-bar smoke case: wait_seconds split by
 * shift into morning/afternoon, each an ArraySourceInput in "dataset"
 * mode with a split column. */
export function TwoIndependentFields({ groups, onGroupsChange, datasets, datasetDetails, onNeedDatasetDetail }: TwoIndependentFieldsProps) {
  const a = groups[0] ?? emptyArraySource("Group A");
  const b = groups[1] ?? emptyArraySource("Group B");

  return (
    <>
      <ArraySourceInput
        value={a} onChange={(v) => onGroupsChange([v, b])} datasets={datasets} datasetDetails={datasetDetails}
        onNeedDatasetDetail={onNeedDatasetDetail} testId="hyp-group-0" labelText="First group"
      />
      <ArraySourceInput
        value={b} onChange={(v) => onGroupsChange([a, v])} datasets={datasets} datasetDetails={datasetDetails}
        onNeedDatasetDetail={onNeedDatasetDetail} testId="hyp-group-1" labelText="Second group"
      />
    </>
  );
}
