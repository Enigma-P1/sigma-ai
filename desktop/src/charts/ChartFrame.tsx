import type { ReactNode } from "react";
import type { PlotlyDatum, PlotlyLayout } from "plotly.js-dist-min";
import { Panel, VerdictBanner } from "../design/components";
import type { VerdictTone } from "../design/components";
import { PlotlyChart } from "./PlotlyChart";
import "./ChartFrame.css";

export interface ChartFrameProps {
  title: string;
  /** The plain-English verdict headline every chart carries above it
   * (research §F) — always engine-sourced text, never fabricated here. */
  headline: string;
  tone: VerdictTone;
  detail?: ReactNode;
  /** Caption below the chart — e.g. ScatterChart's EXIT-15 wording. */
  caption?: ReactNode;
  data: PlotlyDatum[];
  layout?: PlotlyLayout;
  height?: number;
  testId?: string;
}

/** The one wrapper every chart in the app renders through (M2 brief:
 * "ONE wrapper component so §F styling lives in one place"): tokens
 * palette + muted grid (via PlotlyChart's base layout) and the verdict-
 * headline slot above the plot are both applied here and nowhere else. */
export function ChartFrame({ title, headline, tone, detail, caption, data, layout, height, testId }: ChartFrameProps) {
  return (
    <div className="sigma-chart-frame" data-testid={testId}>
      <Panel title={title}>
        <VerdictBanner tone={tone} headline={headline} detail={detail} />
        <PlotlyChart data={data} layout={layout} height={height} />
        {caption && <p className="sigma-chart-frame__caption">{caption}</p>}
      </Panel>
    </div>
  );
}
