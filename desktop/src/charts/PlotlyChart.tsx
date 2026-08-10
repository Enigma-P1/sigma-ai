import { useEffect, useRef } from "react";
import Plotly from "plotly.js-dist-min";
import type { PlotlyDatum, PlotlyLayout } from "plotly.js-dist-min";
import { CHART_COLORS, CHART_FONT_FAMILY } from "./palette";
import { registerChart } from "./capture";

/** `plotly.js-dist-min`'s bundled types are partial and omit toImage, which
 * the runtime does provide. Declared narrowly here rather than casting the
 * whole module to any, so the one untyped call is visible and the rest of
 * PlotlyStatic stays type-checked. */
type WithToImage = {
  toImage: (el: HTMLElement, opts: { format: "png"; width: number; height: number; scale?: number }) => Promise<string>;
};

export interface PlotlyChartProps {
  data: PlotlyDatum[];
  layout?: PlotlyLayout;
  height?: number;
  /** Names this chart for report export. Charts without a key are simply
   * not capturable -- decorative or duplicated plots should leave it off
   * rather than register under a colliding name. */
  captureKey?: string;
  /** Fingerprint of the series this chart was drawn from, so the engine can
   * refuse the image if the data has since moved (charts/capture.ts). */
  captureHash?: string | null;
}

/** Raw Plotly binding — internal to charts/. Every chart-specific
 * component (Histogram, RunChart, ParetoChart, ScatterChart, BoxChart,
 * T-13's ImrChart) renders through ChartFrame, never this directly, so
 * the §F base layout (tokens palette, muted grid) lives in exactly one
 * place (ChartFrame.tsx). */
export function PlotlyChart({ data, layout, height = 340, captureKey, captureHash = null }: PlotlyChartProps) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const { xaxis, yaxis, ...restLayout } = (layout ?? {}) as Record<string, unknown>;
    const mergedLayout: PlotlyLayout = {
      autosize: true,
      height,
      margin: { l: 56, r: 24, t: 16, b: 44 },
      paper_bgcolor: "transparent",
      plot_bgcolor: "transparent",
      font: { family: CHART_FONT_FAMILY, size: 12, color: CHART_COLORS.text },
      showlegend: false,
      ...restLayout,
      xaxis: {
        gridcolor: CHART_COLORS.grid, zerolinecolor: CHART_COLORS.grid, linecolor: CHART_COLORS.border,
        ...(xaxis as Record<string, unknown> | undefined),
      },
      yaxis: {
        gridcolor: CHART_COLORS.grid, zerolinecolor: CHART_COLORS.grid, linecolor: CHART_COLORS.border,
        ...(yaxis as Record<string, unknown> | undefined),
      },
    };
    // react() both creates (first call) and updates (subsequent calls) --
    // no purge+recreate flicker on every data/layout change.
    void Plotly.react(el, data, mergedLayout, { responsive: true, displaylogo: false, displayModeBar: "hover" });
  }, [data, layout, height]);

  useEffect(() => {
    const el = ref.current;
    if (!el || typeof ResizeObserver === "undefined") return;
    const observer = new ResizeObserver(() => Plotly.Plots.resize(el));
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Registered here rather than per chart component: every chart in the app
  // renders through this one element, so eight chart types become capturable
  // with one effect. Re-runs when the hash changes so a capture is never
  // offered with a fingerprint from the previous dataset.
  useEffect(() => {
    if (!captureKey) return;
    return registerChart(
      captureKey,
      async () => {
        const el = ref.current;
        if (!el) return null;
        return (Plotly as unknown as WithToImage).toImage(el, { format: "png", width: 1000, height: 560, scale: 2 });
      },
      captureHash,
    );
  }, [captureKey, captureHash]);

  // Separate one-time effect: purge only on final unmount, not on every
  // data/layout-driven re-run of the effect above.
  useEffect(() => {
    const el = ref.current;
    return () => {
      if (el) Plotly.purge(el);
    };
  }, []);

  return <div ref={ref} className="sigma-plotly" />;
}
