import { Field, TextInput } from "../../design/components";
import { DynamicList } from "../charter/DynamicList";
import { MSA_REPEATS_PER_ITEM, emptyContinuousItem } from "./msaLogic";
import type { ContinuousItemValue } from "./msaLogic";

export interface ContinuousStudyFieldsProps {
  gaugeName: string;
  onGaugeNameChange: (v: string) => void;
  gaugeIncrementText: string;
  onGaugeIncrementChange: (v: string) => void;
  uslText: string;
  onUslChange: (v: string) => void;
  lslText: string;
  onLslChange: (v: string) => void;
  items: ContinuousItemValue[];
  onItemsChange: (items: ContinuousItemValue[]) => void;
}

/** T-12 continuous-path study design: gauge name/increment, spec limits
 * (both needed for the tolerance denominator; either or neither leaves
 * the engine to fall back to study_variation), and the item x repeats
 * readings grid -- >=10 items x >=2 repeats is the matrix §4a guidance,
 * flagged (not blocked) below that by prescore. */
export function ContinuousStudyFields({
  gaugeName, onGaugeNameChange, gaugeIncrementText, onGaugeIncrementChange,
  uslText, onUslChange, lslText, onLslChange, items, onItemsChange,
}: ContinuousStudyFieldsProps) {
  return (
    <>
      <div className="sigma-msa-row">
        <Field label="Gauge / instrument" htmlFor="msa-gauge-name" helper="What did the measuring?">
          <TextInput id="msa-gauge-name" data-testid="msa-gauge-name" value={gaugeName} onChange={(e) => onGaugeNameChange(e.target.value)} placeholder="e.g. digital calipers" />
        </Field>
        <Field
          label="Gauge increment" required htmlFor="msa-gauge-increment"
          helper="The smallest unit the gauge actually reads -- a stopwatch in whole minutes has an increment of 1."
        >
          <TextInput id="msa-gauge-increment" data-testid="msa-gauge-increment" type="number" value={gaugeIncrementText} onChange={(e) => onGaugeIncrementChange(e.target.value)} />
        </Field>
      </div>
      <div className="sigma-msa-row">
        <Field label="USL (optional)" htmlFor="msa-usl" helper="Both spec limits present -> tolerance width is the denominator; otherwise study variation.">
          <TextInput id="msa-usl" data-testid="msa-usl" type="number" value={uslText} onChange={(e) => onUslChange(e.target.value)} />
        </Field>
        <Field label="LSL (optional)" htmlFor="msa-lsl">
          <TextInput id="msa-lsl" data-testid="msa-lsl" type="number" value={lslText} onChange={(e) => onLslChange(e.target.value)} />
        </Field>
      </div>

      <Field label="Items and repeat readings" helper={`Same operator, same procedure, ${MSA_REPEATS_PER_ITEM} repeats per item -- >=10 items spanning the range is the guidance.`}>
        <DynamicList
          items={items}
          onChange={onItemsChange}
          makeEmpty={() => emptyContinuousItem(items.length)}
          minItems={1}
          addLabel="+ Add item"
          renderRow={(row, i, update) => (
            <div className="sigma-msa-item-row" data-testid={`msa-item-row-${i}`}>
              <TextInput
                data-testid={`msa-item-id-${i}`} value={row.item_id}
                onChange={(e) => update({ ...row, item_id: e.target.value })} placeholder={`item-${i + 1}`}
              />
              {row.readings.map((reading, r) => (
                <TextInput
                  key={r} type="number" data-testid={`msa-item-${i}-repeat-${r}`} value={reading}
                  placeholder={`repeat ${r + 1}`}
                  onChange={(e) => {
                    const readings = [...row.readings];
                    readings[r] = e.target.value;
                    update({ ...row, readings });
                  }}
                />
              ))}
            </div>
          )}
        />
      </Field>
    </>
  );
}
