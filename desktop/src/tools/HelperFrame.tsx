import { Panel, VerdictBanner } from "../design/components";
import type { HelperFrameContent } from "./helperFrameTypes";
import "./HelperFrame.css";

export interface HelperFrameProps {
  content: HelperFrameContent;
}

/** The five-part helper frame panel (PLAN §4.3), collapsible, always
 * present on a tool screen. Renders a PLACEHOLDER banner up front for
 * tools that don't have real content yet, so nobody mistakes filler for
 * the real rubric. */
export function HelperFrame({ content }: HelperFrameProps) {
  return (
    <Panel title="How this tool works" subtitle="What it is, when to use it, and what good looks like" collapsible defaultOpen>
      {content.isPlaceholder && (
        <div className="sigma-helper__placeholder">
          <VerdictBanner tone="neutral" headline="PLACEHOLDER CONTENT" detail="Real helper text ships when this tool is built." />
        </div>
      )}

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">What this is</div>
        <p className="sigma-helper__body-text">{content.whatThisIs}</p>
      </div>

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">When to use it</div>
        <p className="sigma-helper__body-text">{content.whenToUse}</p>
      </div>

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">When not to</div>
        <p className="sigma-helper__body-text">{content.whenNotTo}</p>
      </div>

      {content.fieldGuidance.length > 0 && (
        <div className="sigma-helper__section">
          <div className="sigma-helper__section-title">Exactly what goes in each field</div>
          {content.fieldGuidance.map((fg) => (
            <div className="sigma-helper__field" key={fg.field}>
              <div className="sigma-helper__field-name">{fg.field}</div>
              <p className="sigma-helper__example sigma-helper__example--good">✓ {fg.good}</p>
              <p className="sigma-helper__example sigma-helper__example--bad">✗ {fg.bad}</p>
            </div>
          ))}
        </div>
      )}

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">What good looks like</div>
        <ul className="sigma-helper__list">
          {content.whatGoodLooksLike.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>

      <div className="sigma-helper__section">
        <div className="sigma-helper__section-title">Common mistakes</div>
        <ul className="sigma-helper__list">
          {content.commonMistakes.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </div>
    </Panel>
  );
}
