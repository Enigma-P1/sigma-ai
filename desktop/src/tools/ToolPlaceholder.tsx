import { Panel, VerdictBanner } from "../design/components";
import type { ToolDef } from "../app/tools";

export interface ToolPlaceholderProps {
  tool: ToolDef;
}

/** Honest stand-in for every tool this milestone doesn't have a form for
 * (T-06 and later, once Intake+Define ship real forms for T-01..T-05).
 * Distinguishes "the engine doesn't support this tool_id yet" from "the
 * engine supports it, but no milestone has built its screen yet" -- both
 * true claims in principle, so the message says which one applies; today
 * every not-yet-built tool is also not yet engine-registered, so only the
 * `!tool.live` branch actually renders, but the `tool.live` branch stays
 * ready for the day a tool is engine-live before its screen ships. */
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
