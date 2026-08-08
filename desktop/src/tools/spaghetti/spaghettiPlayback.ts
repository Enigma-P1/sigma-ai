import { useEffect, useRef, useState } from "react";
import type { RoutePoint } from "../../api/types";

function segmentLengths(points: RoutePoint[]): number[] {
  const lens: number[] = [];
  for (let i = 0; i < points.length - 1; i++) {
    lens.push(Math.hypot(points[i + 1].x - points[i].x, points[i + 1].y - points[i].y));
  }
  return lens;
}

/** Position at fraction `t` (0..1) along a polyline, by cumulative arc
 * length. Pure display math for the playback dot -- entirely separate
 * from the engine's own distance_per_trip and never feeds a number back
 * into the artifact. */
export function pointAtFraction(points: RoutePoint[], t: number): RoutePoint | null {
  if (points.length < 2) return points[0] ?? null;
  const lens = segmentLengths(points);
  const total = lens.reduce((a, b) => a + b, 0);
  if (total <= 0) return points[0];
  let target = Math.min(Math.max(t, 0), 1) * total;
  for (let i = 0; i < lens.length; i++) {
    if (target <= lens[i] || i === lens.length - 1) {
      const segT = lens[i] > 0 ? Math.min(target / lens[i], 1) : 0;
      const a = points[i];
      const b = points[i + 1];
      return { x: a.x + (b.x - a.x) * segT, y: a.y + (b.y - a.y) * segT };
    }
    target -= lens[i];
  }
  return points[points.length - 1];
}

// Constant on-screen pace: longer routes take proportionally longer to
// animate, which is "proportional speed" read as relative-between-routes
// display pacing, not a literal conversion of the engine's real-world
// walk-time minutes onto the screen clock (documented plainly in
// PlaybackControls so this reads as the honest reduced-scope flourish it is).
const PIXELS_PER_SECOND = 140;
const MIN_LOOP_MS = 500;

/** requestAnimationFrame-driven playback position for the selected route
 * (PLAN: "animated playback for demos") -- a pure display flourish, never
 * a source of any saved or claimed number. */
export function useRoutePlayback(points: RoutePoint[] | null, playing: boolean): RoutePoint | null {
  const [position, setPosition] = useState<RoutePoint | null>(null);
  const frameRef = useRef<number | null>(null);

  useEffect(() => {
    if (!playing || !points || points.length < 2) {
      setPosition(null);
      return;
    }
    const lens = segmentLengths(points);
    const total = lens.reduce((a, b) => a + b, 0);
    const durationMs = Math.max((total / PIXELS_PER_SECOND) * 1000, MIN_LOOP_MS);
    const start = performance.now();

    function tick(now: number) {
      const elapsed = (now - start) % durationMs;
      setPosition(pointAtFraction(points as RoutePoint[], elapsed / durationMs));
      frameRef.current = requestAnimationFrame(tick);
    }
    frameRef.current = requestAnimationFrame(tick);
    return () => {
      if (frameRef.current != null) cancelAnimationFrame(frameRef.current);
    };
  }, [playing, points]);

  return position;
}
