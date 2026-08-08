import { Button, Field, SelectInput } from "../../design/components";
import type { LayoutMode, SpaghettiRoute } from "../../api/types";

export interface PlaybackControlsProps {
  routes: SpaghettiRoute[];
  activeLayoutMode: LayoutMode;
  selectedRouteId: string | null;
  playing: boolean;
  onSelectRoute: (routeId: string) => void;
  onTogglePlay: () => void;
}

/** Animated playback (PLAN: "animated playback for demos") -- a dot
 * traveling the selected route at a constant on-screen pace, longer
 * routes taking proportionally longer (spaghettiPlayback.ts). Pure
 * display: it never computes or claims a number, and never blocks
 * anything else in the tool while mid-animation. */
export function PlaybackControls({ routes, activeLayoutMode, selectedRouteId, playing, onSelectRoute, onTogglePlay }: PlaybackControlsProps) {
  const visible = routes.filter((r) => r.layout_mode === activeLayoutMode);
  return (
    <div className="sigma-spaghetti-playback">
      <Field label="Route to animate" htmlFor="spaghetti-playback-route-select">
        <SelectInput
          id="spaghetti-playback-route-select" data-testid="spaghetti-playback-route-select"
          value={selectedRouteId ?? ""} onChange={(e) => onSelectRoute(e.target.value)}
        >
          <option value="">Select a route…</option>
          {visible.map((r) => (
            <option key={r.route_id} value={r.route_id}>{r.trip_label}</option>
          ))}
        </SelectInput>
      </Field>
      <Button
        variant="secondary" disabled={!selectedRouteId} onClick={onTogglePlay}
        data-testid="spaghetti-playback-toggle" data-playing={playing}
      >
        {playing ? "Pause" : "Play"}
      </Button>
    </div>
  );
}
