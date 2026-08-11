import { useRef } from "react";
import { Arrow, Group, Layer, Rect, Stage, Text } from "react-konva";
import type Konva from "konva";
import type { ProcessMapConnector, ProcessMapLane, ProcessMapStep, StepPosition } from "../../api/types";
import { LANE_HEIGHT, STEP_HEIGHT, STEP_WIDTH, laneTopY } from "./processMapLogic";
import { CANVAS_CONNECTOR, CANVAS_LANE_BORDER, CANVAS_LANE_FILL, CANVAS_SELECTED_STROKE, CANVAS_TEXT, CANVAS_TEXT_MUTED, STEP_FILL, STEP_STROKE } from "./canvasColors";
import "./ProcessMapCanvas.css";
import { useStageCapture } from "../../charts/useStageCapture";

const CANVAS_WIDTH = 1040;
const MIN_SCALE = 0.5;
const MAX_SCALE = 2.5;
const ZOOM_STEP = 1.05;

export interface ProcessMapCanvasProps {
  lanes: ProcessMapLane[];
  steps: ProcessMapStep[];
  connectors: ProcessMapConnector[];
  layout: Record<string, StepPosition>;
  selectedStepId: string | null;
  onSelectStep: (stepId: string | null) => void;
  onMoveStep: (stepId: string, x: number, y: number) => void;
}

function connectorPoints(a: StepPosition, b: StepPosition): number[] {
  const startX = a.x + STEP_WIDTH;
  const startY = a.y + STEP_HEIGHT / 2;
  const endX = b.x;
  const endY = b.y + STEP_HEIGHT / 2;
  const midX = (startX + endX) / 2;
  return [startX, startY, midX, startY, midX, endY, endX, endY];
}

/** The interactive canvas map: horizontal swimlane bands, step cards
 * (click to select for the inspector, drag within/between lanes), and
 * connectors drawn with simple orthogonal (elbow) routing. Pan is the
 * Stage's own draggable behavior; zoom is the standard Konva wheel recipe
 * (scale toward the pointer, imperative -- no React state fights Konva's
 * own transform). */
export function ProcessMapCanvas({ lanes, steps, connectors, layout, selectedStepId, onSelectStep, onMoveStep }: ProcessMapCanvasProps) {
  const stageRef = useRef<Konva.Stage>(null);
  useStageCapture("T-06-process-map", stageRef);
  const canvasHeight = Math.max(lanes.length, 1) * LANE_HEIGHT + 40;

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
    <div className="sigma-processmap-canvas-wrap" data-testid="processmap-canvas">
      <Stage
        ref={stageRef}
        width={CANVAS_WIDTH}
        height={canvasHeight}
        draggable
        onWheel={handleWheel}
        onClick={(e) => {
          if (e.target === e.target.getStage()) onSelectStep(null);
        }}
      >
        <Layer>
          {lanes.map((lane, i) => (
            <Group key={lane.lane_id}>
              <Rect x={0} y={laneTopY(i)} width={CANVAS_WIDTH * 2} height={LANE_HEIGHT} fill={CANVAS_LANE_FILL[i % 2]} stroke={CANVAS_LANE_BORDER} strokeWidth={1} />
              <Text x={10} y={laneTopY(i) + 10} width={150} text={lane.name} fontSize={14} fontStyle="600" fill={CANVAS_TEXT} />
              <Text x={10} y={laneTopY(i) + 30} width={150} text={lane.owner ? `Owner: ${lane.owner}` : "No owner set"} fontSize={11} fill={CANVAS_TEXT_MUTED} />
            </Group>
          ))}

          {connectors.map((c, i) => {
            const a = layout[c.from_step];
            const b = layout[c.to_step];
            if (!a || !b) return null;
            return (
              <Group key={`${c.from_step}->${c.to_step}-${i}`}>
                <Arrow points={connectorPoints(a, b)} stroke={CANVAS_CONNECTOR} fill={CANVAS_CONNECTOR} strokeWidth={2} pointerLength={8} pointerWidth={8} />
                {c.label && (
                  <Text
                    x={(a.x + STEP_WIDTH + b.x) / 2 - 30} y={(a.y + b.y) / 2 - 14}
                    width={60} align="center" text={c.label} fontSize={10} fill={CANVAS_TEXT_MUTED}
                  />
                )}
              </Group>
            );
          })}

          {steps.map((step) => {
            const pos = layout[step.step_id] ?? { x: 0, y: 0 };
            const selected = step.step_id === selectedStepId;
            return (
              <Group
                key={step.step_id}
                x={pos.x}
                y={pos.y}
                draggable
                onClick={(e) => {
                  e.cancelBubble = true;
                  onSelectStep(step.step_id);
                }}
                onDragEnd={(e) => onMoveStep(step.step_id, e.target.x(), e.target.y())}
                dragBoundFunc={(p) => ({ x: p.x, y: Math.min(Math.max(p.y, 0), Math.max(lanes.length, 1) * LANE_HEIGHT - STEP_HEIGHT + 20) })}
              >
                <Rect
                  width={STEP_WIDTH} height={STEP_HEIGHT} cornerRadius={8}
                  fill={STEP_FILL[step.step_type]} stroke={selected ? CANVAS_SELECTED_STROKE : STEP_STROKE[step.step_type]}
                  strokeWidth={selected ? 3 : 1.5} shadowBlur={selected ? 6 : 0} shadowOpacity={0.25}
                />
                <Text x={8} y={8} width={STEP_WIDTH - 16} text={step.name} fontSize={12} fontStyle="600" fill={CANVAS_TEXT} wrap="word" />
                <Text
                  x={8} y={STEP_HEIGHT - 20} width={STEP_WIDTH - 16}
                  text={step.time_minutes != null ? `${step.time_minutes} min` : "no time"}
                  fontSize={10} fill={CANVAS_TEXT_MUTED}
                />
              </Group>
            );
          })}
        </Layer>
      </Stage>
    </div>
  );
}
