/** Minimal ambient types for plotly.js-dist-min — just the surface
 * PlotlyChart.tsx calls. There is no @types/plotly.js dependency here
 * (not on this milestone's allowed-new-deps list); trace/layout shapes
 * are loosely typed (Record<string, unknown>) rather than fully modeled
 * — the honest cost of a thin wrapper over a library this large.
 */
declare module "plotly.js-dist-min" {
  export interface PlotlyDatum extends Record<string, unknown> {
    type?: string;
  }

  export type PlotlyLayout = Record<string, unknown>;

  export interface PlotlyConfig extends Record<string, unknown> {
    responsive?: boolean;
    displaylogo?: boolean;
    displayModeBar?: boolean | "hover";
  }

  export interface PlotlyStatic {
    newPlot(root: HTMLElement, data: PlotlyDatum[], layout?: PlotlyLayout, config?: PlotlyConfig): Promise<HTMLElement>;
    react(root: HTMLElement, data: PlotlyDatum[], layout?: PlotlyLayout, config?: PlotlyConfig): Promise<HTMLElement>;
    purge(root: HTMLElement): void;
    Plots: {
      resize(root: HTMLElement): void;
    };
  }

  const Plotly: PlotlyStatic;
  export default Plotly;
}
