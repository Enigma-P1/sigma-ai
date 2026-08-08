import { useRef } from "react";
import { Circle, Group, Layer, Line, Rect, Stage, Text } from "react-konva";
import type Konva from "konva";
import type { CausePosition, FishboneBranch, FishboneCause } from "../../api/types";
import { FISHBONE_BRANCHES } from "../../api/types";
import {
  BRANCH_LABELS,
  CANVAS_HEIGHT,
  CANVAS_WIDTH,
  CARD_HEIGHT,
  CARD_WIDTH,
  HEAD_X,
  SPINE_START_X,
  SPINE_Y,
  branchLabelPoint,
  branchSlotX,
  isUnproven,
} from "./fishboneLogic";
import {
  CANVAS_BRANCH,
  CANVAS_HEAD_FILL,
  CANVAS_HEAD_STROKE,
  CANVAS_LINK,
  CANVAS_SELECTED_STROKE,
  CANVAS_SPINE,
  CANVAS_TEXT,
  CANVAS_TEXT_MUTED,
  CAUSE_FILL,
  CAUSE_STROKE,
  CAUSE_TEXT,
} from "./canvasColors";
import "./FishboneCanvas.css";

const MIN_SCALE = 0.5;
const MAX_SCALE = 2.5;
const ZOOM_STEP = 1.05;

export interface FishboneCanvasProps {
  effectText: string;
  causes: FishboneCause[];
  layout: Record<string, CausePosition>;
  selectedCauseId: string | null;
  onSelectCause: (causeId: string | null) => void;
  onMoveCause: (causeId: string, x: number, y: number) => void;
  onAddCause: (branch: FishboneBranch) => void;
}

/** The fishbone canvas: a spine ending in the effect "head", six branch
 * lines (three above, three below) each clickable to add a cause, and
 * cause cards positioned along their branch -- sub-causes (parent_
 * cause_id set) draw a link line back to their parent and sit indented
 * further out, the 5-Whys chain rendered as a visible stack. */
export function FishboneCanvas({ effectText, causes, layout, selectedCauseId, onSelectCause, onMoveCause, onAddCause }: FishboneCanvasProps) {
  const stageRef = useRef<Konva.Stage>(null);

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
    <div className="sigma-fishbone-canvas-wrap" data-testid="fishbone-canvas">
      <Stage
        ref={stageRef} width={CANVAS_WIDTH} height={CANVAS_HEIGHT} draggable onWheel={handleWheel}
        onClick={(e) => {
          if (e.target === e.target.getStage()) onSelectCause(null);
        }}
      >
        <Layer>
          {/* Spine + effect head */}
          <Line points={[SPINE_START_X, SPINE_Y, HEAD_X, SPINE_Y]} stroke={CANVAS_SPINE} strokeWidth={3} />
          <Rect x={HEAD_X} y={SPINE_Y - 32} width={CANVAS_WIDTH - HEAD_X - 30} height={64} cornerRadius={8} fill={CANVAS_HEAD_FILL} stroke={CANVAS_HEAD_STROKE} strokeWidth={2} />
          <Text x={HEAD_X + 10} y={SPINE_Y - 24} width={CANVAS_WIDTH - HEAD_X - 50} text="EFFECT" fontSize={10} fill={CANVAS_TEXT_MUTED} fontStyle="600" />
          <Text x={HEAD_X + 10} y={SPINE_Y - 8} width={CANVAS_WIDTH - HEAD_X - 50} text={effectText || "(effect statement not written yet)"} fontSize={12} fill={CANVAS_TEXT} wrap="word" />

          {/* Six branch lines + clickable labels */}
          {FISHBONE_BRANCHES.map((branch) => {
            const slotX = branchSlotX(branch);
            const label = branchLabelPoint(branch);
            return (
              <Group key={branch}>
                <Line points={[slotX, SPINE_Y, label.x, label.y]} stroke={CANVAS_BRANCH} strokeWidth={2} />
                <Group onClick={(e) => { e.cancelBubble = true; onAddCause(branch); }} onTap={(e) => { e.cancelBubble = true; onAddCause(branch); }}>
                  <Rect x={label.x - 55} y={label.y - 14} width={110} height={26} cornerRadius={13} fill="#ffffff" stroke={CANVAS_BRANCH} strokeWidth={1.5} />
                  <Text x={label.x - 55} y={label.y - 6} width={110} align="center" text={`+ ${BRANCH_LABELS[branch]}`} fontSize={11} fontStyle="600" fill={CANVAS_TEXT} />
                </Group>
              </Group>
            );
          })}

          {/* Link lines from each sub-cause back to its parent */}
          {causes.filter((c) => c.parent_cause_id).map((c) => {
            const from = layout[c.parent_cause_id as string];
            const to = layout[c.cause_id];
            if (!from || !to) return null;
            return (
              <Line
                key={`link-${c.cause_id}`}
                points={[from.x + CARD_WIDTH / 2, from.y + CARD_HEIGHT / 2, to.x + CARD_WIDTH / 2, to.y + CARD_HEIGHT / 2]}
                stroke={CANVAS_LINK} strokeWidth={1.5} dash={[4, 3]}
              />
            );
          })}

          {/* Cause cards */}
          {causes.map((cause) => {
            const pos = layout[cause.cause_id] ?? { x: 0, y: 0 };
            const selected = cause.cause_id === selectedCauseId;
            return (
              <Group
                key={cause.cause_id} x={pos.x} y={pos.y} draggable
                onClick={(e) => { e.cancelBubble = true; onSelectCause(cause.cause_id); }}
                onDragEnd={(e) => onMoveCause(cause.cause_id, e.target.x(), e.target.y())}
              >
                <Rect
                  width={CARD_WIDTH} height={CARD_HEIGHT} cornerRadius={8}
                  fill={CAUSE_FILL[cause.status]} stroke={selected ? CANVAS_SELECTED_STROKE : CAUSE_STROKE[cause.status]}
                  strokeWidth={selected ? 3 : 1.5} shadowBlur={selected ? 6 : 0} shadowOpacity={0.25}
                />
                <Text x={8} y={6} width={CARD_WIDTH - 16} text={cause.text || "(new cause)"} fontSize={11} fill={CAUSE_TEXT[cause.status]} wrap="word" />
                {cause.status === "ruled_out" && (
                  <Line points={[6, CARD_HEIGHT / 2, CARD_WIDTH - 6, CARD_HEIGHT / 2]} stroke={CAUSE_STROKE.ruled_out} strokeWidth={1.5} />
                )}
                {isUnproven(cause) && <Circle x={CARD_WIDTH - 10} y={10} radius={4} fill="#9a6700" />}
              </Group>
            );
          })}
        </Layer>
      </Stage>
    </div>
  );
}
