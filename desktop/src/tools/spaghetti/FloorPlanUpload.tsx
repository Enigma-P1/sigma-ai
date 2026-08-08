import { Field, Panel, VerdictBanner } from "../../design/components";

export interface FloorPlanUploadProps {
  hasFloorPlan: boolean;
  sourceFilename?: string;
  uploading: boolean;
  error: string | null;
  onFileSelected: (file: File) => void;
}

/** T-07's first, atomic step: upload a floor-plan image (or a photo of a
 * paper sketch). Upload IS save here -- the engine returns a FloorPlanRef
 * (metadata + SHA-256), and the same base64 payload becomes the canvas's
 * background image locally, with no second round trip needed to see it. */
export function FloorPlanUpload({ hasFloorPlan, sourceFilename, uploading, error, onFileSelected }: FloorPlanUploadProps) {
  return (
    <Panel title="Floor plan" subtitle="Upload a floor-plan image, or a photo of a paper sketch">
      <Field label="Image file (PNG or JPEG)" helper="This becomes the canvas background you calibrate and trace routes on.">
        <input
          type="file" accept=".png,.jpg,.jpeg" data-testid="spaghetti-floorplan-input"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) onFileSelected(file);
          }}
        />
      </Field>
      {uploading && <p>Uploading…</p>}
      {error && <VerdictBanner tone="fail" headline={error} />}
      {hasFloorPlan && !uploading && (
        <div data-testid="spaghetti-floorplan-loaded">
          <VerdictBanner tone="pass" headline={`Floor plan loaded: ${sourceFilename ?? "uploaded image"}`} />
        </div>
      )}
    </Panel>
  );
}
