import { useEffect, useMemo, useRef, useState } from "react";
import { Circle, Group, Image as KonvaImage, Layer, Line, Stage, Text } from "react-konva";
import type Konva from "konva";
import type { Calibration, LayoutMode, Operator, SpaghettiRoute } from "../../api/types";
import {
  CALIBRATION_LINE_COLOR, CALIBRATION_POINT_FILL, CALIBRATION_TEXT,
  PLAYBACK_DOT_FILL, TRACE_DRAFT_COLOR, TRACE_DRAFT_POINT_FILL, colorForOperator,
} from "./canvasColors";
import { heatmapStrokeWidth, pointsToFlat } from "./spaghettiLogic";
import type { DraftPoint } from "./spaghettiLogic";
import { useRoutePlayback } from "./spaghettiPlayback";
import "./SpaghettiCanvas.css";

const STAGE_WIDTH = 900;
const STAGE_HEIGHT = 600;
const MIN_SCALE = 0.5;
const MAX_SCALE = 2.5;
const ZOOM_STEP = 1.05;

export type CanvasMode = "idle" | "calibrate" | "trace";

export interface SpaghettiCanvasProps {
  imageSrc: string | null;
  imageWidth: number;
  imageHeight: number;
  mode: CanvasMode;
  calibration: Calibration | null;
  calibrationDraft: DraftPoint[];
  operators: Operator[];
  routes: SpaghettiRoute[];
  traceDraft: DraftPoint[];
  activeLayoutMode: LayoutMode;
  heatmapOn: boolean;
  playbackRouteId: string | null;
  playing: boolean;
  onCanvasClick: (point: DraftPoint) => void;
}

function useHtmlImage(src: string | null): HTMLImageElement | null {
  const [img, setImg] = useState<HTMLImageElement | null>(null);
  useEffect(() => {
    if (!src) {
      setImg(null);
      return;
    }
    const el = new window.Image();
    el.onload = () => setImg(el);
    el.src = src;
    return () => {
      el.onload = null;
    };
  }, [src]);
  return img;
}

/** T-07's canvas: the uploaded floor plan as a Konva.Image background,
 * click-to-place calibration/trace points (panning is disabled while
 * either mode is active, so a precise click can't be read as a drag),
 * traced routes color-coded by operator with the heatmap toggle scaling
 * line width, and the playback dot for the selected route. */
export function SpaghettiCanvas(props: SpaghettiCanvasProps) {
  const {
    imageSrc, imageWidth, imageHeight, mode, calibration, calibrationDraft, operators, routes,
    traceDraft, activeLayoutMode, heatmapOn, playbackRouteId, playing, onCanvasClick,
  } = props;
  const stageRef = useRef<Konva.Stage>(null);
  const image = useHtmlImage(imageSrc);

  const visibleRoutes = useMemo(() => routes.filter((r) => r.layout_mode === activeLayoutMode), [routes, activeLayoutMode]);
  const maxFrequency = useMemo(() => Math.max(0, ...visibleRoutes.map((r) => r.frequency_per_day)), [visibleRoutes]);
  const playbackRoute = useMemo(() => routes.find((r) => r.route_id === playbackRouteId) ?? null, [routes, playbackRouteId]);
  const dot = useRoutePlayback(playbackRoute?.points ?? null, playing);

  function handleClick() {
    if (mode === "idle") return;
    // getRelativePointerPosition (not getPointerPosition) so a click always
    // lands on the same image-space coordinate the artifact stores,
    // regardless of however the user has panned/zoomed to get a better look.
    const pos = stageRef.current?.getRelativePointerPosition();
    if (pos) onCanvasClick({ x: pos.x, y: pos.y });
  }

  function handleWheel(e: Konva.KonvaEventObject<WheelEvent>) {
    e.evt.preventDefault();
    const stage = stageRef.current;
    const pointer = stage?.getPointerPosition();
    if (!stage || !pointer) return;
    const oldScale = stage.scaleX();
    const mousePointTo = { x: (pointer.x - stage.x()) / oldScale, y: (pointer.y - stage.y()) / oldScale };
    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const rawScale = direction > 0 ? oldScale * ZOOM_STEP : oldScale / ZOOM_STEP;
    const newScale = Math.min(Math.max(rawScale, MIN_SCALE), MAX_SCALE);
    stage.scale({ x: newScale, y: newScale });
    stage.position({ x: pointer.x - mousePointTo.x * newScale, y: pointer.y - mousePointTo.y * newScale });
    stage.batchDraw();
  }

  return (
    <div className="sigma-spaghetti-canvas-wrap" data-testid="spaghetti-canvas">
      <Stage ref={stageRef} width={STAGE_WIDTH} height={STAGE_HEIGHT} draggable={mode === "idle"} onWheel={handleWheel} onClick={handleClick}>
        <Layer>
          {image && <KonvaImage image={image} x={0} y={0} width={imageWidth} height={imageHeight} />}

          {visibleRoutes.map((route) => {
            const operator = operators.find((o) => o.operator_id === route.operator_id);
            const width = heatmapOn ? heatmapStrokeWidth(route.frequency_per_day, maxFrequency) : 3;
            return (
              <Line
                key={route.route_id} points={pointsToFlat(route.points)}
                stroke={colorForOperator(operator?.color_index ?? 0)} strokeWidth={width}
                opacity={heatmapOn ? 0.5 + (0.4 * (width - 2)) / 8 : 0.9}
                lineCap="round" lineJoin="round"
              />
            );
          })}

          {traceDraft.length > 0 && (
            <Group>
              <Line points={pointsToFlat(traceDraft)} stroke={TRACE_DRAFT_COLOR} strokeWidth={3} dash={[6, 4]} lineCap="round" />
              {traceDraft.map((p, i) => (
                <Circle key={i} x={p.x} y={p.y} radius={4} fill={TRACE_DRAFT_POINT_FILL} stroke={TRACE_DRAFT_COLOR} strokeWidth={1.5} />
              ))}
            </Group>
          )}

          {(calibration || calibrationDraft.length > 0) && (
            <Group>
              {calibration && (
                <>
                  <Line
                    points={[calibration.point_a.x, calibration.point_a.y, calibration.point_b.x, calibration.point_b.y]}
                    stroke={CALIBRATION_LINE_COLOR} strokeWidth={2}
                  />
                  <Text
                    x={(calibration.point_a.x + calibration.point_b.x) / 2}
                    y={(calibration.point_a.y + calibration.point_b.y) / 2 - 18}
                    text={`${calibration.real_length} ${calibration.unit}`} fontSize={12} fill={CALIBRATION_TEXT}
                  />
                </>
              )}
              {(calibration ? [calibration.point_a, calibration.point_b] : calibrationDraft).map((p, i) => (
                <Circle key={i} x={p.x} y={p.y} radius={5} fill={CALIBRATION_POINT_FILL} stroke={CALIBRATION_LINE_COLOR} strokeWidth={2} />
              ))}
            </Group>
          )}

          {dot && <Circle x={dot.x} y={dot.y} radius={7} fill={PLAYBACK_DOT_FILL} stroke="#ffffff" strokeWidth={2} />}
        </Layer>
      </Stage>
    </div>
  );
}
