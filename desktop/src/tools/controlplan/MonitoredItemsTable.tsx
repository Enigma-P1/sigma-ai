import { Button, TextInput } from "../../design/components";
import type { MonitoredItem } from "../../api/types";

export interface MonitoredItemsTableProps {
  items: MonitoredItem[];
  onChange: (itemId: string, patch: Partial<MonitoredItem>) => void;
  onRemove: (itemId: string) => void;
  onAddOcap: (itemId: string) => void;
}

/** The control-plan table: one row per monitored item. `owner_name` is
 * left EMPTY-able on purpose -- saving an ownerless row is how the theater
 * flag gets demonstrated (rubric R-CTL-03 Fail line), not blocked. */
export function MonitoredItemsTable({ items, onChange, onRemove, onAddOcap }: MonitoredItemsTableProps) {
  return (
    <div className="sigma-controlplan-table-wrap">
      <table className="sigma-controlplan-table" data-testid="controlplan-items-table">
        <thead>
          <tr>
            <th>Characteristic</th><th>How measured</th><th>Where</th><th>Frequency</th><th>Reason</th>
            <th>Owner</th><th>Accepted</th><th>CTQ</th><th>Improve fix</th><th></th>
          </tr>
        </thead>
        <tbody>
          {items.map((item) => (
            <tr key={item.item_id} data-testid={`controlplan-item-${item.item_id}`}>
              <td><TextInput data-testid={`controlplan-item-${item.item_id}-characteristic`} value={item.characteristic} onChange={(e) => onChange(item.item_id, { characteristic: e.target.value })} /></td>
              <td><TextInput data-testid={`controlplan-item-${item.item_id}-how`} value={item.how_measured} onChange={(e) => onChange(item.item_id, { how_measured: e.target.value })} /></td>
              <td><TextInput data-testid={`controlplan-item-${item.item_id}-where`} value={item.where} onChange={(e) => onChange(item.item_id, { where: e.target.value })} /></td>
              <td><TextInput data-testid={`controlplan-item-${item.item_id}-frequency`} value={item.frequency} onChange={(e) => onChange(item.item_id, { frequency: e.target.value })} /></td>
              <td><TextInput data-testid={`controlplan-item-${item.item_id}-reason`} value={item.frequency_reason} onChange={(e) => onChange(item.item_id, { frequency_reason: e.target.value })} /></td>
              <td>
                <TextInput
                  data-testid={`controlplan-item-${item.item_id}-owner`} value={item.owner_name}
                  onChange={(e) => onChange(item.item_id, { owner_name: e.target.value })} placeholder="(none -- theater flag)"
                />
              </td>
              <td>
                <input
                  type="checkbox" data-testid={`controlplan-item-${item.item_id}-accepted`} checked={item.owner_accepted}
                  onChange={(e) => onChange(item.item_id, { owner_accepted: e.target.checked })}
                />
              </td>
              <td><input type="checkbox" data-testid={`controlplan-item-${item.item_id}-ctq`} checked={item.is_primary_ctq} onChange={(e) => onChange(item.item_id, { is_primary_ctq: e.target.checked })} /></td>
              <td><input type="checkbox" data-testid={`controlplan-item-${item.item_id}-improve`} checked={item.is_improve_change} onChange={(e) => onChange(item.item_id, { is_improve_change: e.target.checked })} /></td>
              <td>
                <Button variant="ghost" size="sm" onClick={() => onAddOcap(item.item_id)} data-testid={`controlplan-item-${item.item_id}-add-ocap`}>+ OCAP</Button>
                <Button variant="danger" size="sm" onClick={() => onRemove(item.item_id)}>Remove</Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
