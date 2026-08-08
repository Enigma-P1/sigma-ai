import { Field, SelectInput, TextArea, TextInput } from "../../design/components";
import { countUnparsedTokens, parseNumberList } from "./hypothesisParsing";
import type { ArraySourceValue } from "./hypothesisFormState";
import type { DatasetDetail, DatasetMeta } from "../../api/types";
import "./HypothesisForm.css";

export interface ArraySourceInputProps {
  value: ArraySourceValue;
  onChange: (v: ArraySourceValue) => void;
  datasets: DatasetMeta[];
  datasetDetails: Record<string, DatasetDetail>;
  onNeedDatasetDetail: (datasetId: string) => void;
  testId: string;
  labelText: string;
}

/** One array of numbers, sourced either by pasting values or by pulling a
 * numeric column from a project dataset -- optionally filtered to one
 * value of a second (categorical) column first, e.g. the coffee-bar's
 * wait_seconds column split by its shift column into morning/afternoon.
 * Reused for every T-17 array slot: two_independent's groups, multi_group's
 * groups, paired's before/after, one_sample_vs_target's sample. */
export function ArraySourceInput({ value, onChange, datasets, datasetDetails, onNeedDatasetDetail, testId, labelText }: ArraySourceInputProps) {
  const dataset = datasets.find((d) => d.dataset_id === value.datasetId);
  const numericColumns = dataset?.columns.filter((c) => c.type === "numeric") ?? [];
  const textColumns = dataset?.columns.filter((c) => c.type === "text") ?? [];
  const detail = value.datasetId ? datasetDetails[value.datasetId] : undefined;
  const splitValues = detail && value.splitColumn ? Array.from(new Set(detail.rows.map((r) => r[value.splitColumn]))).sort() : [];
  const n = parseNumberList(value.pasteText).length;
  const badTokens = countUnparsedTokens(value.pasteText);

  return (
    <div className="sigma-hyp-array-source" data-testid={testId}>
      <div className="sigma-hyp-row">
        <Field label={`${labelText} label`} htmlFor={`${testId}-label`}>
          <TextInput id={`${testId}-label`} data-testid={`${testId}-label`} value={value.label} onChange={(e) => onChange({ ...value, label: e.target.value })} />
        </Field>
        <Field label="Source" htmlFor={`${testId}-mode`}>
          <SelectInput
            id={`${testId}-mode`} data-testid={`${testId}-mode`} value={value.mode}
            onChange={(e) => onChange({ ...value, mode: e.target.value as ArraySourceValue["mode"] })}
          >
            <option value="paste">Paste values</option>
            <option value="dataset">From a project dataset</option>
          </SelectInput>
        </Field>
      </div>

      {value.mode === "paste" ? (
        <Field label={`${labelText} values`} helper={`${n} value(s) parsed${badTokens > 0 ? `; ${badTokens} token(s) could not be read as numbers` : ""}.`}>
          <TextArea
            data-testid={`${testId}-paste`} rows={3} placeholder="e.g. 95, 91, 98, 93, 97"
            value={value.pasteText} onChange={(e) => onChange({ ...value, pasteText: e.target.value })}
          />
        </Field>
      ) : (
        <div className="sigma-hyp-row">
          <Field label="Dataset" htmlFor={`${testId}-dataset`}>
            <SelectInput
              id={`${testId}-dataset`} data-testid={`${testId}-dataset`} value={value.datasetId}
              onChange={(e) => { onChange({ ...value, datasetId: e.target.value, column: "", splitColumn: "", splitValue: "" }); if (e.target.value) onNeedDatasetDetail(e.target.value); }}
            >
              <option value="">Select a dataset…</option>
              {datasets.map((d) => (
                <option key={d.dataset_id} value={d.dataset_id}>{d.source_filename} ({d.row_count} rows)</option>
              ))}
            </SelectInput>
          </Field>
          <Field label="Column (numeric)" htmlFor={`${testId}-column`}>
            <SelectInput id={`${testId}-column`} data-testid={`${testId}-column`} value={value.column} disabled={!dataset} onChange={(e) => onChange({ ...value, column: e.target.value })}>
              <option value="">Select a column…</option>
              {numericColumns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
            </SelectInput>
          </Field>
          <Field label="Split by (optional)" htmlFor={`${testId}-split-column`} helper="Filter to one value of a category column -- e.g. shift = morning.">
            <SelectInput
              id={`${testId}-split-column`} data-testid={`${testId}-split-column`} value={value.splitColumn} disabled={!dataset}
              onChange={(e) => onChange({ ...value, splitColumn: e.target.value, splitValue: "" })}
            >
              <option value="">— whole column, no filter —</option>
              {textColumns.map((c) => <option key={c.name} value={c.name}>{c.name}</option>)}
            </SelectInput>
          </Field>
          {value.splitColumn && (
            <Field label={`Where ${value.splitColumn} =`} htmlFor={`${testId}-split-value`}>
              <SelectInput id={`${testId}-split-value`} data-testid={`${testId}-split-value`} value={value.splitValue} onChange={(e) => onChange({ ...value, splitValue: e.target.value })}>
                <option value="">Select a value…</option>
                {splitValues.map((v) => <option key={v} value={v}>{v}</option>)}
              </SelectInput>
            </Field>
          )}
        </div>
      )}
    </div>
  );
}
