import { useEffect, useState } from "react";
import { getDataset, listDatasets } from "../../api/client";
import type { DatasetDetail, DatasetMeta } from "../../api/types";

/** Project datasets + an on-demand, cached full-detail fetch -- shared by
 * every ArraySourceInput on the screen (they may all point at the same
 * dataset, e.g. the coffee-bar fixture split two different ways) so a
 * dataset's rows are only ever fetched once. */
export function useDatasetDetailCache(projectId: string) {
  const [datasets, setDatasets] = useState<DatasetMeta[]>([]);
  const [datasetDetails, setDatasetDetails] = useState<Record<string, DatasetDetail>>({});

  useEffect(() => {
    listDatasets(projectId).then(setDatasets).catch(() => {
      /* an empty picker is still honest -- no dataset imported yet */
    });
  }, [projectId]);

  async function getDatasetDetailCached(datasetId: string): Promise<DatasetDetail> {
    const cached = datasetDetails[datasetId];
    if (cached) return cached;
    const detail = await getDataset(projectId, datasetId);
    setDatasetDetails((prev) => ({ ...prev, [datasetId]: detail }));
    return detail;
  }

  function loadDatasetDetail(datasetId: string) {
    if (!datasetId || datasetDetails[datasetId]) return;
    void getDatasetDetailCached(datasetId);
  }

  return { datasets, datasetDetails, loadDatasetDetail, getDatasetDetailCached };
}
