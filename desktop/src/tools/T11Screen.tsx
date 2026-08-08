import { useState } from "react";
import { Button } from "../design/components";
import { DataImportForm } from "./dataimport/DataImportForm";
import { SampleSizePanel } from "./samplesize/SampleSizePanel";
import { CollectionPlanForm } from "./collectionplan/CollectionPlanForm";
import type { ProjectMetadata } from "../api/types";
import "./T11Screen.css";

export interface T11ScreenProps {
  projectId: string;
  project: ProjectMetadata;
  onSaved: () => void;
}

type T11Tab = "import" | "plan" | "sample-size";

const TABS: { id: T11Tab; label: string }[] = [
  { id: "import", label: "Import Data" },
  { id: "plan", label: "Collection Plan" },
  { id: "sample-size", label: "Sample Size" },
];

/** T-11's three halves, one screen, tabbed: the dataset import and the
 * sample-size calculator (both pre-existing) plus the Collection Plan
 * (rubric R-MEA-05: operational definition, data type, stratification,
 * logistics). Every tab stays mounted (display:none, not unmount) so
 * switching tabs never loses in-progress, unsaved state in another one. */
export function T11Screen({ projectId, project, onSaved }: T11ScreenProps) {
  const [tab, setTab] = useState<T11Tab>("import");

  return (
    <div className="sigma-t11-screen">
      <div className="sigma-t11-screen__tabs" role="tablist" aria-label="Data Collection Plan sections">
        {TABS.map((t) => (
          <Button
            key={t.id} type="button" role="tab" aria-selected={tab === t.id}
            variant={tab === t.id ? "primary" : "ghost"} size="sm"
            onClick={() => setTab(t.id)} data-testid={`t11-tab-${t.id}`}
          >
            {t.label}
          </Button>
        ))}
      </div>

      <div className="sigma-t11-screen__panel" hidden={tab !== "import"}>
        <DataImportForm projectId={projectId} onSaved={onSaved} />
      </div>
      <div className="sigma-t11-screen__panel" hidden={tab !== "plan"}>
        <CollectionPlanForm projectId={projectId} project={project} onSaved={onSaved} />
      </div>
      <div className="sigma-t11-screen__panel" hidden={tab !== "sample-size"}>
        <SampleSizePanel />
      </div>
    </div>
  );
}
