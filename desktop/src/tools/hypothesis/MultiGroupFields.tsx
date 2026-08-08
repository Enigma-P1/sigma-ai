import { ArraySourceInput } from "./ArraySourceInput";
import { DynamicList } from "../charter/DynamicList";
import { emptyArraySource, ensureMinGroups } from "./hypothesisFormState";
import type { ArraySourceValue } from "./hypothesisFormState";
import type { DatasetDetail, DatasetMeta } from "../../api/types";

export interface MultiGroupFieldsProps {
  groups: ArraySourceValue[];
  onGroupsChange: (groups: ArraySourceValue[]) => void;
  datasets: DatasetMeta[];
  datasetDetails: Record<string, DatasetDetail>;
  onNeedDatasetDetail: (datasetId: string) => void;
}

/** Three or more independent groups -- add/remove, floored at 3 (one-way
 * ANOVA's own EXIT-06 floor; the selector exits below it anyway, but the
 * form shouldn't offer fewer than a real 3+-group design needs). */
export function MultiGroupFields({ groups, onGroupsChange, datasets, datasetDetails, onNeedDatasetDetail }: MultiGroupFieldsProps) {
  const padded = ensureMinGroups(groups, 3);

  return (
    <DynamicList
      items={padded}
      onChange={onGroupsChange}
      makeEmpty={() => emptyArraySource(`Group ${padded.length + 1}`)}
      minItems={3}
      addLabel="+ Add group"
      renderRow={(row, i, update) => (
        <ArraySourceInput
          value={row} onChange={update} datasets={datasets} datasetDetails={datasetDetails}
          onNeedDatasetDetail={onNeedDatasetDetail} testId={`hyp-group-${i}`} labelText={`Group ${i + 1}`}
        />
      )}
    />
  );
}
