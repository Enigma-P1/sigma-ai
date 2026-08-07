import { Panel, VerdictBanner } from "../design/components";
import type { ToolDef } from "../app/tools";

export interface ToolPlaceholderProps {
  tool: ToolDef;
}

/** Honest stand-in for every tool this milestone doesn't have a form for.
 * Distinguishes "the engine doesn't support this tool_id yet" (T-06..T-25)
 * from "the engine supports it, but this milestone's UI doesn't have a
 * dedicated form for it yet" (T-02, T-04, T-05) -- both true, different
 * claims, so the message says which one it is. */
export function ToolPlaceholder({ tool }: ToolPlaceholderProps) {
  if (tool.live) {
    return (
      <Panel title={tool.name}>
        <VerdictBanner
          tone="neutral"
          headline="Engine-ready, no dedicated form yet"
          detail={`${tool.id} is registered in the engine (validate / save / prescore all work) but this milestone didn't build its screen. A later milestone adds the form.`}
        />
      </Panel>
    );
  }
  return (
    <Panel title={tool.name}>
      <VerdictBanner
        tone="neutral"
        headline="Not yet built — NOT_YET_BUILT"
        detail={`${tool.id} ships in a later milestone. Nothing to fill in here yet.`}
      />
    </Panel>
  );
}
