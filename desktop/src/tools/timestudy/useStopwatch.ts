import { useEffect, useRef, useState } from "react";

/** Pure timer mechanics, no artifact/save concerns -- a continuous
 * lap-stopwatch: `start()` zeroes it, each `split()` returns the seconds
 * since the previous split (or since start, for the first) while the
 * displayed `elapsedMs` keeps counting the whole cycle. Client timestamps
 * are fine for CAPTURE (M2 brief) -- nothing here is a statistic; the
 * engine recomputes every stat from the seconds a split hands off to a
 * Cycle's element_times. */
export function useStopwatch() {
  const [running, setRunning] = useState(false);
  const [, forceTick] = useState(0);
  const startedAtRef = useRef<number | null>(null);
  const lastSplitAtRef = useRef<number | null>(null);

  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => forceTick((t) => t + 1), 100);
    return () => window.clearInterval(id);
  }, [running]);

  function start() {
    const now = Date.now();
    startedAtRef.current = now;
    lastSplitAtRef.current = now;
    setRunning(true);
  }

  /** Seconds since the previous split (start counts as the first). */
  function split(): number {
    const now = Date.now();
    const since = lastSplitAtRef.current ?? now;
    lastSplitAtRef.current = now;
    return (now - since) / 1000;
  }

  function reset() {
    startedAtRef.current = null;
    lastSplitAtRef.current = null;
    setRunning(false);
  }

  const elapsedMs = running && startedAtRef.current != null ? Date.now() - startedAtRef.current : 0;

  return { running, elapsedMs, start, split, reset };
}
