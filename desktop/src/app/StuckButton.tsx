import { useState } from "react";
import { Button, Modal, VerdictBanner } from "../design/components";
import { DEFINE_STUCK_TREE, isStuckLeaf } from "./stuckTree";
import type { StuckNode } from "./stuckTree";
import "./StuckButton.css";

export interface StuckButtonProps {
  onNavigateToTool: (toolId: string) => void;
}

/** The "I'm stuck" button (PLAN §4.2 item 3): opens an offline, hardcoded
 * decision tree for the Define phase -- no AI, no network call. */
export function StuckButton({ onNavigateToTool }: StuckButtonProps) {
  const [open, setOpen] = useState(false);
  const [node, setNode] = useState<StuckNode>(DEFINE_STUCK_TREE);
  const [trail, setTrail] = useState<string[]>([]);

  function reset() {
    setNode(DEFINE_STUCK_TREE);
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

  return (
    <>
      <Button variant="secondary" size="sm" onClick={() => setOpen(true)} data-testid="stuck-button">
        I'm stuck — what do I use now?
      </Button>
      {open && (
        <Modal title="What do I use now?" onClose={close}>
          <p className="sigma-stuck__intro">
            An offline routing tree for the Define phase — a couple of plain questions, no AI involved.
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
          ) : (
            <>
              <VerdictBanner tone="pass" headline={node.recommendation} detail={node.explanation} />
              <div className="sigma-stuck__footer">
                {node.toolId && (
                  <Button
                    variant="primary"
                    onClick={() => {
                      onNavigateToTool(node.toolId as string);
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
            </>
          )}
        </Modal>
      )}
    </>
  );
}
