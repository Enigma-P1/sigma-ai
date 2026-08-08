import { VerdictBanner } from "../../design/components";
import { ContingencyTableFields } from "./ContingencyTableFields";
import { MultiGroupFields } from "./MultiGroupFields";
import { OneSampleFields } from "./OneSampleFields";
import { PairedFields } from "./PairedFields";
import { ProportionsFields } from "./ProportionsFields";
import { TwoIndependentFields } from "./TwoIndependentFields";
import type { HypothesisFormState } from "./hypothesisFormState";
import type { DatasetDetail, DatasetMeta } from "../../api/types";

export interface DataSourceFieldsProps {
  state: HypothesisFormState;
  patch: (p: Partial<HypothesisFormState>) => void;
  datasets: DatasetMeta[];
  datasetDetails: Record<string, DatasetDetail>;
  onNeedDatasetDetail: (datasetId: string) => void;
}

/** Dispatches to the right data-entry shape for the declared comparison
 * type -- the "what are you comparing" answer decides which fields exist
 * at all, matching the engine's own comparison_type branching. */
export function DataSourceFields({ state, patch, datasets, datasetDetails, onNeedDatasetDetail }: DataSourceFieldsProps) {
  const common = { datasets, datasetDetails, onNeedDatasetDetail };

  switch (state.comparisonType) {
    case "two_independent":
      return <TwoIndependentFields groups={state.groups} onGroupsChange={(groups) => patch({ groups })} {...common} />;
    case "multi_group":
      return <MultiGroupFields groups={state.groups} onGroupsChange={(groups) => patch({ groups })} {...common} />;
    case "paired":
      return (
        <PairedFields
          before={state.pairedBefore} after={state.pairedAfter}
          onBeforeChange={(pairedBefore) => patch({ pairedBefore })} onAfterChange={(pairedAfter) => patch({ pairedAfter })}
          {...common}
        />
      );
    case "one_sample_vs_target":
      return (
        <OneSampleFields
          sample={state.sample} onSampleChange={(sample) => patch({ sample })}
          targetText={state.targetText} onTargetChange={(targetText) => patch({ targetText })}
          {...common}
        />
      );
    case "proportions":
      return (
        <ProportionsFields
          groups={state.proportionGroups} onGroupsChange={(proportionGroups) => patch({ proportionGroups })}
          targetText={state.proportionTargetText} onTargetChange={(proportionTargetText) => patch({ proportionTargetText })}
        />
      );
    case "association_categorical":
      return <ContingencyTableFields value={state.contingency} onChange={(contingency) => patch({ contingency })} />;
    case "relationship_continuous":
      return (
        <VerdictBanner
          tone="neutral"
          headline="This shape always routes to a named exit"
          detail="Quantified correlation/regression is deferred by name in v1 (EXIT-15) -- no data entry is needed to see that; preview the tree below to see the exit and its route out."
        />
      );
  }
}
