import { useEffect, useState } from "react";
import { Button, Modal, VerdictBanner } from "../design/components";
import { STUCK_TREE_BY_PHASE, doneToolIdsFromProject, isStuckLeaf, nextNotDoneToolId, stuckTreeNotBuiltLeaf } from "./stuckTree";
import type { StuckNode } from "./stuckTree";
import { getVisitedTools } from "./toolVisitedStore";
import { toolById } from "./tools";
import type { Phase, ProjectMetadata } from "../api/types";
import "./StuckButton.css";

export interface StuckButtonProps {
  phase: Phase;
  project: ProjectMetadata;
  onNavigateToTool: (toolId: string) => void;
}

/** The "I'm stuck" button (PLAN §4.2 item 3): opens an offline, hardcoded
 * decision tree -- no AI, no network call. Phase-aware (Jordan usability
 * fix): the tree shown matches whichever phase is currently active
 * (stuckTree.ts's STUCK_TREE_BY_PHASE), with an honest fallback for a
 * phase that doesn't have one yet, rather than always showing Define's
 * questions. Completion-aware (same fix): a leaf's recommendation is
 * routed through nextNotDoneToolId before it's shown, so this never
 * points at a tool the project has already completed -- it offers the
 * next not-done tool in phase order instead. */
export function StuckButton({ phase, project, onNavigateToTool }: StuckButtonProps) {
  const tree = STUCK_TREE_BY_PHASE[phase];
  const [open, setOpen] = useState(false);
  const [node, setNode] = useState<StuckNode>(tree ?? stuckTreeNotBuiltLeaf(phase));
  const [trail, setTrail] = useState<string[]>([]);

  // Re-arm to this phase's own root whenever the active phase changes
  // (e.g. the user opens the modal in Define, closes it, moves to
  // Measure) so the tree shown always matches where they currently are.
  useEffect(() => {
    setNode(tree ?? stuckTreeNotBuiltLeaf(phase));
    setTrail([]);
  }, [phase, tree]);

  function reset() {
    setNode(tree ?? stuckTreeNotBuiltLeaf(phase));
    setTrail([]);
  }

  function close() {
    setOpen(false);
    reset();
  }

  function answer(yes: boolean) {
    if (isStuckLeaf(node)) return;
    setTrail((t) => [...t, `${node.question} → ${yes ? "Yes" : "No"}`]);
    setNode(yes ? node.yes : node.no);
  }

  // Completion-aware substitution -- only meaningful inside a real tree
  // (`tree` non-null): a leaf's own toolId, or the phase's next not-done
  // live tool if that one's already done, or null if every live tool in
  // this phase already reads Done. The "no tree for this phase yet"
  // fallback leaf never has a toolId and skips this entirely, so it never
  // shows a "Go to this tool" button pointing at some other, unrelated tool.
  const doneToolIds = new Set([...doneToolIdsFromProject(project), ...getVisitedTools(project.project_id)]);
  const leafToolId = tree && isStuckLeaf(node) ? node.toolId : undefined;
  const routedToolId = tree && isStuckLeaf(node) ? nextNotDoneToolId(phase, leafToolId, doneToolIds) : null;
  const substituted = leafToolId != null && routedToolId !== leafToolId;
  const routedTool = routedToolId ? toolById(routedToolId) : null;

  return (
    <>
      <Button variant="secondary" size="sm" onClick={() => setOpen(true)} data-testid="stuck-button">
        I'm stuck — what do I use now?
      </Button>
      {open && (
        <Modal title="What do I use now?" onClose={close}>
          <p className="sigma-stuck__intro">
            An offline routing tree for the {phase} phase — a couple of plain questions, no AI involved.
          </p>
          {trail.length > 0 && (
            <ul className="sigma-stuck__trail">
              {trail.map((line) => (
                <li key={line}>{line}</li>
              ))}
            </ul>
          )}
          {!isStuckLeaf(node) ? (
            <>
              <p className="sigma-stuck__question" data-testid="stuck-question">
                {node.question}
              </p>
              <div className="sigma-stuck__actions">
                <Button variant="primary" onClick={() => answer(true)} data-testid="stuck-answer-yes">
                  Yes
                </Button>
                <Button variant="secondary" onClick={() => answer(false)} data-testid="stuck-answer-no">
                  No
                </Button>
              </div>
            </>
          ) : !tree ? (
            // No stuck-tree written for this phase yet -- the fallback
            // leaf's own text, verbatim, no tool button (nothing routed).
            <VerdictBanner tone="neutral" headline={node.recommendation} detail={node.explanation} />
          ) : routedTool ? (
            <VerdictBanner
              tone="pass"
              headline={substituted ? `Already done — try next: ${routedTool.name} (${routedTool.id})` : node.recommendation}
              detail={
                substituted
                  ? `${node.explanation} (You've already completed ${leafToolId ? (toolById(leafToolId)?.name ?? leafToolId) : "that tool"}, so this points at the next tool in ${phase} that isn't done yet.)`
                  : node.explanation
              }
            />
          ) : (
            <VerdictBanner
              tone="pass"
              headline={`Every tool in ${phase} already looks done`}
              detail="If you're still stuck, the phase's exit gate or the next phase's tools are probably the more useful place to look."
            />
          )}
          {isStuckLeaf(node) && (
            <div className="sigma-stuck__footer">
              {routedToolId && (
                <Button
                  variant="primary"
                  onClick={() => {
                    onNavigateToTool(routedToolId);
                    close();
                  }}
                  data-testid="stuck-go-to-tool"
                >
                  Go to this tool
                </Button>
              )}
              <Button variant="ghost" onClick={reset}>
                Start over
              </Button>
            </div>
          )}
        </Modal>
      )}
    </>
  );
}
