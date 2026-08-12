import { Button, VerdictBanner } from "../../design/components";
import { qualityActionFindings } from "./dataImportLogic";
import type { QualityActionFinding } from "./dataImportLogic";
import type { QualityScanResult } from "../../api/types";

export interface DatasetQualityFindingsProps {
  quality: QualityScanResult;
  onFixRepeatedHeader: () => void;
  onFixNearDuplicate: (column: string, variants: string[]) => void;
  onFixMixedDateFormat: () => void;
}

/** The saved dataset's own quality scan (meta.quality -- computed once at
 * save time by the same scan_quality the preview uses), rendered with a
 * live button per finding instead of the preview screen's "after saving"
 * text. Unlike the preview, this dataset already has an id, so the
 * derivation controls right below actually exist to jump into --
 * docs/uat/README.md's rule for this whole feature: "a finding a user
 * cannot act on is just a scolding." Renders nothing when the scan found
 * none of these three things, same as the preview scan's own clean case. */
export function DatasetQualityFindings({ quality, onFixRepeatedHeader, onFixNearDuplicate, onFixMixedDateFormat }: DatasetQualityFindingsProps) {
  const findings = qualityActionFindings(quality);
  if (findings.length === 0) return null;

  return (
    <div className="sigma-dataimport__quality-actions" data-testid="dataimport-rows-quality-actions">
      {findings.map((f, i) => (
        <QualityActionRow
          key={i} finding={f} index={i}
          onFixRepeatedHeader={onFixRepeatedHeader} onFixNearDuplicate={onFixNearDuplicate} onFixMixedDateFormat={onFixMixedDateFormat}
        />
      ))}
    </div>
  );
}

interface QualityActionRowProps {
  finding: QualityActionFinding;
  index: number;
  onFixRepeatedHeader: () => void;
  onFixNearDuplicate: (column: string, variants: string[]) => void;
  onFixMixedDateFormat: () => void;
}

function QualityActionRow({ finding, index, onFixRepeatedHeader, onFixNearDuplicate, onFixMixedDateFormat }: QualityActionRowProps) {
  if (finding.kind === "repeated_header_row") {
    return (
      <VerdictBanner
        tone="flag"
        headline={`${finding.count} row${finding.count === 1 ? "" : "s"} repeat the column header as data, not a real record`}
        actions={
          <Button variant="secondary" size="sm" onClick={onFixRepeatedHeader} data-testid="dataimport-quality-fix-delete-header">
            Select for Delete rows
          </Button>
        }
      />
    );
  }
  if (finding.kind === "near_duplicate") {
    return (
      <VerdictBanner
        tone="flag"
        headline={`${finding.column}: ${finding.variants.map((v) => `"${v}"`).join(", ")} look like the same value`}
        detail="Spelled differently, probably the same thing -- Recode merges the checked spellings into one."
        actions={
          <Button
            variant="secondary" size="sm" onClick={() => onFixNearDuplicate(finding.column, finding.variants)}
            data-testid={`dataimport-quality-fix-recode-${finding.column}-${index}`}
          >
            Recode this column
          </Button>
        }
      />
    );
  }
  return (
    <VerdictBanner
      tone="flag"
      headline={`${finding.column}: ${finding.shapes.length} different date formats (${finding.shapes.join(", ")})`}
      detail="No bulk fix for a date shape -- Edit a cell changes the odd ones out, one at a time."
      actions={
        <Button variant="secondary" size="sm" onClick={onFixMixedDateFormat} data-testid={`dataimport-quality-fix-dates-${finding.column}`}>
          Fix with Edit a cell
        </Button>
      }
    />
  );
}
