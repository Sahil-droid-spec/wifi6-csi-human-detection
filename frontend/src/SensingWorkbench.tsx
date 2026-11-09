import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import * as echarts from "echarts";
import "./sensing-workbench.css";
import {
  advanceTimeline,
  packetAt,
  heldOutAt,
  qualityAt,
} from "./sensingTimeline";
const SpatialScene = lazy(() => import("./SpatialScene"));
type D = Record<string, any>;
const defaults = {
  scenario: "walking",
  packet_rate: 100,
  subcarriers: 52,
  duration: 12,
  noise: 0.012,
  motion_intensity: 0.7,
  virtual_speed: 1,
  multipath: 5,
  gain: 1,
  packet_loss: 0.01,
  jitter: 0.01,
  drift: 0.015,
  threshold_multiplier: 3,
  seed: 42,
};
const fields: [string, string, number, number, number, string][] = [
  [
    "packet_rate",
    "Packet rate · Hz",
    20,
    500,
    1,
    "Synthetic packets per second. This is not measured Wi-Fi throughput.",
  ],
  [
    "subcarriers",
    "Subcarriers",
    16,
    256,
    1,
    "Complex channel samples per packet; this simulator is not a full Wi-Fi PHY.",
  ],
  [
    "duration",
    "Duration · seconds",
    4,
    30,
    1,
    "Session duration. Total complex samples are capped at one million.",
  ],
  [
    "noise",
    "Noise amplitude",
    0,
    0.3,
    0.001,
    "Independent complex Gaussian noise added to the generated channel.",
  ],
  [
    "motion_intensity",
    "Motion intensity",
    0,
    2,
    0.05,
    "Scales the person-reflection term, not a detection confidence.",
  ],
  [
    "virtual_speed",
    "Virtual speed · m/s",
    0,
    3,
    0.1,
    "Controls procedural path timing; not a speed recovered from Wi-Fi.",
  ],
  [
    "multipath",
    "Static multipath components",
    1,
    12,
    1,
    "Number of independently seeded static channel paths.",
  ],
  [
    "gain",
    "Channel gain",
    0.1,
    3,
    0.1,
    "Linear amplitude multiplier before added noise.",
  ],
  [
    "packet_loss",
    "Packet loss fraction",
    0,
    0.3,
    0.005,
    "Missing packets stay gaps, never zero-filled into filters.",
  ],
  [
    "jitter",
    "Sampling jitter fraction",
    0,
    0.3,
    0.005,
    "Changes inter-packet timing. FFT uses nominal rate; timing irregularity limits interpretation.",
  ],
  [
    "drift",
    "Baseline drift",
    0,
    0.2,
    0.005,
    "Slow common channel-amplitude change, separate from motion.",
  ],
  [
    "threshold_multiplier",
    "Threshold multiplier",
    1,
    8,
    0.1,
    "Threshold = mean + multiplier × SD of a separate empty-room simulation.",
  ],
  [
    "seed",
    "Random seed",
    0,
    4294967295,
    1,
    "Same seed and settings reproduce exactly the same synthetic channel.",
  ],
];
const initialFilter = {
  operation: "butterworth",
  kind: "lowpass",
  cutoff: 0.08,
  upper: 0.2,
  order: 4,
  taps: 31,
  window: "hann",
  stft_size: 64,
  overlap: 0.5,
  subcarrier: 0,
};
function Plot({
  option,
  label,
  cursor,
}: {
  option: D;
  label: string;
  cursor?: number;
}) {
  const ref = useRef<HTMLDivElement>(null),
    chart = useRef<echarts.ECharts | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const c = echarts.init(ref.current);
    chart.current = c;
    const r = new ResizeObserver(() => c.resize());
    r.observe(ref.current);
    return () => {
      r.disconnect();
      c.dispose();
    };
  }, []);
  useEffect(() => {
    chart.current?.setOption(option, true);
  }, [option]);
  useEffect(() => {
    if (cursor !== undefined)
      chart.current?.setOption({
        series: option.series.map(() => ({
          markLine: {
            silent: true,
            symbol: "none",
            label: { show: false },
            lineStyle: { color: "#CC79A7", type: "dashed" },
            data: [{ xAxis: cursor }],
          },
        })),
      });
  }, [cursor]);
  return (
    <div className="sensing-chart" ref={ref} role="img" aria-label={label} />
  );
}
const lessons = [
  [
    "CSI & OFDM",
    "H(k,t) = Σ aₗ(t) exp(−j2π fₖ τₗ(t)) + w(k,t)",
    "CSI is the complex channel response on each subcarrier. Reflections add with different phases; motion can change those reflections. This simulator approximates that idea, not an 802.11ax radio.",
    "Can a normal phone upload measure CSI?",
    "No. An uploaded file is application data. CSI needs suitable radio hardware, firmware and capture validation.",
  ],
  [
    "Multipath & motion",
    "Δφ = −2π Δd / λ",
    "A path-length change changes phase. Static reflections can cancel the moving reflection; still-person detection is harder than detecting motion.",
    "Does a motion score establish human presence?",
    "No. Nonhuman motion and gain changes can trigger it. A validated classifier and held-out measurements are separate.",
  ],
  [
    "Sampling & aliasing",
    "fₛ > 2 fmax",
    "The Nyquist condition assumes a band-limited signal sampled regularly. Here rate is nominal when jitter is enabled. Recorded files without timestamps use cycles per packet.",
    "Why not label every spectrum in Hz?",
    "Hz needs a known sample rate. Without timing, cycles per packet is the honest frequency unit.",
  ],
  [
    "FIR filtering",
    "y[n] = Σ h[k] x[n−k]",
    "A finite impulse response filter uses current and past input samples. Hamming/Hann/Blackman/Kaiser windows trade transition width and sidelobes.",
    "Does smoother CSI prove higher accuracy?",
    "No. Filtering can remove useful motion. Compare the same data using leakage-safe validation.",
  ],
  [
    "IIR filtering",
    "y[n] = Σ b[k]x[n−k] − Σ a[k]y[n−k], a[0]=1",
    "Feedback makes an efficient infinite impulse response. Butterworth has a maximally flat passband. Causal filtering has startup transients and phase delay.",
    "Why reset a filter at packet gaps?",
    "Otherwise it falsely treats samples on opposite sides of a gap as adjacent in time.",
  ],
  [
    "Fourier transform",
    "X[k] = Σ x[n] exp(−j2πkn/N)",
    "FFT efficiently computes the DFT. Windowing reduces leakage, with a resolution tradeoff. Spectra here exclude missing samples by using one contiguous usable run.",
    "What determines frequency resolution?",
    "Approximately sample rate divided by the number of contiguous samples, with window-dependent effective resolution.",
  ],
  [
    "STFT spectrogram",
    "X(m,ω) = Σ x[n]w[n−mR] exp(−jωn)",
    "Short overlapping windows show how frequency content evolves. Longer windows improve frequency resolution and reduce time resolution.",
    "What does the colour measure?",
    "Magnitude in dB relative to one signal unit, not RF power in dBm and not confidence.",
  ],
  [
    "Motion proxy & calibration",
    "score = 100 σ₁₆ / mean(|x₁₆|); threshold = μempty + k σempty",
    "This heuristic uses 16 consecutive valid median-amplitude samples. It is not RF/ANN inference. Empty calibration uses a separate generated empty scenario, not held-out classifier labels.",
    "What does no motion mean?",
    "Only that this proxy did not exceed its threshold; it does not prove an empty room.",
  ],
];
export function SensingWorkbench({
  capture,
  reduced = false,
  models = [],
}: {
  capture?: D;
  reduced?: boolean;
  models?: D[];
}) {
  const [tab, setTab] = useState("scene"),
    [config, setConfig] = useState<D>(defaults),
    [filter, setFilter] = useState<D>(initialFilter),
    [session, setSession] = useState<D | null>(null),
    [analysis, setAnalysis] = useState<D | null>(null),
    [source, setSource] = useState("simulation"),
    [cursor, setCursor] = useState(0),
    [playing, setPlaying] = useState(false),
    [speed, setSpeed] = useState(1),
    [busy, setBusy] = useState(false),
    [error, setError] = useState(""),
    [notice, setNotice] = useState(""),
    [query, setQuery] = useState(""),
    [comparisons, setComparisons] = useState<D[]>([]),
    [health, setHealth] = useState<D | null>(null),
    [theme, setTheme] = useState(0),
    [model, setModel] = useState(""),
    [prediction, setPrediction] = useState<D | null>(null),
    [recordings, setRecordings] = useState<D[]>([]),
    [clipStart, setClipStart] = useState(0),
    [clipEnd, setClipEnd] = useState(0),
    [recordingSegment, setRecordingSegment] = useState(false),
    [filterComparisons, setFilterComparisons] = useState<D[]>([]),
    [autoTour, setAutoTour] = useState(false);
  useEffect(() => {
    setPrediction(null);
    setModel("");
    setClipStart(0);
    setClipEnd(Math.min(session?.packets || 0, 10000));
    setRecordingSegment(false);
  }, [session?.id]);
  const availableModels = models.filter(
    (m) => capture && m.held_out_windows?.[capture.sha256],
  );
  const predictionWindow = heldOutAt(
    prediction as any,
    packetAt(cursor, session?.packets || 0),
    session?.capture_id || null,
  );
  async function refreshRecordings() {
    try {
      const r = await fetch("/api/sensing/recordings"),
        d = await r.json();
      if (!r.ok)
        throw Error("Refresh the Library after reconnecting to Orbit.");
      setRecordings(d.recordings);
    } catch (e) {
      setError((e as Error).message);
    }
  }
  useEffect(() => {
    if (tab === "recordings") void refreshRecordings();
  }, [tab]);
  useEffect(() => {
    if (!autoTour) return;
    const views = ["scene", "csi", "dsp", "spectrum", "motion"];
    const timer = setInterval(
      () => setTab((t) => views[(views.indexOf(t) + 1) % views.length]),
      8000,
    );
    return () => clearInterval(timer);
  }, [autoTour]);
  useEffect(() => {
    if (!recordingSegment || !session) return;
    const end = Math.min(Math.floor(cursor) + 1, clipStart + 10000);
    setClipEnd(end);
    if (end >= session.packets || end >= clipStart + 10000) {
      setRecordingSegment(false);
      setPlaying(false);
    }
  }, [cursor, recordingSegment, clipStart, session?.id]);
  const analysisWindow = session
    ? Math.min(
        Math.floor(cursor / 128) * 128,
        Math.max(0, session.packets - 256),
      )
    : 0;
  useEffect(() => {
    const fn = () => setTheme((t) => t + 1);
    window.addEventListener("orbit-theme", fn);
    return () => window.removeEventListener("orbit-theme", fn);
  }, []);
  useEffect(() => {
    if (!playing || !session) return;
    let last = performance.now();
    const timer = setInterval(() => {
      const now = performance.now(),
        dt = (now - last) / 1000;
      last = now;
      setCursor((c) => {
        const next = advanceTimeline(
          c,
          dt,
          session.rate || 100,
          speed,
          session.packets,
        );
        if (next.ended) setPlaying(false);
        return next.cursor;
      });
    }, 80);
    return () => clearInterval(timer);
  }, [playing, session?.id, speed]);
  useEffect(() => {
    if (!session) return;
    const controller = new AbortController();
    let live = true;
    const timer = setTimeout(async () => {
      try {
        const r = await fetch(
          "/api/sensing/sessions/" + session.id + "/analyze",
          {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              ...filter,
              start: analysisWindow,
              length: 256,
            }),
            signal: controller.signal,
          },
        );
        const d = await r.json();
        if (!r.ok)
          throw Error(
            typeof d.detail === "string"
              ? d.detail
              : "Check the filter settings, then apply again.",
          );
        if (live) setAnalysis({ ...d, settings: { ...filter } });
      } catch (e) {
        if (live && (e as Error).name !== "AbortError") {
          setAnalysis(null);
          setError((e as Error).message);
        }
      }
    }, 100);
    return () => {
      live = false;
      controller.abort();
      clearTimeout(timer);
    };
  }, [session?.id, analysisWindow, filter]);
  useEffect(() => {
    setError("");
  }, [source, capture?.id, config, filter]);
  async function load() {
    setBusy(true);
    setError("");
    setNotice("");
    setPlaying(false);
    try {
      const r = await fetch("/api/sensing/sessions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          source,
          capture_id: source === "recorded" ? capture?.id : null,
          simulation: config,
        }),
      });
      const d = await r.json();
      if (!r.ok)
        throw Error(
          typeof d.detail === "string"
            ? d.detail
            : "Reduce duration, packet rate or subcarriers; then apply again.",
        );
      setSession(d);
      setAnalysis(null);
      setCursor(0);
      setNotice(
        "Session ready. Press Play; the scene, cursor and motion card use this same timeline.",
      );
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  const p = packetAt(cursor, session?.packets || 0),
    score = session?.score[p],
    valid = session?.trace[p] !== null,
    time = session?.time[p] || 0;
  const scenario = session?.config?.scenario || "still",
    simulated = session?.config?.scenario !== undefined;
  const colors = useMemo(() => {
    const s = getComputedStyle(document.documentElement);
    return {
      text: s.getPropertyValue("--text"),
      muted: s.getPropertyValue("--muted"),
      line: s.getPropertyValue("--line"),
    };
  }, [theme]);
  const base: D = {
    animation: false,
    backgroundColor: "transparent",
    textStyle: { color: colors.text },
    tooltip: { trigger: "axis" },
    legend: { bottom: 0, textStyle: { color: colors.text } },
    grid: { left: 60, right: 20, top: 35, bottom: 55 },
    xAxis: {
      type: "value",
      name: "packet",
      axisLabel: { color: colors.muted },
      splitLine: { lineStyle: { color: colors.line } },
    },
    yAxis: {
      type: "value",
      scale: true,
      axisLabel: { color: colors.muted },
      splitLine: { lineStyle: { color: colors.line } },
    },
  };
  const marker = {
    silent: true,
    symbol: "none",
    label: { show: false },
    lineStyle: { color: "#CC79A7", type: "dashed" },
    data: [{ xAxis: p }],
  };
  const line = (
    name: string,
    data: any[],
    color: string,
    dashed = false,
  ): D => ({
    name,
    type: "line",
    showSymbol: false,
    connectNulls: false,
    lineStyle: { color, type: dashed ? "dashed" : "solid" },
    data,
    markLine: marker,
  });
  const trace = useMemo(
    () => ({
      ...base,
      series: [
        line(
          "Original median amplitude",
          session?.trace.map((v: number, i: number) => [i, v]) || [],
          "#0072B2",
        ),
        line(
          "Filtered selected window",
          analysis?.filtered.map((v: number, i: number) => [
            analysis.start + i,
            v,
          ]) || [],
          "#E69F00",
          true,
        ),
      ],
    }),
    [session, analysis, theme],
  );
  const motion = useMemo(
    () => ({
      ...base,
      yAxis: { ...base.yAxis, name: "relative motion proxy" },
      series: [
        line(
          "Motion proxy",
          session?.score.map((v: number, i: number) => [i, v]) || [],
          "#009E73",
        ),
        line(
          "Empty-simulation threshold",
          session?.threshold == null
            ? []
            : [
                [0, session.threshold],
                [session.packets - 1, session.threshold],
              ],
          "#D55E00",
          true,
        ),
      ],
    }),
    [session, theme],
  );
  const spectrum = useMemo(
    () => ({
      ...base,
      xAxis: { ...base.xAxis, name: analysis?.frequency_unit },
      series: [
        line(
          "Original",
          analysis?.spectrum.map((v: number[]) => [v[0], v[1]]) || [],
          "#0072B2",
        ),
        line(
          "Filtered",
          analysis?.spectrum.map((v: number[]) => [v[0], v[2]]) || [],
          "#E69F00",
          true,
        ),
      ].map((s) => ({ ...s, markLine: undefined })),
    }),
    [analysis, theme],
  );
  const heatmap = (data: number[][], xName: string, yName: string) => ({
    ...base,
    tooltip: { trigger: "item" },
    xAxis: {
      ...base.xAxis,
      name: xName,
      type: "category",
      data: [...new Set(data.map((d) => d[0]))].sort((a, b) => a - b),
    },
    yAxis: {
      ...base.yAxis,
      name: yName,
      type: "category",
      data: [...new Set(data.map((d) => d[1]))].sort((a, b) => a - b),
    },
    visualMap: {
      min: data.length ? Math.min(...data.map((d) => d[2])) : 0,
      max: data.length ? Math.max(...data.map((d) => d[2])) : 1,
      show: false,
      inRange: { color: ["#182d55", "#0072B2", "#56B4E9", "#E69F00"] },
    },
    series: [
      {
        type: "heatmap",
        progressive: 0,
        data: data.map((d) => [String(d[0]), String(d[1]), d[2]]),
      },
    ],
  });
  const stftData =
    analysis?.stft?.db.flatMap((row: number[], i: number) =>
      row.map((v: number, j: number) => [
        analysis.stft.time[j],
        analysis.stft.frequency[i],
        v,
      ]),
    ) || [];
  return (
    <div className="sensing-workbench">
      <header className="sensing-heading">
        <div>
          <span className="control-eyebrow">ORBIT / SPATIAL SIGNAL LAB</span>
          <h2>One channel. Every perspective.</h2>
          <p>
            Explore a reproducible simulation or inspect a saved recording, with
            one shared packet timeline.
          </p>
        </div>
        <span className="control-tag">
          {session?.source || "No session loaded"}
        </span>
      </header>
      <label className="sensing-import">
        Reopen an exported session · JSON or NPZ
        <input
          type="file"
          disabled={recordingSegment}
          accept=".json,.npz"
          onChange={async (e) => {
            const file = e.target.files?.[0];
            if (!file) return;
            setBusy(true);
            setError("");
            setPlaying(false);
            try {
              const form = new FormData();
              form.append("file", file);
              const r = await fetch("/api/sensing/import", {
                  method: "POST",
                  body: form,
                }),
                d = await r.json();
              if (!r.ok)
                throw Error(
                  typeof d.detail === "string"
                    ? d.detail
                    : "Choose an intact Orbit session export.",
                );
              setSession(d);
              setAnalysis(null);
              setCursor(0);
              setNotice(
                "Imported " +
                  file.name +
                  ". Source metadata retained; no pose is inferred.",
              );
            } catch (err) {
              setError((err as Error).message);
            } finally {
              setBusy(false);
              e.target.value = "";
            }
          }}
        />
      </label>
      <div className="sensing-source">
        <label title="Simulations are generated here; recorded data load from the saved CSI selection above.">
          Source
          <select
            disabled={recordingSegment}
            value={source}
            onChange={(e) => {
              setSource(e.target.value);
              setPlaying(false);
            }}
          >
            <option value="simulation">Simulation library</option>
            <option value="recorded">Selected saved CSI recording</option>
          </select>
        </label>
        <label>
          Scenario
          <select
            disabled={recordingSegment || source !== "simulation"}
            value={config.scenario}
            onChange={(e) =>
              setConfig((c) => ({ ...c, scenario: e.target.value }))
            }
          >
            {[
              ["empty", "Empty room"],
              ["still", "One person still"],
              ["walking", "One person walking"],
              ["moving", "One person moving"],
              ["two", "Two people"],
              ["crossing", "Crossing paths"],
            ].map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <button
          disabled={
            recordingSegment || busy || (source === "recorded" && !capture)
          }
          onClick={load}
        >
          {busy
            ? "Preparing…"
            : source === "simulation"
              ? "Apply & restart simulation"
              : "Load selected recording"}
        </button>
      </div>
      {source === "recorded" && (
        <p className="control-footnote">
          {capture
            ? "Selected: " + capture.name
            : "Choose a saved input above first."}{" "}
          Amplitude-only files have no phase, recovered pose or measured packet
          rate.
        </p>
      )}
      {error && (
        <p role="alert" className="control-error">
          {error} <button onClick={load}>Reload session</button>
        </p>
      )}
      {notice && (
        <p role="status" className="sensing-notice">
          {notice}
        </p>
      )}
      <label className="sensing-auto">
        <input
          type="checkbox"
          checked={autoTour}
          onChange={(e) => setAutoTour(e.target.checked)}
        />
        Auto tour · cycle analysis views every 8 seconds
      </label>
      <nav className="control-tabs" aria-label="3D studio analysis views">
        {[
          ["scene", "3D environment"],
          ["csi", "CSI explorer"],
          ["dsp", "DSP laboratory"],
          ["spectrum", "FFT & STFT"],
          ["motion", "Motion analytics"],
          ["experiments", "Experiments"],
          ["recordings", "Record & export"],
          ["diagnostics", "Diagnostics"],
          ["theory", "Theory & viva"],
        ].map(([k, v]) => (
          <button
            key={k}
            className={tab === k ? "active" : ""}
            aria-pressed={tab === k}
            onClick={() => setTab(k)}
          >
            {v}
          </button>
        ))}
      </nav>
      {session && (
        <section className="sensing-transport">
          <button
            title="Play the loaded timeline; no new sensor measurement is acquired."
            onClick={() => setPlaying(!playing)}
          >
            {playing ? "Pause" : "Play"}
          </button>
          <button
            onClick={() => {
              setPlaying(false);
              setCursor(0);
            }}
          >
            Restart
          </button>
          <button
            onClick={() => {
              setPlaying(false);
              setCursor((c) =>
                Math.min(session.packets - 1, Math.floor(c) + 1),
              );
            }}
          >
            Step packet
          </button>
          <label>
            Playback
            <select value={speed} onChange={(e) => setSpeed(+e.target.value)}>
              {[0.25, 0.5, 1, 2, 4].map((v) => (
                <option key={v} value={v}>
                  {v}×
                </option>
              ))}
            </select>
          </label>
          <span>
            Packet {p} / {session.packets - 1} ·{" "}
            {session.rate ? time.toFixed(2) + " s" : "timing unavailable"}
          </span>
          <input
            aria-label="Shared packet timeline"
            type="range"
            min={0}
            max={session.packets - 1}
            step={1}
            value={p}
            onChange={(e) => {
              setPlaying(false);
              setCursor(+e.target.value);
            }}
          />
        </section>
      )}
      {!session && !["experiments", "theory", "diagnostics"].includes(tab) ? (
        <div className="control-empty">
          <h3>Start with a real input or a named simulation.</h3>
          <p>
            Press Apply & restart simulation above. To inspect your CSI, select
            it above and switch Source.
          </p>
        </div>
      ) : null}
      {tab === "scene" && session && (
        <>
          <div className="sensing-scene-layout">
            <Suspense fallback={<p>Loading the WebGL environment…</p>}>
              <SpatialScene
                frame={{
                  time,
                  packet: p,
                  scenario,
                  positions: simulated
                    ? session.positions.map((person: number[][]) => person[p])
                    : [[0, 0, 0]],
                  playing,
                  reduced,
                  source: session.source,
                  activity:
                    score == null
                      ? 0
                      : Math.min(5, score / (session.threshold || 1)),
                  trails: simulated
                    ? session.positions.map((person: number[][]) =>
                        person
                          .slice(Math.max(0, p - 300), p + 1)
                          .filter((_: number[], i: number) => i % 5 === 0),
                      )
                    : [],
                }}
              />
            </Suspense>
            <aside className="control-card sensing-verdict">
              <span className="control-eyebrow">CURRENT PACKET</span>
              <h3>
                {qualityAt(session.trace, session.score, p) !== "usable"
                  ? qualityAt(session.trace, session.score, p)
                  : session.threshold == null
                    ? "Uncalibrated recorded input"
                    : score > session.threshold
                      ? "Motion proxy above threshold"
                      : "Below motion threshold"}
              </h3>
              <dl>
                <dt>Motion proxy</dt>
                <dd>{score == null ? "Unavailable" : score.toFixed(3)}</dd>
                <dt>Threshold</dt>
                <dd>
                  {session.threshold == null
                    ? "Not calibrated"
                    : session.threshold.toFixed(3)}
                </dd>
                <dt>Packets usable</dt>
                <dd>
                  {session.packet_audit.received} / {session.packet_audit.total}
                </dd>
                <dt>Missing / invalid</dt>
                <dd>{session.packet_audit.missing_or_invalid}</dd>
                <dt>Trained prediction</dt>
                <dd>
                  {!prediction
                    ? "No model selected"
                    : !valid
                      ? "Window skipped · quality"
                      : predictionWindow
                        ? predictionWindow.prediction
                          ? "Person"
                          : "No person"
                        : "No held-out window at this packet"}
                </dd>
              </dl>
              <p>{session.protocol}</p>
              <p>
                The avatar uses generated positions in Simulation. For recorded
                data it stays in an illustrative location; CSI does not provide
                verified pose or through-wall localization.
              </p>
              {source === "recorded" && (
                <>
                  <label>
                    Held-out model
                    <select
                      value={model}
                      onChange={(e) => {
                        setModel(e.target.value);
                        setPrediction(null);
                      }}
                    >
                      <option value="">Choose an evaluated model</option>
                      {availableModels.map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name} · {m.split}
                        </option>
                      ))}
                    </select>
                  </label>
                  <button
                    disabled={
                      !model || !capture || session.capture_id !== capture.id
                    }
                    onClick={async () => {
                      try {
                        setError("");
                        const r = await fetch("/api/predict", {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                              capture_id: capture?.id,
                              model_id: model,
                              mode: "held_out",
                            }),
                          }),
                          d = await r.json();
                        if (!r.ok)
                          throw Error(
                            d.detail || "Choose a compatible held-out model.",
                          );
                        setPrediction(d);
                      } catch (e) {
                        setError((e as Error).message);
                      }
                    }}
                  >
                    Load held-out predictions
                  </button>
                  {prediction && (
                    <p>
                      Validation protocol: {prediction.validation_protocol}.
                      Each decision is displayed only inside its actual saved
                      window. This model does not control the avatar.
                    </p>
                  )}
                  {!availableModels.length && (
                    <p>
                      No saved model has held-out predictions for this
                      recording. Use Learning Lab; no training-seen result is
                      substituted.
                    </p>
                  )}
                </>
              )}
              <a href="#/replay">Open held-out model Replay →</a>
            </aside>
          </div>
          <Plot
            cursor={p}
            option={trace}
            label="Shared-timeline raw and filtered amplitude"
          />
        </>
      )}
      {tab === "csi" && session && (
        <>
          <h3>Subcarrier amplitude</h3>
          <Plot
            option={heatmap(analysis?.heatmap || [], "packet", "subcarrier")}
            label="Selected-window subcarrier amplitude heatmap"
          />
          <label>
            Phase subcarrier
            <input
              type="number"
              min={0}
              max={session.subcarriers - 1}
              value={filter.subcarrier}
              onChange={(e) =>
                setFilter((f) => ({ ...f, subcarrier: +e.target.value }))
              }
            />
          </label>
          <p>{analysis?.phase_note}</p>
          {analysis?.phase && (
            <Plot
              option={{
                ...base,
                yAxis: { ...base.yAxis, name: "wrapped phase · rad" },
                series: [
                  line(
                    "Phase",
                    analysis.phase.map((v: number, i: number) => [
                      analysis.start + i,
                      v,
                    ]),
                    "#CC79A7",
                  ),
                ],
              }}
              label="Wrapped complex CSI phase"
            />
          )}
          <Plot
            cursor={p}
            option={trace}
            label="Raw and filtered packet trace"
          />
        </>
      )}
      {tab === "dsp" && (
        <>
          <div className="sensing-settings">
            <label>
              Filter
              <select
                disabled={recordingSegment}
                value={filter.operation}
                onChange={(e) =>
                  setFilter((f) => ({ ...f, operation: e.target.value }))
                }
              >
                {["raw", "fir", "butterworth", "notch"].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
            <label>
              Response
              <select
                disabled={
                  recordingSegment ||
                  !["fir", "butterworth"].includes(filter.operation)
                }
                value={filter.kind}
                onChange={(e) =>
                  setFilter((f) => ({ ...f, kind: e.target.value }))
                }
              >
                {["lowpass", "highpass", "bandpass", "bandstop"].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
            {(
              [
                [
                  "cutoff",
                  "Lower / single cutoff · cycles/packet",
                  0.001,
                  0.49,
                  0.005,
                ],
                ["upper", "Upper cutoff · cycles/packet", 0.002, 0.499, 0.005],
                ["order", "Butterworth order", 1, 8, 1],
                ["taps", "FIR taps · odd", 3, 127, 2],
                ["overlap", "STFT overlap", 0, 0.9, 0.05],
              ] as const
            ).map(([k, label, min, max, step]) => (
              <label key={k}>
                {label}
                <input
                  type="number"
                  disabled={recordingSegment}
                  min={min}
                  max={max}
                  step={step}
                  value={filter[k]}
                  onChange={(e) =>
                    setFilter((f) => ({ ...f, [k]: +e.target.value }))
                  }
                />
              </label>
            ))}
            <label>
              Window
              <select
                disabled={recordingSegment}
                value={filter.window}
                onChange={(e) =>
                  setFilter((f) => ({ ...f, window: e.target.value }))
                }
              >
                {["hann", "hamming", "blackman", "kaiser"].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
            <label>
              STFT samples
              <select
                disabled={recordingSegment}
                value={filter.stft_size}
                onChange={(e) =>
                  setFilter((f) => ({ ...f, stft_size: +e.target.value }))
                }
              >
                {[32, 64, 128, 256].map((v) => (
                  <option key={v}>{v}</option>
                ))}
              </select>
            </label>
          </div>
          <Plot
            cursor={p}
            option={trace}
            label="Same-input DSP waveform comparison"
          />
          <Plot
            option={{
              ...base,
              xAxis: { ...base.xAxis, name: analysis?.frequency_unit },
              yAxis: { ...base.yAxis, name: "response · dB" },
              series: [
                {
                  ...line(
                    "Filter response",
                    analysis?.response || [],
                    "#009E73",
                  ),
                  markLine: undefined,
                },
              ],
            }}
            label="Computed filter frequency response"
          />
          <div className="sensing-actions">
            <button
              disabled={!analysis}
              onClick={() => {
                setPlaying(false);
                if (analysis)
                  setFilterComparisons((c) => [
                    ...c.slice(-7),
                    {
                      session_id: session?.id,
                      source: session?.source,
                      start: analysis.start,
                      end: analysis.end,
                      settings: analysis.settings,
                      filtered: analysis.filtered,
                    },
                  ]);
              }}
            >
              Capture FIR / IIR comparison
            </button>
            <button onClick={() => setFilterComparisons([])}>
              Clear filter comparisons
            </button>
            <button
              disabled={!session || !analysis}
              onClick={async () => {
                try {
                  const r = await fetch(
                      "/api/sensing/sessions/" + session?.id + "/save-analysis",
                      {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({
                          ...filter,
                          start: analysisWindow,
                          length: 256,
                        }),
                      },
                    ),
                    d = await r.json();
                  if (!r.ok)
                    throw Error(
                      d.detail || "Check the settings and retry saving.",
                    );
                  setNotice(
                    "Saved analysis with original settings and computed outputs: " +
                      d.asset.name,
                  );
                } catch (e) {
                  setError((e as Error).message);
                }
              }}
            >
              Save this analysis to Library
            </button>
          </div>
          {filterComparisons.length > 0 && (
            <>
              <p>
                Overlay includes only the same session and exact analyzed packet
                range. Captures from other ranges remain listed below but are
                not overlaid.
              </p>
              <Plot
                option={{
                  ...base,
                  series: filterComparisons
                    .filter(
                      (c) =>
                        c.session_id === session?.id &&
                        c.start === analysis?.start &&
                        c.end === analysis?.end,
                    )
                    .map((c, i) =>
                      line(
                        c.settings.operation +
                          " " +
                          c.settings.kind +
                          " " +
                          c.settings.window +
                          " #" +
                          (i + 1),
                        c.filtered.map((v: number, j: number) => [
                          c.start + j,
                          v,
                        ]),
                        ["#0072B2", "#D55E00", "#009E73", "#CC79A7"][i % 4],
                        i % 2 === 1,
                      ),
                    ),
                }}
                label="Matched-window captured filter comparison"
              />
              {filterComparisons.map((c, i) => (
                <p key={i}>
                  Comparison {i + 1}: {c.source} · packets {c.start}–{c.end - 1}{" "}
                  · {c.settings.operation}/{c.settings.kind}/{c.settings.window}
                </p>
              ))}
            </>
          )}
          <details>
            <summary>Phase, group delay & pole–zero plane</summary>
            <p>
              Group delay is measured in packets/samples, not transfer latency.
              Delay at response zeros is withheld. Phase is unwrapped filter
              response, distinct from CSI phase. The unreduced z-plane includes
              delay poles at zero; coincident poles and zeros may cancel.
            </p>
            <Plot
              option={{
                ...base,
                xAxis: { ...base.xAxis, name: analysis?.frequency_unit },
                yAxis: { ...base.yAxis, name: "group delay · samples" },
                series: [
                  {
                    ...line(
                      "Group delay",
                      analysis?.group_delay_samples.map(
                        (v: number, i: number) => [analysis.response[i][0], v],
                      ) || [],
                      "#009E73",
                    ),
                    markLine: undefined,
                  },
                ],
              }}
              label="Calculated filter group delay"
            />
            <Plot
              option={{
                ...base,
                xAxis: { ...base.xAxis, name: "real", min: -1.5, max: 1.5 },
                yAxis: {
                  ...base.yAxis,
                  name: "imaginary",
                  min: -1.5,
                  max: 1.5,
                },
                series: [
                  {
                    name: "Unit circle",
                    type: "line",
                    showSymbol: false,
                    lineStyle: { color: "#CC79A7", type: "dashed" },
                    data: Array.from({ length: 129 }, (_, i) => [
                      Math.cos((i * Math.PI) / 64),
                      Math.sin((i * Math.PI) / 64),
                    ]),
                  },
                  {
                    name: "Poles",
                    type: "scatter",
                    symbol: "cross",
                    symbolSize: 10,
                    itemStyle: { color: "#D55E00" },
                    data: analysis?.poles || [],
                  },
                  {
                    name: "Zeros",
                    type: "scatter",
                    symbolSize: 9,
                    itemStyle: { color: "#0072B2" },
                    data: analysis?.zeros || [],
                  },
                ],
              }}
              label="Computed filter poles and zeros"
            />
          </details>
          <details>
            <summary>Computed coefficients & protocol</summary>
            <pre>{JSON.stringify(analysis?.coefficients, null, 2)}</pre>
            <p>{analysis?.protocol}</p>
            <p>
              {analysis?.computation_ms?.toFixed(2)} ms · measured server
              computation on this window only.
            </p>
          </details>
        </>
      )}
      {tab === "spectrum" && session && (
        <>
          <h3>Same-window amplitude spectrum</h3>
          <Plot
            option={spectrum}
            label="Original and filtered FFT amplitude spectrum"
          />
          <h3>Short-time Fourier transform · magnitude dB</h3>
          <Plot
            option={heatmap(
              stftData,
              session.rate ? "seconds" : "packet",
              analysis?.frequency_unit || "frequency",
            )}
            label="Computed STFT spectrogram"
          />
          <p className="control-footnote">
            Spectral window:{" "}
            {analysis?.spectral_window
              ? JSON.stringify(analysis.spectral_window)
              : "No contiguous usable run."}{" "}
            {analysis?.protocol} Jittered synthetic samples use nominal rate
            without resampling; do not infer physical Doppler accuracy.
          </p>
        </>
      )}
      {tab === "motion" && session && (
        <>
          <Plot
            cursor={p}
            option={motion}
            label="Motion proxy versus empty-simulation calibrated threshold"
          />
          <p>{session.protocol}</p>
          <details>
            <summary>
              Signal variance, relative level & received packet timing
            </summary>
            <p>
              16 contiguous valid packet windows. Level is 20 log10(RMS/1
              amplitude unit), not RF dBm. Timing comes from actual stored
              simulation timestamps; untimed recordings correctly have no timing
              plot.
            </p>
            <div className="sensing-metric-grid">
              {[
                ["variance", "Median-amplitude variance", "amplitude²"],
                [
                  "relative_level_db",
                  "Relative digital level",
                  "dB re 1 amplitude unit",
                ],
                ["interval_ms", "Inter-packet timing", "ms"],
              ].map(([key, title, unit]) => (
                <div key={key}>
                  <h4>{title}</h4>
                  {session[key] ? (
                    <Plot
                      cursor={p}
                      option={{
                        ...base,
                        yAxis: { ...base.yAxis, name: unit },
                        series: [
                          line(
                            title,
                            session[key].map((v: number, i: number) => [i, v]),
                            "#0072B2",
                          ),
                        ],
                      }}
                      label={title}
                    />
                  ) : (
                    <p>
                      Timing unavailable in this recording; no rate or interval
                      invented.
                    </p>
                  )}
                </div>
              ))}
            </div>
          </details>
          <h3>Events · heuristic transitions</h3>
          {session.events.length ? (
            <table>
              <thead>
                <tr>
                  <th>Start packet</th>
                  <th>End packet · exclusive</th>
                  <th>Event</th>
                  <th>Inspect</th>
                </tr>
              </thead>
              <tbody>
                {session.events.map((e: D) => (
                  <tr key={e.start}>
                    <td>{e.start}</td>
                    <td>{e.end}</td>
                    <td>{e.kind}</td>
                    <td>
                      <button
                        onClick={() => {
                          setCursor(e.start);
                          setPlaying(false);
                        }}
                      >
                        Jump here
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p>
              No above-threshold event. Recorded data have no automatic
              empty-room calibration.
            </p>
          )}
        </>
      )}
      {tab === "experiments" && (
        <>
          <p>
            These controls generate a new synthetic channel only after Apply &
            restart. They do not alter your saved CSI or trained model.
          </p>
          <div className="sensing-settings">
            {fields.map(([k, label, min, max, step, help]) => (
              <label key={k} title={help}>
                {label}
                <input
                  type="number"
                  disabled={recordingSegment}
                  min={min}
                  max={max}
                  step={step}
                  value={config[k]}
                  onChange={(e) =>
                    setConfig((c) => ({ ...c, [k]: +e.target.value }))
                  }
                />
                <small>{help}</small>
              </label>
            ))}
          </div>
          <button
            disabled={recordingSegment || source !== "simulation" || busy}
            onClick={load}
          >
            Apply & restart simulation
          </button>
          <button
            disabled={recordingSegment || source !== "simulation" || busy}
            title="Restart with the current settings and recalculate mean+kSD on a separate generated empty-room baseline."
            onClick={load}
          >
            Calibrate simulated empty room & restart
          </button>
          <button
            disabled={!session || !simulated}
            onClick={() => {
              if (session)
                setComparisons((c) => [
                  ...c.slice(-7),
                  {
                    config: session.config,
                    packets: session.packets,
                    missing: session.packet_audit.missing_or_invalid,
                    threshold: session.threshold,
                  },
                ]);
            }}
          >
            Capture experiment comparison
          </button>
          <button onClick={() => setComparisons([])}>Clear comparisons</button>
          <p>
            Empty-room threshold is recalculated from a separate generated empty
            scenario at each Apply. Calibration is a simulation exercise, not
            validation on real people.
          </p>
          {comparisons.map((c, i) => (
            <details key={i}>
              <summary>
                Comparison {i + 1} · {c.config.scenario} · seed {c.config.seed}{" "}
                · missing {c.missing}/{c.packets}
              </summary>
              <pre>{JSON.stringify(c, null, 2)}</pre>
            </details>
          ))}
        </>
      )}
      {tab === "recordings" && (
        <>
          <h3>Record a replay segment. Keep the original.</h3>
          <p>
            These are source-labelled finite buffers, not a live hardware
            acquisition claim. Segment recording follows the shared replay
            cursor, up to10,000 packets. Stop before changing signal settings.
          </p>
          {session && (
            <>
              <div className="sensing-actions">
                <button
                  disabled={recordingSegment || p > session.packets - 32}
                  onClick={() => {
                    setClipStart(p);
                    setClipEnd(p + 1);
                    setRecordingSegment(true);
                    setPlaying(true);
                  }}
                >
                  Start recording replay segment
                </button>
                <button
                  disabled={!recordingSegment}
                  onClick={() => {
                    setRecordingSegment(false);
                    setPlaying(false);
                  }}
                >
                  Stop recording segment
                </button>
                <span role="status">
                  {recordingSegment ? "Recording replay" : "Stopped"} ·{" "}
                  {Math.max(0, clipEnd - clipStart)} selected packets
                </span>
              </div>
              <div className="sensing-actions">
                <label>
                  First packet
                  <input
                    disabled={recordingSegment}
                    type="number"
                    min={0}
                    max={session.packets - 32}
                    value={clipStart}
                    onChange={(e) => setClipStart(+e.target.value)}
                  />
                </label>
                <label>
                  End packet · exclusive
                  <input
                    disabled={recordingSegment}
                    type="number"
                    min={clipStart + 32}
                    max={Math.min(session.packets, clipStart + 10000)}
                    value={clipEnd}
                    onChange={(e) => setClipEnd(+e.target.value)}
                  />
                </label>
              </div>
              <p>
                JSON/CSV are trace summaries; NPZ preserves complex channel
                where available. Every export includes its source and original
                packet range.
              </p>
              <div className="sensing-actions">
                {["json", "csv", "npz"].map((v) => (
                  <a
                    className="button"
                    key={v}
                    href={
                      "/api/sensing/sessions/" +
                      session.id +
                      "/export/" +
                      v +
                      "?start=" +
                      clipStart +
                      "&end=" +
                      clipEnd
                    }
                  >
                    Download {v.toUpperCase()}
                  </a>
                ))}
                <button
                  disabled={
                    recordingSegment ||
                    clipEnd - clipStart < 32 ||
                    clipEnd - clipStart > 10000
                  }
                  onClick={async () => {
                    try {
                      const r = await fetch(
                          "/api/sensing/sessions/" + session.id + "/save",
                          {
                            method: "POST",
                            headers: { "Content-Type": "application/json" },
                            body: JSON.stringify({
                              start: clipStart,
                              end: clipEnd,
                            }),
                          },
                        ),
                        d = await r.json();
                      if (!r.ok)
                        throw Error(
                          d.detail ||
                            "Choose a valid segment, then save again.",
                        );
                      setNotice(
                        "Saved in the shared Library: " +
                          d.asset.name +
                          " · SHA-256 " +
                          d.sha256,
                      );
                      await refreshRecordings();
                    } catch (e) {
                      setError((e as Error).message);
                    }
                  }}
                >
                  Save selected NPZ to Library
                </button>
                <a href="#/workbench?tab=library">Open shared Library</a>
              </div>
            </>
          )}
          <h3>Saved sensing recordings</h3>
          <button onClick={refreshRecordings}>Refresh list</button>
          {recordings.length ? (
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Recording</th>
                    <th>Source</th>
                    <th>Bytes</th>
                    <th>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {recordings.map((r) => (
                    <tr key={r.id}>
                      <td>{r.title || r.name}</td>
                      <td>{r.synthetic ? "Simulation" : "Recorded input"}</td>
                      <td>{r.size.toLocaleString()}</td>
                      <td>
                        <button
                          onClick={async () => {
                            try {
                              const response = await fetch(
                                  "/api/sensing/recordings/" + r.id + "/open",
                                  { method: "POST" },
                                ),
                                d = await response.json();
                              if (!response.ok)
                                throw Error(
                                  d.detail ||
                                    "Restore this recording from the Library first.",
                                );
                              setSession(d);
                              setCursor(0);
                              setPlaying(false);
                              setAnalysis(null);
                              setNotice(
                                "Reopened " +
                                  r.name +
                                  "; original saved bytes preserved.",
                              );
                            } catch (e) {
                              setError((e as Error).message);
                            }
                          }}
                        >
                          Replay
                        </button>
                        <a href={"/api/media/" + r.id + "/file"}>
                          Download original NPZ
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p>
              No saved sensing sessions yet. Save a selected segment above;
              manage deletion and restore in the shared Library.
            </p>
          )}
          <p>
            In-memory previews expire after four loaded sessions. Saved
            originals persist locally.
          </p>
        </>
      )}
      {tab === "diagnostics" && (
        <>
          <h3>What this browser and server actually report</h3>
          <button
            onClick={async () => {
              try {
                const r = await fetch("/api/health"),
                  d = await r.json();
                setHealth({ http_status: r.status, ...d });
              } catch {
                setHealth({
                  error: "Server unavailable. Start Orbit and retry.",
                });
              }
            }}
          >
            Check server health
          </button>
          <dl>
            <dt>Network request to server</dt>
            <dd>
              {health ? health.http_status || health.error : "Not checked"}
            </dd>
            <dt>Source</dt>
            <dd>{session?.source || "No session"}</dd>
            <dt>Buffer</dt>
            <dd>{session ? session.packets + " packets" : "Not loaded"}</dd>
            <dt>CSI hardware</dt>
            <dd>Not verified by this studio</dd>
            <dt>Secure browser context</dt>
            <dd>
              {window.isSecureContext
                ? "Yes"
                : "No · phone camera/microphone may require trusted HTTPS"}
            </dd>
            <dt>WebGL rendering</dt>
            <dd>
              Actual FPS shown inside the scene. GPU fallback is explicit.
            </dd>
          </dl>
          <pre>
            {JSON.stringify(
              {
                session: session?.id,
                simulation: session?.config,
                filter,
                health,
              },
              null,
              2,
            )}
          </pre>
        </>
      )}
      {tab === "theory" && (
        <>
          <label>
            Find a concept
            <input
              placeholder="Try FFT, motion, phase…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </label>
          <div className="sensing-lessons">
            {lessons
              .filter((l) =>
                l.join(" ").toLowerCase().includes(query.toLowerCase()),
              )
              .map(([title, equation, explanation, q, a]) => (
                <article className="control-card" key={title}>
                  <h3>{title}</h3>
                  <p className="sensing-equation">{equation}</p>
                  <p>{explanation}</p>
                  <details>
                    <summary>Viva: {q}</summary>
                    <p>{a}</p>
                  </details>
                </article>
              ))}
          </div>
        </>
      )}
    </div>
  );
}
