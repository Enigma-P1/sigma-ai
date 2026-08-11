import { useEffect } from "react";
import type Konva from "konva";
import { registerChart } from "./capture";

/** Register a Konva canvas with the capture registry, so its diagram can
 * reach a PDF.
 *
 * WHY THE HASH IS NULL HERE, deliberately. Plotly charts submit a
 * fingerprint of the series they were drawn from, and the engine refuses an
 * image whose fingerprint disagrees with the data it is rendering. A
 * fishbone, a process map and a spaghetti diagram have no such series:
 * they are drawings of a structure, and the engine's `_chart_series`
 * returns None for them for exactly that reason. `check_chart` then takes
 * the image on trust, because — in that module's own words — inventing a
 * comparison would be theatre.
 *
 * What protects these instead is that the canvas is captured live, from
 * the mounted stage, at the moment the button is pressed. There is no
 * stored image that could go stale.
 *
 * PIXEL RATIO 2 because these land on a printed page: a 1x capture of a
 * canvas sized for a screen looks soft at print resolution, and this is
 * the one report whose whole content is the picture.
 */
export function useStageCapture(captureKey: string, stageRef: React.RefObject<Konva.Stage | null>) {
  useEffect(() => {
    return registerChart(
      captureKey,
      async () => {
        const stage = stageRef.current;
        if (!stage) return null;
        try {
          return stage.toDataURL({ pixelRatio: 2, mimeType: "image/png" });
        } catch {
          // A tainted canvas (a floor plan loaded cross-origin) throws
          // here. Losing the picture is the right cost; losing the report
          // would not be.
          return null;
        }
      },
      null,
    );
  }, [captureKey, stageRef]);
}
