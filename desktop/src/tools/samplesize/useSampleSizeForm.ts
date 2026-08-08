import { useEffect, useState } from "react";
import { runSampleSize } from "../../api/client";
import { ApiError } from "../../api/errors";
import type { SampleSizeResponse } from "../../api/types";

export type CalculatorKind = "mean" | "proportion";

/** T-11's sample-size panel state + engine wiring. The I-MR rule of thumb
 * and bias warnings are cheap and input-independent (aside from the bias
 * checkboxes), so they refresh automatically; the margin-of-error
 * calculator only runs when the user asks (canCalculate gates real
 * inputs, mirroring useBaselineForm's canRun pattern). */
export function useSampleSizeForm() {
  const [calculator, setCalculator] = useState<CalculatorKind>("mean");
  const [planningSdText, setPlanningSdText] = useState("");
  const [planningPPercentText, setPlanningPPercentText] = useState("50");
  const [marginText, setMarginText] = useState("");
  const [confidenceLevel, setConfidenceLevel] = useState(0.95);
  const [isConvenienceSample, setIsConvenienceSample] = useState(false);
  const [singleShiftOnly, setSingleShiftOnly] = useState(false);
  const [singleOperatorOnly, setSingleOperatorOnly] = useState(false);
  const [shortCollectionWindow, setShortCollectionWindow] = useState(false);
  const [result, setResult] = useState<SampleSizeResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    runSampleSize({
      is_convenience_sample: isConvenienceSample,
      single_shift_only: singleShiftOnly,
      single_operator_only: singleOperatorOnly,
      short_collection_window: shortCollectionWindow,
    })
      .then((res) => setResult((prev) => ({ ...res, calculator: prev?.calculator ?? null })))
      .catch(() => {
        /* the rule-of-thumb panel just stays empty; not fatal */
      });
  }, [isConvenienceSample, singleShiftOnly, singleOperatorOnly, shortCollectionWindow]);

  const marginOfError = Number(marginText);
  const planningSd = Number(planningSdText);
  const planningP = Number(planningPPercentText) / 100;
  const marginAsFraction = calculator === "proportion" ? marginOfError / 100 : marginOfError;

  const canCalculate =
    Number.isFinite(marginOfError) &&
    marginOfError > 0 &&
    (calculator === "mean"
      ? Number.isFinite(planningSd) && planningSd > 0
      : Number.isFinite(planningP) && planningP > 0 && planningP < 1);

  async function handleCalculate() {
    if (!canCalculate) return;
    setLoading(true);
    setError(null);
    try {
      const res = await runSampleSize({
        calculator,
        planning_sd: calculator === "mean" ? planningSd : undefined,
        planning_p: calculator === "proportion" ? planningP : undefined,
        margin_of_error: marginAsFraction,
        confidence_level: confidenceLevel,
        is_convenience_sample: isConvenienceSample,
        single_shift_only: singleShiftOnly,
        single_operator_only: singleOperatorOnly,
        short_collection_window: shortCollectionWindow,
      });
      setResult(res);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not run the calculator.");
    } finally {
      setLoading(false);
    }
  }

  return {
    calculator, setCalculator, planningSdText, setPlanningSdText, planningPPercentText, setPlanningPPercentText,
    marginText, setMarginText, confidenceLevel, setConfidenceLevel,
    isConvenienceSample, setIsConvenienceSample, singleShiftOnly, setSingleShiftOnly,
    singleOperatorOnly, setSingleOperatorOnly, shortCollectionWindow, setShortCollectionWindow,
    result, loading, error, canCalculate, handleCalculate,
  };
}
