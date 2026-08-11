import { useEffect, useState } from "react";
import { ChartFrame } from "../../charts/ChartFrame";
import { fingerprint } from "../../charts/capture";
import { CHART_COLORS } from "../../charts/palette";
import {
  CHART_COMPONENT_LABELS,
  CHART_COMPONENT_ORDER,
  chartSeries,
  studyVariationValues,
  toleranceValues,
} from "./gageRrLogic";
import type { GageRRResult } from "../../api/types";
import { GRR_ACCEPTABLE_MAX_PERCENT, GRR_MARGINAL_MAX_PERCENT } from "../../api/types";
import type { VerdictTone } from "../../design/components";

export interface GageRrComponentsChartProps {
  result: GageRRResult;
  testId?: string;
  captureKey?: string;
}

const TONE: Record<string, VerdictTone> = { acceptable: "pass", marginal: "flag", unacceptable: "fail" };

/** Components of variation — the one panel of a Gage R&R that a reader
 * takes in at a glance, and the reason the report is worth printing.
 *
 * Four bars, and the shape of them is the finding: measurement error tall
 * beside a short part-to-part bar means the gauge is looking at itself.
 * The 10% and 30% convention lines are drawn so the verdict is legible
 * without reading the number, and both bases are plotted side by side when
 * a tolerance exists, because a gauge can clear one and fail the other and
 * showing only the flattering basis is how that gets missed.
 */
export function GageRrComponentsChart({ result, testId, captureKey = "T-35-components" }: GageRrComponentsChartProps) {
  // Async (SubtleCrypto), so it lands a tick after paint. Until then the
  // chart registers with a null hash, which the engine treats as
  // unverifiable and declines rather than trusting -- the safe direction.
  const [hash, setHash] = useState<string | null>(null);
  const series = chartSeries(result);
  const seriesKey = series.join(",");
  useEffect(() => {
    let live = true;
    void fingerprint(series).then((h) => {
      if (live) setHash(h);
    });
    return () => {
      live = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps -- seriesKey is the value identity of `series`
  }, [seriesKey]);

  const labels = CHART_COMPONENT_ORDER.map((name) => CHART_COMPONENT_LABELS[name]);
  const studyVar = studyVariationValues(result);
  const tolerance = toleranceValues(result);
  // Deliberately NOT the verdict. The verdict banner is already on the
  // screen directly above this chart, and repeating it here read as two
  // separate findings. This headline says what the picture shows, which is
  // the split the bars are drawn to make visible.
  const partPercent = result.components.find((c) => c.name === "part_to_part")?.percent_study_variation ?? 0;
  const headline =
    `Where the variation lives — ${result.grr_percent_study_variation.toFixed(1)}% measurement, ` +
    `${partPercent.toFixed(1)}% parts, as a share of study variation`;

  const line = (y: number, color: string) => ({
    type: "line", x0: 0, x1: 1, xref: "paper", y0: y, y1: y, line: { color, dash: "dot", width: 1.5 },
  });

  return (
    <ChartFrame
      captureKey={captureKey}
      captureHash={hash}
      title="Components of variation"
      headline={headline}
      tone={TONE[result.verdict] ?? "neutral"}
      detail={
        `Dotted lines mark the ${GRR_ACCEPTABLE_MAX_PERCENT}% and ${GRR_MARGINAL_MAX_PERCENT}% convention bands. ` +
        "Percentages are computed on standard deviations, not variances, which is why the bars do not add to 100."
      }
      caption={
        tolerance
          ? "Two bars per component: what the gauge does to the process variation you can see, and what it does to the spec you have to hold."
          : "No tolerance given, so this is study variation only — it says whether the gauge can see the process vary, not whether it can police a spec."
      }
      // VALUE LABELS ARE NOT DECORATION HERE. Part-to-part is usually the
      // tallest bar by a wide margin -- and %tolerance for it can run past
      // 100% -- which squashes the Gage R&R bars, the ones the reader came
      // for, into slivers at the axis. Printing each bar's own number keeps
      // "1.5% vs 0.6%" readable at any scale, without capping an axis and
      // truncating a real bar to make the picture look tidier than the data.
      data={[
        {
          type: "bar", name: "% study variation",
          x: labels, y: studyVar,
          text: studyVar.map((v) => `${v.toFixed(1)}%`),
          textposition: "outside", cliponaxis: false,
          marker: { color: CHART_COLORS.accent },
        },
        ...(tolerance
          ? [{
              type: "bar" as const, name: "% tolerance", x: labels, y: tolerance,
              text: tolerance.map((v) => `${v.toFixed(1)}%`),
              textposition: "outside" as const, cliponaxis: false,
              marker: { color: CHART_COLORS.neutral },
            }]
          : []),
      ]}
      layout={{
        barmode: "group",
        yaxis: { title: { text: "Percent" } },
        shapes: [line(GRR_ACCEPTABLE_MAX_PERCENT, CHART_COLORS.pass), line(GRR_MARGINAL_MAX_PERCENT, CHART_COLORS.fail)],
        showlegend: tolerance !== null,
        legend: { orientation: "h", y: -0.2 },
      }}
      testId={testId}
    />
  );
}
