/** Shared cursor rules: finite buffers, exclusive window ends, no seen-data fallback. */
export function packetAt(cursor: number, count: number): number {
  if (!Number.isFinite(cursor) || !Number.isInteger(count) || count < 1)
    return 0;
  return Math.max(0, Math.min(count - 1, Math.floor(cursor)));
}
export function advanceTimeline(
  cursor: number,
  elapsed: number,
  rate: number,
  speed: number,
  count: number,
): { cursor: number; ended: boolean } {
  if (
    ![cursor, elapsed, rate, speed].every(Number.isFinite) ||
    elapsed < 0 ||
    rate <= 0 ||
    speed <= 0 ||
    !Number.isInteger(count) ||
    count < 1
  )
    throw new Error("Use a finite positive replay rate and a loaded buffer.");
  const next = Math.max(0, cursor) + elapsed * rate * speed;
  return { cursor: Math.min(count - 1, next), ended: next >= count - 1 };
}
type Window = { start: number; end: number; prediction: number };
type HeldOut = { capture_id: string; mode: string; windows: Window[] };
export function heldOutAt(
  result: HeldOut | null,
  packet: number,
  captureId: string | null,
): Window | null {
  if (
    !result ||
    result.mode !== "held_out" ||
    !captureId ||
    result.capture_id !== captureId ||
    !Number.isInteger(packet)
  )
    return null;
  return (
    result.windows.find(
      (w) =>
        Number.isInteger(w.start) &&
        Number.isInteger(w.end) &&
        w.start >= 0 &&
        w.end > w.start &&
        packet >= w.start &&
        packet < w.end,
    ) || null
  );
}
export function qualityAt(
  trace: (number | null)[],
  score: (number | null)[],
  packet: number,
): string {
  if (
    packet < 0 ||
    packet >= trace.length ||
    trace[packet] === null ||
    !Number.isFinite(trace[packet])
  )
    return "Window skipped · quality";
  if (score[packet] === null || !Number.isFinite(score[packet]))
    return packet < 15
      ? "Collecting 16 valid packets"
      : "Window skipped · quality";
  return "usable";
}

/** Simulation ground truth is separate from recorded-model decisions. */
export function scenarioForFrame(generated:string|undefined,decision:Window|null,usable:boolean):string{
  if(generated)return generated;
  if(!usable||!decision)return 'unknown';
  return decision.prediction===1?'still':decision.prediction===0?'empty':'unknown';
}
