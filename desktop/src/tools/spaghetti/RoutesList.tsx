import { Button, Panel, StatusPill } from "../../design/components";
import type { LayoutMode, Operator, RouteMetrics, SpaghettiRoute } from "../../api/types";
import { operatorName } from "./spaghettiLogic";

export interface RoutesListProps {
  routes: SpaghettiRoute[];
  operators: Operator[];
  metricsByRouteId: Record<string, RouteMetrics> | null;
  onRemove: (routeId: string) => void;
}

const MODE_TONE: Record<LayoutMode, "accent" | "pass"> = { current: "accent", proposed: "pass" };

/** Every traced route, both layout modes, with the engine's own computed
 * distance/time once a save has echoed metrics back (M2 build brief:
 * "computed distance/time from the ENGINE's response after save") --
 * nothing rendered here is computed client-side. */
export function RoutesList({ routes, operators, metricsByRouteId, onRemove }: RoutesListProps) {
  return (
    <Panel title="Routes" subtitle="Every traced trip, current and proposed">
      {routes.length === 0 && <p>No routes traced yet.</p>}
      <ul className="sigma-spaghetti-routes">
        {routes.map((route, i) => {
          const m = metricsByRouteId?.[route.route_id];
          return (
            <li key={route.route_id} className="sigma-spaghetti-route-row" data-testid={`spaghetti-route-${i}`}>
              <div className="sigma-spaghetti-route-row__header">
                <StatusPill tone={MODE_TONE[route.layout_mode]} label={route.layout_mode} />
                <span>{route.trip_label}</span>
                <span className="sigma-spaghetti-route-row__operator">{operatorName(operators, route.operator_id)}</span>
                <span>{route.frequency_per_day}/day</span>
                <Button variant="ghost" size="sm" onClick={() => onRemove(route.route_id)} data-testid={`spaghetti-route-${i}-remove`}>×</Button>
              </div>
              <div data-testid={`spaghetti-route-${i}-metrics`} className="sigma-spaghetti-route-row__metrics">
                {m ? (
                  <>
                    <span data-testid={`spaghetti-route-${i}-distance`}>{m.distance_per_trip.toFixed(1)} {m.unit}/trip</span>
                    {" · "}
                    <span data-testid={`spaghetti-route-${i}-daily-distance`}>{m.daily_distance.toFixed(1)} {m.unit}/day</span>
                    {" · "}
                    <span data-testid={`spaghetti-route-${i}-walk-time`}>{m.walk_time_minutes_per_trip.toFixed(1)} min/trip</span>
                  </>
                ) : (
                  <span>not yet computed — save to see the engine's numbers</span>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </Panel>
  );
}
