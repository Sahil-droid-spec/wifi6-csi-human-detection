import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react";
import { SensingWorkbench } from "./SensingWorkbench";
const SpatialScene = lazy(() => import("./SpatialScene"));
import * as echarts from "echarts";
import {
  Activity,
  ArrowUpRight,
  Pause,
  Play,
  RotateCcw,
  Download,
  Radio,
  SlidersHorizontal,
  Maximize2,
} from "lucide-react";
import { call } from "./Extensions";
import { Progression } from "./Demo";
import "./control-room.css";

type D = Record<string, any>;

function Plot({ option, label }: { option: D; label: string }) {
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
      chart.current = null;
    };
  }, []);
  useEffect(() => {
    chart.current?.setOption(option, true);
  }, [option]);
  return (
    <div className="control-plot">
      <div ref={ref} role="img" aria-label={label} />
      <button
        className="icon-btn"
        aria-label={"Download " + label}
        onClick={() => {
          if (!chart.current) return;
          const a = document.createElement("a");
          a.href = chart.current.getDataURL({
            pixelRatio: 2,
            backgroundColor: getComputedStyle(document.documentElement)
              .getPropertyValue("--surface")
              .trim(),
          });
          a.download = "Orbit-" + label.replaceAll(" ", "-") + ".png";
          a.click();
        }}
      >
        <Download size={14} />
      </button>
    </div>
  );
}

export function ControlRoom({
  state,
  capture,
  onSelect,
  onNavigate,
  reduced,
  studio = false,
}: {
  studio?: boolean;
  state: D;
  capture?: D;
  onSelect: (id: string) => void;
  onNavigate: (page: string) => void;
  reduced: boolean;
}) {
  const [tab, setTab] = useState(studio ? "studio" : "overview"),
    [scenario, setScenario] = useState("walking"),
    [playing, setPlaying] = useState(true),
    [sceneTime, setSceneTime] = useState(0),
    [theme, setTheme] = useState(0);
  const [start, setStart] = useState(0),
    [window, setWindow] = useState<D | null>(null),
    [dsp, setDsp] = useState<D | null>(null),
    [filter, setFilter] = useState("fir"),
    [cutoff, setCutoff] = useState(0.08),
    [taps, setTaps] = useState(15),
    [win, setWin] = useState("hamming"),
    [error, setError] = useState(""),
    [busy, setBusy] = useState(false),
    [saved, setSaved] = useState(false);
  const captures = state.captures || [];
  useEffect(() => {
    const f = () => setTheme((v) => v + 1);
    globalThis.addEventListener("orbit-theme", f);
    return () => globalThis.removeEventListener("orbit-theme", f);
  }, []);
  const mono=["paper","graphite"].includes(document.documentElement.dataset.theme||"");
  const themeStyle = getComputedStyle(document.documentElement),
    ink = themeStyle.getPropertyValue("--text").trim(),
    muted = themeStyle.getPropertyValue("--muted").trim(),
    lineColor = themeStyle.getPropertyValue("--line").trim();
  useEffect(() => {
    if (!playing || reduced) return;
    let last = performance.now();
    const timer = setInterval(() => {
      const now = performance.now();
      setSceneTime((t) => t + Math.min(0.1, (now - last) / 1000));
      last = now;
    }, 50);
    return () => clearInterval(timer);
  }, [playing, reduced]);
  useEffect(() => {
    setStart(0);
    setWindow(null);
    setDsp(null);
    setSaved(false);
  }, [capture?.id]);
  const settings = {
    capture_id: capture?.id,
    operation: filter,
    taps,
    window: win,
    cutoff,
    order: 4,
    kind: "lowpass",
    length: 1024,
    start,
  };
  useEffect(() => {
    if (!capture) {
      setWindow(null);
      setDsp(null);
      return;
    }
    let live = true;
    const controller = new AbortController();
    setBusy(true);
    setError("");
    setWindow(null);
    setDsp(null);
    setSaved(false);
    const timer = setTimeout(async () => {
      try {
        const r = await fetch(
          "/api/captures/" + capture.id + "?start=" + start + "&length=1024",
          { signal: controller.signal },
        );
        const data = await r.json();
        if (!r.ok) throw Error(data.detail || "Choose another recording.");
        if (!live) return;
        setWindow(data);
        {
          const result = await fetch("/api/control/process", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(settings),
            signal: controller.signal,
          });
          const d = await result.json();
          if (!result.ok) throw Error(d.detail || "Check the filter settings.");
          if (live) setDsp(d);
        }
      } catch (e) {
        if (live && (e as Error).name !== "AbortError")
          setError((e as Error).message);
      } finally {
        if (live) setBusy(false);
      }
    }, 220);
    return () => {
      live = false;
      clearTimeout(timer);
      controller.abort();
    };
  }, [capture?.id, start, filter, taps, win, cutoff]);
  const valid = window
      ? window.trace.length - window.invalid_indices.length
      : 0,
    source = capture?.synthetic ? "SIMULATION" : "RECORDED DATA";
  const base: D = {
    backgroundColor: "transparent",
    animation: !reduced,
    textStyle: { color: ink, fontFamily: "Segoe UI" },
    tooltip: { trigger: "axis" },
    grid: { left: 58, right: 22, top: 25, bottom: 62 },
    legend: { textStyle: { color: ink }, bottom: 0 },
    xAxis: {
      type: "value",
      name: "packet",
      nameLocation: "middle",
      nameGap: 30,
      axisLine: { lineStyle: { color: muted } },
      splitLine: { lineStyle: { color: lineColor } },
    },
    yAxis: {
      type: "value",
      scale: true,
      splitLine: { lineStyle: { color: lineColor } },
    },
    dataZoom: [{ type: "inside" }, { type: "slider", height: 12, bottom: 35 }],
  };
  const trace = useMemo(
    () => ({
      ...base,
      series: [
        {
          name: "Original",
          type: "line",
          showSymbol: false,
          connectNulls: false,
          lineStyle: { color: mono?ink:"#56B4E9", width: 1.7 },
          data:
            window?.packet.map((p: number, i: number) => [
              p,
              window.trace[i],
            ]) || [],
        },
        {
          name: "Filtered",
          type: "line",
          showSymbol: false,
          lineStyle: { color: mono?ink:"#E69F00", type: "dashed", width: 1.8 },
          data:
            dsp?.processed?.map((v: number, i: number) => [start + i, v]) || [],
        },
      ],
    }),
    [window, dsp, reduced, start, theme],
  );
  const spectrum = useMemo(
    () => ({
      ...base,
      xAxis: { ...base.xAxis, name: "cycles / packet" },
      yAxis: { ...base.yAxis, name: "magnitude" },
      series: [
        {
          name: "Original",
          type: "line",
          showSymbol: false,
          lineStyle: { color: mono?ink:"#56B4E9" },
          data:
            dsp?.frequency.map((v: number, i: number) => [
              v,
              dsp.raw_spectrum[i],
            ]) || [],
        },
        {
          name: "Filtered",
          type: "line",
          showSymbol: false,
          lineStyle: { color: mono?ink:"#E69F00", type: "dashed" },
          data:
            dsp?.frequency.map((v: number, i: number) => [
              v,
              dsp.processed_spectrum[i],
            ]) || [],
        },
      ],
    }),
    [window, dsp, reduced, start, theme],
  );
  const responsePlot = useMemo(
    () => ({
      ...base,
      xAxis: { ...base.xAxis, name: "cycles / packet" },
      yAxis: { ...base.yAxis, name: "response dB" },
      series: [
        {
          name: "Filter response",
          type: "line",
          showSymbol: false,
          lineStyle: { color: mono?ink:"#009E73" },
          data:
            dsp?.response_frequency.map((v: number, i: number) => [
              v,
              dsp.response_db[i],
            ]) || [],
        },
      ],
    }),
    [window, dsp, reduced, start, theme],
  );
  const heat = useMemo<D>(
    () => ({
      backgroundColor: "transparent",
      animation: false,
      textStyle: { color: ink },
      tooltip: { position: "top" },
      grid: { left: 55, right: 22, top: 20, bottom: 60 },
      xAxis: {
        type: "category",
        name: "packet",
        data: window?.heatmap_packet.map(String) || [],
        axisLabel: { color: ink },
      },
      yAxis: {
        type: "category",
        name: "subcarrier",
        data: window?.heatmap_subcarrier.map(String) || [],
        axisLabel: { color: ink },
      },
      visualMap: {
        min: window
          ? Math.min(...window.heatmap.flat().filter(Number.isFinite))
          : 0,
        max: window
          ? Math.max(...window.heatmap.flat().filter(Number.isFinite))
          : 1,
        orient: "horizontal",
        bottom: 0,
        left: "center",
        textStyle: { color: ink },
        inRange: { color: mono?["#eeeeee","#222222"]:["#102b46", "#0072B2", "#56B4E9", "#E69F00"] },
      },
      series: [
        {
          type: "heatmap",
          progressive: 0,
          encode: { x: 0, y: 1, value: 2 },
          data:
            window?.heatmap.flatMap((row: number[], y: number) =>
              row.flatMap((value: number, x: number) =>
                Number.isFinite(value) &&
                !window.invalid_indices.includes(
                  window.heatmap_packet[x] - start,
                )
                  ? [[x, y, value]]
                  : [],
              ),
            ) || [],
        },
      ],
    }),
    [window, start, theme],
  );
  return (
    <div className="control-room">
      <header className="control-title">
        <div>
          <span className="control-eyebrow">
            ORBIT / RESEARCH WORKSPACE · 5.0 DEVELOPMENT
          </span>
          <h1>A clearer view of the signal.</h1>
          <p>Your recordings, your processing, one connected workspace.</p>
        </div>
        <span className="control-source">
          <i />
          {capture
            ? capture.synthetic
              ? "Simulation recording"
              : "Recorded input"
            : "Choose a recording"}
        </span>
      </header>
      <div
        className="control-tabs"
        role="tablist"
        aria-label="Command center views"
      >
        {[
          ["overview", "Command center"],
          ["signals", "Signal & spectrum"],
          ["models", "Model evidence"],
          ["devices", "Devices & transfer"],
          ["studio", "3D sensing studio"],
        ].map(([k, v]) => (
          <button
            key={k}
            role="tab"
            aria-selected={tab === k}
            className={tab === k ? "active" : ""}
            onClick={() => setTab(k)}
          >
            {v}
          </button>
        ))}
      </div>
      <section className="control-input">
        <label>
          Saved CSI recording
          <select
            value={capture?.id || ""}
            onChange={(e) => onSelect(e.target.value)}
          >
            <option value="">Choose a saved input</option>
            {captures.map((c: D) => (
              <option key={c.id} value={c.id}>
                {c.name}
              </option>
            ))}
          </select>
        </label>
        <button onClick={() => onNavigate("data")}>
          Open Library <ArrowUpRight size={14} />
        </button>
        <button onClick={() => onNavigate("simulation")}>
          Create Simulation input <ArrowUpRight size={14} />
        </button>
      </section>
      {error && (
        <p className="control-error" role="alert">
          {error}
        </p>
      )}
      <div className="control-stats">
        {[
          [
            "Input window",
            window ? window.trace.length + " packets" : "—",
            "Actual selected trace",
          ],
          [
            "Usable packets",
            window ? valid + " / " + window.trace.length : "—",
            "Zero/NaN gaps stay visible",
          ],
          [
            "Bandwidth",
            capture ? capture.bandwidth + " MHz" : "—",
            "Recording metadata",
          ],
          ["Prediction", "Open Replay", "No prediction invented here"],
        ].map(([k, v, n]) => (
          <article key={k}>
            <span>{k}</span>
            <strong>{v}</strong>
            <small>{n}</small>
          </article>
        ))}
      </div>
      {tab === "overview" && (
        <div className="control-scene-grid">
          <section className="control-card">
            <div className="control-card-head">
              <div>
                <span className="control-eyebrow">
                  INTERACTIVE 3D ENVIRONMENT
                </span>
                <h3>Explore the channel in space.</h3>
              </div>
              <span className="control-tag">Illustration</span>
            </div>
            <div className="control-scene-tools">
              <button
                className="control-play"
                aria-label={
                  playing ? "Pause illustration" : "Play illustration"
                }
                onClick={() => setPlaying(!playing)}
              >
                {playing ? <Pause size={16} /> : <Play size={16} />}
              </button>
              <button onClick={() => setTab("studio")}>
                Open synchronized 3D studio →
              </button>
            </div>
            <Suspense fallback={<p>Loading the WebGL 3D environment…</p>}>
              <SpatialScene onTogglePlay={()=>setPlaying(v=>!v)} onRestart={()=>{setSceneTime(0);setPlaying(false);}}
                frame={{
                  time: sceneTime,
                  scenario,
                  playing,
                  reduced,
                  source: "ILLUSTRATION",
                }}
              />
            </Suspense>
            <div className="control-scene-footer">
              <label>
                Illustrated scenario
                <select
                  value={scenario}
                  onChange={(e) => setScenario(e.target.value)}
                >
                  <option value="empty">Empty scene</option>
                  <option value="still">One person still</option>
                  <option value="walking">One person walking</option>
                  <option value="two">Two people</option>
                </select>
              </label>
              <label>
                Animation time · {sceneTime.toFixed(1)} s
                <input
                  type="range"
                  min={0}
                  max={60}
                  step={0.1}
                  value={sceneTime}
                  onChange={(e) => {
                    setSceneTime(+e.target.value);
                    setPlaying(false);
                  }}
                />
              </label>
              <button
                aria-label="Reset view"
                onClick={() => {
                  setSceneTime(0);
                }}
              >
                <RotateCcw size={16} />
              </button>
            </div>
            <p className="control-footnote">
              Procedural 3D illustration. This is not a human pose recovered
              from Wi-Fi. Changing this scene does not change your recording,
              label or prediction.
            </p>
          </section>
          <aside className="control-card control-story">
            <span className="control-eyebrow">THE ENGINEERING STORY</span>
            <h3>From a channel to a decision.</h3>
            <ol>
              {[
                ["Capture", "Real or explicitly generated CSI."],
                ["Inspect", "Keep packet loss and source visible."],
                [
                  "Process",
                  "Compare the same input before and after filtering.",
                ],
                ["Learn", "Train only on the training groups."],
                ["Validate", "Use held-out recordings and report failures."],
              ].map(([t, d], i) => (
                <li key={t}>
                  <span>{i + 1}</span>
                  <div>
                    <strong>{t}</strong>
                    <p>{d}</p>
                  </div>
                </li>
              ))}
            </ol>
            <button
              className="control-primary"
              onClick={() => onNavigate("replay")}
            >
              Open held-out Replay <ArrowUpRight size={16} />
            </button>
            <button onClick={() => onNavigate("presence")}>
              Compare baseline and Hamming <ArrowUpRight size={16} />
            </button>
          </aside>
        </div>
      )}
      {(tab === "overview" || tab === "signals") && (
        <>
          <section className="control-card">
            <div className="control-card-head">
              <div>
                <span className="control-eyebrow">SAME-INPUT DSP</span>
                <h3>Original and filtered. Side by side.</h3>
              </div>
              <span className="control-tag">
                {capture ? source : "No input"}
              </span>
            </div>
            <div className="control-filter">
              <label>
                Processing
                <select
                  value={filter}
                  onChange={(e) => setFilter(e.target.value)}
                >
                  <option value="fir">Windowed FIR low-pass</option>
                  <option value="butterworth">Butterworth low-pass</option>
                  <option value="moving_average">Moving average</option>
                </select>
              </label>
              <label>
                Window
                <select value={win} onChange={(e) => setWin(e.target.value)}>
                  {["hamming", "hann", "blackman", "kaiser"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
              <label>
                Odd tap count
                <input
                  type="number"
                  min={3}
                  max={127}
                  step={2}
                  value={taps}
                  onChange={(e) => setTaps(+e.target.value)}
                />
              </label>
              <label>
                Cutoff · cycles/packet
                <input
                  type="number"
                  min={0.001}
                  max={0.499}
                  step={0.01}
                  value={cutoff}
                  onChange={(e) => setCutoff(+e.target.value)}
                />
              </label>
            </div>
            {capture && (
              <label className="control-window">
                Window start · packet {start}
                <input
                  type="range"
                  min={0}
                  max={Math.max(0, (capture.packets || 1024) - 1024)}
                  step={128}
                  value={start}
                  onChange={(e) => setStart(+e.target.value)}
                />
              </label>
            )}
            {busy && (
              <div className="control-skeleton" role="status">
                Computing the selected window…
              </div>
            )}
            {!capture && (
              <div className="control-empty">
                <Radio size={28} />
                <h3>Start with one recording.</h3>
                <p>
                  Select a saved input above. Graphs appear only after its
                  samples are loaded.
                </p>
                <button onClick={() => onNavigate("data")}>
                  Choose in Library
                </button>
              </div>
            )}
            {window && !busy && (
              <>
                <div className="control-two-plots">
                  <div>
                    <h4>Amplitude / packet</h4>
                    <Plot option={trace} label="Original and filtered CSI" />
                  </div>
                  <div>
                    <h4>Frequency content</h4>
                    {dsp ? (
                      <Plot
                        option={spectrum}
                        label="Same-input amplitude spectrum"
                      />
                    ) : (
                      <p>
                        Filtering and spectrum withheld: this window contains
                        invalid packets. Choose a clean window; no zero-filled
                        filter result is shown.
                      </p>
                    )}
                  </div>
                </div>
                <p className="control-footnote">
                  {dsp?.note ||
                    "Invalid samples remain gaps. No filtered metrics are invented."}{" "}
                  {dsp?.spectral_window &&
                    "Spectrum: packets " +
                      dsp.spectral_window.start +
                      "–" +
                      (dsp.spectral_window.end - 1) +
                      ", " +
                      dsp.spectral_window.samples +
                      " contiguous samples."}{" "}
                  Smoother does not establish better detection.
                </p>
                {dsp && (
                  <details>
                    <summary>Inspect filter response and computation</summary>
                    <Plot
                      option={responsePlot}
                      label="Filter frequency response"
                    />
                    <p className="control-footnote">
                      Backend DSP computation:{" "}
                      {dsp.extra.measured_elapsed_ms.toFixed(2)} ms on this
                      selected window.{" "}
                      {dsp.extra.estimated_multiplications.toLocaleString()}{" "}
                      estimated multiplications ·{" "}
                      {dsp.extra.computation_protocol}. This is not phone
                      transfer latency.
                    </p>
                  </details>
                )}
                <button
                  disabled={!dsp || saved || busy}
                  onClick={async () => {
                    try {
                      setBusy(true);
                      setError("");
                      await call("control/save", settings);
                      setSaved(true);
                    } catch (e) {
                      setError((e as Error).message);
                    } finally {
                      setBusy(false);
                    }
                  }}
                >
                  {saved
                    ? "DSP settings saved in run history"
                    : "Save this DSP experiment"}
                </button>
              </>
            )}
          </section>
          {window && (
            <section className="control-card">
              <div className="control-card-head">
                <h3>Subcarrier amplitude map</h3>
                <span className="control-tag">
                  Selected input · no inferred pose
                </span>
              </div>
              <Plot option={heat} label="CSI subcarrier heatmap" />
              <p className="control-footnote">
                Subsampled preview of actual amplitude. Invalid packet columns
                are omitted. Colours show amplitude, not presence confidence.
              </p>
            </section>
          )}
        </>
      )}
      {tab === "studio" && (
        <SensingWorkbench
          capture={capture}
          reduced={reduced}
          models={state.models || []}
        />
      )}
      {tab === "models" && (
        <div className="control-models">
          <Progression state={state} capture={capture} />
          <button onClick={() => onNavigate("learning")}>
            Train / compare in Learning Lab <ArrowUpRight size={16} />
          </button>
          <button onClick={() => onNavigate("results")}>
            Recorded Evidence <ArrowUpRight size={16} />
          </button>
        </div>
      )}
      {tab === "devices" && (
        <div className="control-destinations">
          {[
            [
              "Connect the phone",
              "Fresh QR, correct LAN address and Connection Doctor.",
              "settings",
              Radio,
            ],
            [
              "Move an original",
              "Normal file transfer and actual byte progress.",
              "transfer",
              ArrowUpRight,
            ],
            [
              "Send encrypted sound",
              "Create, record, recover and inspect missing packets.",
              "link",
              Activity,
            ],
            [
              "Check the setup",
              "Dependencies, storage, TLS and hardware adapters.",
              "workbench?tab=diagnostics",
              SlidersHorizontal,
            ],
          ].map(([title, description, route, Icon]: any) => (
            <button
              className="control-card"
              key={title}
              onClick={() => {
                location.hash = "/" + route;
              }}
            >
              <Icon size={24} />
              <h3>{title}</h3>
              <p>{description}</p>
              <ArrowUpRight size={18} />
            </button>
          ))}
        </div>
      )}
      <footer className="control-footer">
        <span>
          Local processing · source preserved · no hidden measurements
        </span>
        <button onClick={() => onNavigate("plan")}>
          <Maximize2 size={14} /> Open recording plan
        </button>
      </footer>
    </div>
  );
}
