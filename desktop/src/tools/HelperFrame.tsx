import { Panel, VerdictBanner } from "../design/components";
import type { HelperFrameContent } from "./helperFrameTypes";
import { splitCite } from "./rubricCite";
import "./HelperFrame.css";

export interface HelperFrameProps {
  content: HelperFrameContent;
}

/** The five-part helper frame panel (PLAN §4.3), collapsible, always
 * present on a tool screen. Renders a PLACEHOLDER banner up front for
 * tools that don't have real content yet, so nobody mistakes filler for
 * the real rubric. Every text field runs through splitCite() first
 * (Jordan usability fix): an embedded rubric code (R-XXX-NN) never prints
 * on screen, but survives as that same text's hover title -- a no-op for
 * any string that doesn't carry one. */
export function HelperFrame({ content }: HelperFrameProps) {
  const whatThisIs = splitCite(content.whatThisIs);
  const whenToUse = splitCite(content.whenToUse);
  const whenNotTo = splitCite(content.whenNotTo);

  return (
    <Panel title="How this tool works" subtitle="What it is, when to use it, and what good looks like" collapsible defaultOpen>
      {content.isPlaceholder && (
        <div className="sigma-helper__placeholder">
          <VerdictBanner tone="neutral" headline="PLACEHOLDER CONTENT" detail="Real helper text ships when this tool is built." />
        </div>
      )}

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">What this is</div>
        <p className="sigma-helper__body-text" title={whatThisIs.cite ?? undefined}>{whatThisIs.text}</p>
      </div>

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">When to use it</div>
        <p className="sigma-helper__body-text" title={whenToUse.cite ?? undefined}>{whenToUse.text}</p>
      </div>

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">When not to</div>
        <p className="sigma-helper__body-text" title={whenNotTo.cite ?? undefined}>{whenNotTo.text}</p>
      </div>

      {content.fieldGuidance.length > 0 && (
        <div className="sigma-helper__section">
          <div className="sigma-helper__section-title">Exactly what goes in each field</div>
          {content.fieldGuidance.map((fg) => {
            const good = splitCite(fg.good);
            const bad = splitCite(fg.bad);
            return (
              <div className="sigma-helper__field" key={fg.field}>
                <div className="sigma-helper__field-name">{fg.field}</div>
                <p className="sigma-helper__example sigma-helper__example--good" title={good.cite ?? undefined}>✓ {good.text}</p>
                <p className="sigma-helper__example sigma-helper__example--bad" title={bad.cite ?? undefined}>✗ {bad.text}</p>
              </div>
            );
          })}
        </div>
      )}

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">What good looks like</div>
        <ul className="sigma-helper__list">
          {content.whatGoodLooksLike.map((item) => {
            const { text, cite } = splitCite(item);
            return <li key={item} title={cite ?? undefined}>{text}</li>;
          })}
        </ul>
      </div>

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">Common mistakes</div>
        <ul className="sigma-helper__list">
          {content.commonMistakes.map((item) => {
            const { text, cite } = splitCite(item);
            return <li key={item} title={cite ?? undefined}>{text}</li>;
          })}
        </ul>
      </div>
    </Panel>
  );
}
