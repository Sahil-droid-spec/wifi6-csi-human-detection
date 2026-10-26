import React, { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import * as echarts from "echarts";
import {
  Activity,
  ArrowDownToLine,
  ArrowRight,
  AudioLines,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  ChevronLeft,
  ChevronRight,
  CircleHelp,
  CircuitBoard,
  Database,
  ExternalLink,
  FileUp,
  FlaskConical,
  FolderOpen,
  GitBranch,
  Home,
  Info,
  Layers3,
  LayoutDashboard,
  LoaderCircle,
  LockKeyhole,
  Menu,
  Network,
  Pause,
  Play,
  Plus,
  Radio,
  RotateCcw,
  Search,
  Settings2,
  ShieldCheck,
  SlidersHorizontal,
  Smartphone,
  Sparkles,
  Upload,
  Waves,
  Wifi,
  X,
  Zap,
  BrainCircuit,
  Trash2,
  Download,
  CircleDot,
} from "lucide-react";
import "./styles.css";
type Dict = Record<string, any>;
type Page =
  | "intro"
  | "overview"
  | "data"
  | "dsp"
  | "learning"
  | "replay"
  | "results"
  | "modes"
  | "settings"
  | "upload"
  | "media";
const stages = [
  "Receive",
  "Window",
  "Filter",
  "Spectrum",
  "Features",
  "Reason",
  "Model",
  "Verdict",
];
const stagePages: Page[] = [
  "data",
  "dsp",
  "dsp",
  "dsp",
  "dsp",
  "learning",
  "learning",
  "replay",
];
const nav = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "data", label: "Data & captures", icon: Database },
  { id: "media", label: "Recordings & media", icon: FolderOpen },
  { id: "dsp", label: "Signal Studio", icon: AudioLines },
  { id: "learning", label: "Learning Lab", icon: BrainCircuit },
  { id: "replay", label: "Detect & replay", icon: Play },
  { id: "results", label: "Results & evidence", icon: FlaskConical },
  { id: "modes", label: "Wi-Fi modes", icon: Radio },
  { id: "settings", label: "Server & settings", icon: Settings2 },
];
const pretty = (n: any, d = 3) =>
  typeof n === "number" ? n.toFixed(d) : String(n ?? "—");
const percent = (n: any) => `${(Number(n) * 100).toFixed(1)}%`;
const color = ["#22d3ee", "#fb923c", "#a78bfa", "#4f7dff", "#34d399"];
async function api(path: string, body?: any, method?: string) {
  const r = await fetch("/api/" + path, {
    method: method || (body ? "POST" : "GET"),
    credentials: "same-origin",
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!r.ok) {
    const e = await r.json().catch(() => ({ detail: r.statusText }));
    throw new Error(
      "Error: " +
        (typeof e.detail === "string" ? e.detail : JSON.stringify(e.detail)),
    );
  }
  return r.json();
}
function Badge({
  children,
  tone = "cyan",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  return <span className={"badge " + tone}>{children}</span>;
}
function Mark() {
  return (
    <span className="orbit-mark">
      <i />
      <b />
    </span>
  );
}
function Button({
  children,
  onClick,
  secondary = false,
  disabled = false,
  className = "",
  type = "button",
}: {
  children: React.ReactNode;
  onClick?: () => void;
  secondary?: boolean;
  disabled?: boolean;
  className?: string;
  type?: "button" | "submit";
}) {
  return (
    <button
      type={type}
      onClick={onClick}
      disabled={disabled}
      className={`${secondary ? "button secondary" : "button"} ${className}`}
    >
      {children}
    </button>
  );
}
function Empty({
  icon: Icon = AudioLines,
  title,
  children,
  action,
}: {
  icon?: any;
  title: string;
  children: React.ReactNode;
  action?: React.ReactNode;
}) {
  return (
    <div className="empty">
      <span className="empty-icon">
        <Icon size={25} />
      </span>
      <h3>{title}</h3>
      <p>{children}</p>
      {action}
    </div>
  );
}
function Note({
  children,
  tone = "amber",
}: {
  children: React.ReactNode;
  tone?: string;
}) {
  const text = typeof children === "string" ? children : "";
  const essential =
    tone === "red" ||
    /confound|mismatch|no accepted|outside|failed|invalid|used to fit|in-training|simulator research|proposed architecture/i.test(
      text,
    );
  if (essential)
    return (
      <div className={"note essential " + tone}>
        <div>{children}</div>
      </div>
    );
  return (
    <details className={"method-note " + tone}>
      <summary>Method & data notes</summary>
      <div>{children}</div>
    </details>
  );
}

function Chart({
  series,
  x,
  axis = "Packet index",
  height = 260,
  heatmap,
  labels,
  yName = "Subcarrier",
  exportName = "orbit-plot",
}: {
  series?: {
    name: string;
    data: number[];
    color?: string;
    x?: number[];
    dashed?: boolean;
  }[];
  x?: number[];
  axis?: string;
  height?: number;
  heatmap?: number[][];
  yName?: string;
  labels?: { x: any[]; y: any[] };
  exportName?: string;
}) {
  const [chartTheme, setChartTheme] = useState(
    document.documentElement.dataset.theme || "light",
  );
  const isLight = ["light", "soft"].includes(chartTheme);
  useEffect(() => {
    const change = () =>
      setChartTheme(document.documentElement.dataset.theme || "light");
    window.addEventListener("orbit-theme", change);
    return () => window.removeEventListener("orbit-theme", change);
  }, []);
  const ref = useRef<HTMLDivElement>(null);
  const instance = useRef<echarts.ECharts | null>(null);
  useEffect(() => {
    if (!ref.current) return;
    const c = echarts.init(ref.current, undefined, { renderer: "canvas" });
    instance.current = c;
    const ro = new ResizeObserver(() => c.resize());
    ro.observe(ref.current);
    return () => {
      ro.disconnect();
      c.dispose();
    };
  }, []);
  useEffect(() => {
    const c = instance.current;
    if (!c) return;
    let option: Dict = {
      animation: false,
      backgroundColor: isLight ? "#ffffff" : "#121c2d",
      color,
      tooltip: {
        trigger: "axis",
        backgroundColor: isLight ? "#ffffff" : "#192940",
        borderColor: "#2b3b52",
        textStyle: { color: isLight ? "#26364a" : "#e7edf8" },
      },
      legend: {
        top: 0,
        textStyle: { color: isLight ? "#586577" : "#a2b0c7" },
        itemWidth: 16,
        itemHeight: 2,
      },
      grid: { left: 55, right: 24, top: 40, bottom: 58 },
      xAxis: {
        type: "value",
        name: axis,
        nameLocation: "middle",
        nameGap: 32,
        axisLabel: { color: isLight ? "#5c6a7c" : "#8293ae" },
        nameTextStyle: { color: isLight ? "#5c6a7c" : "#8293ae" },
        splitLine: { show: false },
        axisLine: { lineStyle: { color: "#2b3b52" } },
      },
      yAxis: {
        type: "value",
        scale: true,
        axisLabel: { color: isLight ? "#5c6a7c" : "#8293ae" },
        splitLine: {
          lineStyle: { color: isLight ? "#e1e7ee" : "#233149", type: "dashed" },
        },
        axisLine: { show: false },
      },
      dataZoom: [{ type: "inside", filterMode: "none" }],
      series: (series || []).map((s, i) => ({
        type: "line",
        name: s.name,
        showSymbol: false,
        sampling: "lttb",
        lineStyle: {
          width: 1.7,
          color: s.color || color[i % 5],
          type: s.dashed ? "dashed" : "solid",
        },
        data: s.data.map((v, j) => [(s.x || x)?.[j] ?? j, v]),
      })),
    };
    if (heatmap) {
      const all = heatmap.flat();
      option = {
        ...option,
        tooltip: { position: "top" },
        legend: { show: false },
        xAxis: {
          type: "category",
          data: labels?.x,
          axisLabel: {
            color: isLight ? "#5c6a7c" : "#8293ae",
            interval: "auto",
          },
          name: "Packet index",
          nameLocation: "middle",
          nameGap: 28,
        },
        yAxis: {
          type: "category",
          data: labels?.y,
          axisLabel: { color: isLight ? "#5c6a7c" : "#8293ae" },
          name: yName,
        },
        visualMap: {
          min: Math.min(...all),
          max: Math.max(...all),
          calculable: false,
          orient: "horizontal",
          left: "center",
          bottom: 0,
          textStyle: { color: isLight ? "#5c6a7c" : "#8293ae" },
          inRange: {
            color: ["#101b35", "#2442a1", "#209ac2", "#22d3ee", "#d9f9f4"],
          },
        },
        series: [
          {
            type: "heatmap",
            data: heatmap.flatMap((row, i) => row.map((v, j) => [j, i, v])),
            progressive: 2000,
          },
        ],
        dataZoom: [],
      };
    }
    c.setOption(option, true);
  }, [series, x, axis, heatmap, labels, chartTheme]);
  return (
    <div className="chart-wrap">
      <div ref={ref} style={{ height }} role="img" aria-label={exportName} />
      <button
        className="chart-export icon-btn"
        title="Export plot as PNG"
        onClick={() => {
          const a = document.createElement("a");
          a.href =
            instance.current?.getDataURL({
              type: "png",
              pixelRatio: 2,
              backgroundColor: isLight ? "#ffffff" : "#121c2d",
            }) || "";
          a.download = exportName + ".png";
          a.click();
        }}
      >
        <Download size={15} />
      </button>
    </div>
  );
}
function Ring({
  navigate,
  hasData = false,
  hasModel = false,
  compact = false,
}: {
  navigate: (p: Page) => void;
  hasData?: boolean;
  hasModel?: boolean;
  compact?: boolean;
}) {
  return (
    <div className={"ring-scene " + (compact ? "compact" : "")}>
      <div className="ring-dots" />
      <div className="ring-track" />
      <div className="ring-track inner" />
      <svg className="ring-ticks" viewBox="0 0 400 400" aria-hidden="true">
        {Array.from({ length: 80 }, (_, i) => {
          let a = (i * Math.PI) / 40;
          return (
            <line
              key={i}
              x1={200 + 149 * Math.cos(a)}
              y1={200 + 149 * Math.sin(a)}
              x2={200 + (i % 5 === 0 ? 141 : 145) * Math.cos(a)}
              y2={200 + (i % 5 === 0 ? 141 : 145) * Math.sin(a)}
              stroke={i < 25 ? "#318cab" : "#2b3b52"}
              strokeWidth={i % 5 === 0 ? 2 : 1}
            />
          );
        })}
      </svg>
      <div className="ring-center">
        <span className="tiny-label">SENSING WORKSPACE</span>
        <span className="center-symbol">
          <Waves size={34} />
        </span>
        <strong>{hasData ? "Signal ready" : "Ready when\nyou are."}</strong>
        <span className="ring-status">
          <i />
          {hasData
            ? hasModel
              ? "Model available"
              : "Ready to analyse"
            : "Waiting for a recording"}
        </span>
      </div>
      {stages.map((s, i) => {
        const a = ((i * 45 - 90) * Math.PI) / 180;
        return (
          <button
            key={s}
            className={"stage stage-" + i}
            style={{
              left: `${50 + 43 * Math.cos(a)}%`,
              top: `${50 + 43 * Math.sin(a)}%`,
            }}
            onClick={() => navigate(stagePages[i])}
            title={`${s} · ${i < 5 ? (hasData ? "Recording available" : "Needs a recording") : hasModel ? "Model available" : "Explore lab"}`}
          >
            <span>{String(i + 1).padStart(2, "0")}</span>
            <b>{s}</b>
          </button>
        );
      })}
      <span className="ring-caption">
        ONE SIGNAL. EIGHT STEPS. A CLEARER PICTURE.
      </span>
    </div>
  );
}
function App() {
  const [page, setPage] = useState<Page>(
    () =>
      ((location.hash.slice(2) === "soft"
        ? "learning"
        : location.hash.slice(2)) as Page) || "intro",
  );
  const [state, setState] = useState<Dict>({
    captures: [],
    datasets: [],
    models: [],
    runs: [],
    jobs: [],
  });
  const [evidence, setEvidence] = useState<Dict>({});
  const [online, setOnline] = useState(false);
  const [authed, setAuthed] = useState(false);
  const [checkedAuth, setCheckedAuth] = useState(false);
  const [authOpen, setAuthOpen] = useState(false);
  const [code, setCode] = useState("");
  const [authError, setAuthError] = useState("");
  const [busy, setBusy] = useState(false);
  const [selected, setSelected] = useState(
    localStorage.getItem("orbit-capture") || "",
  );
  const [mode, setMode] = useState(localStorage.getItem("orbit-mode") || "ax");
  const [theme, setTheme] = useState(
    localStorage.getItem("orbit-theme") || "light",
  );
  const [quiet, setQuiet] = useState(
    localStorage.getItem("orbit-quiet") !== "false",
  );
  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("orbit-theme", theme);
    window.dispatchEvent(new Event("orbit-theme"));
  }, [theme]);
  useEffect(() => {
    document.documentElement.dataset.quiet = String(quiet);
    localStorage.setItem("orbit-quiet", String(quiet));
  }, [quiet]);
  useEffect(() => {
    localStorage.setItem("orbit-mode", mode);
  }, [mode]);
  const [toast, setToast] = useState("");
  const [mobileMenu, setMobileMenu] = useState(false);
  const [confirmDelete, setConfirmDelete] = useState("");
  const [small, setSmall] = useState(matchMedia("(max-width:800px)").matches);
  useEffect(() => {
    const mq = matchMedia("(max-width:800px)");
    const listener = () => setSmall(mq.matches);
    mq.addEventListener("change", listener);
    return () => mq.removeEventListener("change", listener);
  }, []);
  useEffect(() => {
    if (!authOpen && !confirmDelete) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setAuthOpen(false);
        setConfirmDelete("");
        if (authOpen) {
          location.hash = "/intro";
          setPage("intro");
        }
      }
      if (e.key === "Tab") {
        const modal = document.querySelector("[role=dialog]");
        const items = Array.from(
          modal?.querySelectorAll<HTMLElement>(
            "button:not([disabled]),input,select,a[href]",
          ) || [],
        );
        if (!items.length) return;
        const first = items[0],
          last = items[items.length - 1];
        if (e.shiftKey && document.activeElement === first) {
          e.preventDefault();
          last.focus();
        } else if (!e.shiftKey && document.activeElement === last) {
          e.preventDefault();
          first.focus();
        }
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [authOpen, confirmDelete]);
  const capture = state.captures.find((c: Dict) => c.id === selected);
  const job = state.jobs.find((j: Dict) =>
    ["queued", "running"].includes(j.status),
  );
  const notify = (message: string) => {
    if (
      localStorage.getItem("orbit-quiet") !== "false" &&
      !/error|failed|incorrect|mismatch|outside|cannot|not match|needs|requires|invalid/i.test(
        message,
      )
    )
      return;
    setToast(message);
    window.setTimeout(() => setToast(""), 6500);
  };
  const refresh = async () => {
    try {
      const s = await api("status");
      setState(s);
      setSelected((current) => {
        if (s.captures.some((c: Dict) => c.id === current)) return current;
        const first =
          s.captures.find((c: Dict) => c.bandwidth === 20 && c.windows > 0) ||
          s.captures[0];
        if (first) {
          localStorage.setItem("orbit-capture", first.id);
          return first.id;
        }
        return "";
      });
      setOnline(true);
      setAuthed(true);
      setAuthOpen(false);
      setEvidence(await api("evidence"));
    } catch {
      setAuthed(false);
    } finally {
      setCheckedAuth(true);
    }
  };
  useEffect(() => {
    api("health")
      .then(() => setOnline(true))
      .catch(() => setOnline(false));
    refresh();
    const id = setInterval(refresh, 4000);
    return () => clearInterval(id);
  }, []);
  useEffect(() => {
    const fn = () =>
      setPage(
        ((location.hash.slice(2) === "soft"
          ? "learning"
          : location.hash.slice(2)) as Page) || "intro",
      );
    window.addEventListener("hashchange", fn);
    return () => window.removeEventListener("hashchange", fn);
  }, []);
  useEffect(() => {
    if (page !== "intro" && !authed && online && checkedAuth) setAuthOpen(true);
  }, [page, authed, online, checkedAuth]);
  const navigate = (p: Page) => {
    location.hash = "/" + p;
    setPage(p);
    setMobileMenu(false);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };
  const choose = (id: string) => {
    setSelected(id);
    localStorage.setItem("orbit-capture", id);
  };
  const authenticate = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true);
    try {
      await api("auth", { code });
      await refresh();
      setAuthOpen(false);
      setAuthError("");
    } catch (e: any) {
      setAuthError(e.message);
    } finally {
      setBusy(false);
    }
  };
  const common = {
    state,
    capture,
    selected,
    choose,
    navigate,
    notify,
    refresh,
    job,
  };
  const mainPage = nav.find((n) => n.id === page);
  const activeTitle =
    page === "upload" ? "Phone upload" : mainPage?.label || "Overview";
  return (
    <>
      {page === "intro" ? (
        <div className="intro">
          <header className="intro-nav">
            <button className="brand" onClick={() => navigate("intro")}>
              <Mark />
              <span>
                orbit<small>Wi-Fi Sensing Lab</small>
              </span>
            </button>
            <nav>
              <button onClick={() => navigate("results")}>The research</button>
              <button onClick={() => navigate("modes")}>Capabilities</button>
              <Button secondary onClick={() => navigate("overview")}>
                Open workspace <ArrowRight size={16} />
              </Button>
            </nav>
          </header>
          <main className="intro-main">
            <div className="intro-hero">
              <div className="intro-copy">
                <Badge>
                  <span className="status-dot" /> LOCAL-FIRST RESEARCH WORKSPACE
                </Badge>
                <h1>
                  See the signal.
                  <br />
                  <span>
                    Understand
                    <br />
                    the decision.
                  </span>
                </h1>
                <p>
                  A clearer way to explore Wi-Fi sensing. Bring your CSI
                  recordings, shape the signal, and put every result under the
                  microscope.
                </p>
                <div className="button-row">
                  <Button onClick={() => navigate("overview")}>
                    Open workspace <ArrowRight size={18} />
                  </Button>
                  <button
                    className="text-button"
                    onClick={() => navigate("data")}
                  >
                    <Upload size={17} /> Bring a recording
                  </button>
                </div>
                <div className="intro-trust">
                  <ShieldCheck size={16} />
                  <span>Your recordings. Your laptop. Your research.</span>
                </div>
              </div>
              <div className="intro-orbit">
                <div className="visual-tag top">
                  <CircleDot size={14} /> FROM SIGNAL TO UNDERSTANDING
                </div>
                <Ring navigate={navigate} />
                <div className="visual-tag bottom">
                  <LockKeyhole size={13} /> Local processing <span /> Recorded
                  CSI
                </div>
              </div>
            </div>
            <div className="capability-grid">
              {[
                {
                  n: "01",
                  icon: Upload,
                  title: "Bring in your data",
                  text: "MATLAB captures. One local library.",
                  p: "data",
                },
                {
                  n: "02",
                  icon: AudioLines,
                  title: "Find the signal",
                  text: "Windows, filters, spectra. Made tangible.",
                  p: "dsp",
                },
                {
                  n: "03",
                  icon: BrainCircuit,
                  title: "Explore the decision",
                  text: "Learning models and transparent rules.",
                  p: "learning",
                },
                {
                  n: "04",
                  icon: FlaskConical,
                  title: "Follow the evidence",
                  text: "Real metrics. Context included.",
                  p: "results",
                },
              ].map((c) => (
                <button
                  className="capability"
                  key={c.n}
                  onClick={() => navigate(c.p as Page)}
                >
                  <span className="cap-number">{c.n}</span>
                  <c.icon size={23} />
                  <h3>{c.title}</h3>
                  <p>{c.text}</p>
                  <ArrowRight className="cap-arrow" size={17} />
                </button>
              ))}
            </div>
            <section className="research-strip">
              <div>
                <span className="tiny-label">THE RESEARCH SO FAR</span>
                <p>
                  Recorded experiments.
                  <br />
                  Room to discover more.
                </p>
              </div>
              <div>
                <strong>
                  15 <small>captures</small>
                </strong>
                <span>20 MHz · two recording dates</span>
              </div>
              <div>
                <strong>
                  3 <small>learning models</small>
                </strong>
                <span>LR · Random Forest · ANN</span>
              </div>
              <div>
                <strong>AX + BF</strong>
                <span>Simulator evidence, clearly labelled</span>
              </div>
              <button
                className="round-btn"
                onClick={() => navigate("results")}
                aria-label="Explore evidence"
              >
                <ArrowRight />
              </button>
            </section>
          </main>
          <footer className="intro-footer">
            <span>ORBIT / WI-FI SENSING LAB</span>
            <span>Built for curiosity. Grounded in evidence.</span>
            <button onClick={() => navigate("modes")}>
              Research status <ArrowUpRight />
            </button>
          </footer>
        </div>
      ) : (
        <div className="app-shell">
          {mobileMenu && (
            <button
              className="nav-scrim"
              aria-label="Close navigation"
              onClick={() => setMobileMenu(false)}
            />
          )}
          <aside
            inert={small && !mobileMenu}
            className={"sidebar " + (mobileMenu ? "open" : "")}
          >
            <button className="brand" onClick={() => navigate("intro")}>
              <Mark />
              <span>
                orbit<small>Wi-Fi Sensing Lab</small>
              </span>
            </button>
            <div className="sidebar-label">WORKSPACE</div>
            <nav>
              {nav.map((n, i) => (
                <React.Fragment key={n.id}>
                  {i === 6 && <div className="nav-divider" />}
                  <button
                    onClick={() => navigate(n.id as Page)}
                    className={page === n.id ? "active" : ""}
                  >
                    <n.icon size={19} />
                    <span>{n.label}</span>
                    {n.id === "dsp" && <i className="nav-dot orange" />}
                    {n.id === "learning" && <i className="nav-dot violet" />}
                  </button>
                </React.Fragment>
              ))}
            </nav>
            <div className="sidebar-bottom">
              <div className="local-card">
                <span className="local-icon">
                  <ShieldCheck size={19} />
                </span>
                <div>
                  <strong>A lab of your own</strong>
                  <span>Everything stays local.</span>
                </div>
              </div>
              <button className="profile" onClick={() => navigate("settings")}>
                <span className="avatar">O</span>
                <span>
                  Local workspace
                  <small>
                    {online ? "Server connected" : "Server offline"}
                  </small>
                </span>
                <Settings2 size={16} />
              </button>
            </div>
          </aside>
          <div className="workspace">
            <header className="topbar">
              <div className="breadcrumb">
                <button
                  className="mobile-toggle icon-btn"
                  onClick={() => setMobileMenu(!mobileMenu)}
                  aria-label="Toggle navigation"
                >
                  <Menu size={21} />
                </button>
                <span>Workspace</span>
                <ChevronRight size={13} />
                <strong>{activeTitle}</strong>
              </div>
              <div className="top-actions">
                <select
                  className="theme-picker"
                  aria-label="Colour theme"
                  value={theme}
                  onChange={(e) => setTheme(e.target.value)}
                >
                  <option value="light">Google Light</option>
                  <option value="soft">Soft Sage</option>
                  <option value="midnight">Orbit Midnight</option>
                  <option value="charcoal">Classic Dark</option>
                </select>
                <button
                  className={"presentation-toggle " + (quiet ? "enabled" : "")}
                  aria-label="Toggle presentation mode"
                  aria-pressed={quiet}
                  onClick={() => setQuiet(!quiet)}
                >
                  {quiet ? "Presentation" : "Detailed"}
                </button>
                <span className={"server-state " + (!online ? "offline" : "")}>
                  <i />
                  {online ? "Local server online" : "Server offline"}
                </span>
                <button
                  className="icon-btn"
                  onClick={() => navigate("settings")}
                  aria-label="Phone connection"
                >
                  <Smartphone size={18} />
                </button>
                <button
                  className="icon-btn"
                  onClick={() => navigate("modes")}
                  aria-label="Research help"
                >
                  <CircleHelp size={18} />
                </button>
              </div>
            </header>
            <main className="workspace-main">
              <div className="page-heading">
                <div>
                  <span className="eyebrow">
                    ORBIT /{" "}
                    {page === "dsp"
                      ? "DIGITAL SIGNAL PROCESSING"
                      : page === "learning"
                        ? "LEARNING LAB"
                        : "WI-FI SENSING LAB"}
                  </span>
                  <h1>
                    {page === "media"
                      ? "Recordings, photos & experiment videos."
                      : page === "overview"
                        ? "Your signal. Your workspace."
                        : page === "dsp"
                          ? "Make sense of the signal."
                          : page === "learning"
                            ? "Inside the decision."
                            : page === "results"
                              ? "Evidence, in perspective."
                              : page === "data"
                                ? "Every recording starts here."
                                : page === "replay"
                                  ? "From recording to decision."
                                  : page === "modes"
                                    ? "Know what’s possible."
                                    : page === "upload"
                                      ? "Send it to your laptop."
                                      : "Your local lab, connected."}
                  </h1>
                  <p>
                    {page === "overview"
                      ? "A complete path from recorded CSI to a decision you can inspect."
                      : page === "data"
                        ? "Import, inspect, and keep your recordings organised in one local library."
                        : page === "dsp"
                          ? "Follow the waveform. Change one thing. See what happens."
                          : page === "learning"
                            ? "Train a model, explore a rule, and examine the evidence behind the output."
                            : page === "replay"
                              ? "Step through recorded packets. Run a compatible model when one is available."
                              : page === "results"
                                ? "Historical research and your local experiments, with their methods attached."
                                : page === "modes"
                                  ? "Three sensing directions. Each with a clear, honest readiness status."
                                  : "Local processing. Shared access across your trusted network."}
                  </p>
                </div>
                {page === "overview" && (
                  <Button onClick={() => navigate("data")}>
                    <Plus size={17} /> Add recording
                  </Button>
                )}
              </div>
              {mode !== "ax" && (
                <Note>
                  {mode === "bf"
                    ? "802.11bf mode shows simulator research. Recording analysis still uses its actual CSI source; physical BF capture is unverified."
                    : "Adaptive mode is a proposed architecture. No automatic hardware selection or sensing switch is active."}
                </Note>
              )}
              {job && (
                <div className="job-banner">
                  <LoaderCircle className="spin" size={18} />
                  <span>{job.message}</span>
                  <progress value={job.progress} max={100} />
                  <b>{job.progress}%</b>
                </div>
              )}
              {!online && (
                <Note tone="red">
                  The local analysis server is offline. Start Orbit using{" "}
                  <code>python -m orbit</code>, then reload this page.
                </Note>
              )}
              {page === "overview" && (
                <>
                  <div className="mode-toolbar">
                    <div className="mode-switch">
                      {[
                        ["ax", "Wi-Fi 6", "802.11ax CSI"],
                        ["bf", "802.11bf", "Simulator"],
                        ["adaptive", "Adaptive", "Planned"],
                      ].map(([id, label, sub]) => (
                        <button
                          key={id}
                          className={mode === id ? "selected" : ""}
                          onClick={() => setMode(id)}
                        >
                          {id === "ax" ? (
                            <Wifi size={16} />
                          ) : id === "bf" ? (
                            <Radio size={16} />
                          ) : (
                            <GitBranch size={16} />
                          )}
                          <span>
                            {label}
                            <small>{sub}</small>
                          </span>
                          {mode === id && <Check size={15} />}
                        </button>
                      ))}
                    </div>
                    <span className="source-state">
                      <span className="status-dot" />
                      {capture ? "Recorded data" : "No input source"}
                    </span>
                  </div>
                  <div className="overview-grid">
                    <section className="panel input-panel">
                      <div className="panel-label">
                        <span>01 / INPUT</span>
                        <Upload size={17} />
                      </div>
                      <h2>Bring in a signal.</h2>
                      <p>
                        Your next discovery starts
                        <br />
                        with a recording.
                      </p>
                      <button
                        className="upload-tile"
                        onClick={() => navigate("data")}
                      >
                        <span className="upload-circle">
                          <Plus size={24} />
                        </span>
                        <strong>
                          {capture
                            ? "Add another recording"
                            : "Upload a recording"}
                        </strong>
                        <span>.mat or .zip · up to 2 GiB</span>
                        <b>
                          Browse files <ArrowRight size={14} />
                        </b>
                      </button>
                      <div className="small-divider" />
                      <button
                        className="subtle-action"
                        onClick={() => navigate("settings")}
                      >
                        <Smartphone size={18} />
                        <span>
                          Send from your phone
                          <small>On the same Wi-Fi network</small>
                        </span>
                        <ChevronRight size={16} />
                      </button>
                      <div className="input-footer">
                        <LockKeyhole size={12} /> Processed and stored on this
                        laptop
                      </div>
                    </section>
                    <section className="hub-panel">
                      <div className="hub-header">
                        <span className="tiny-label">THE SIGNAL PATH</span>
                        <Badge tone={capture ? "green" : "muted"}>
                          {capture ? "RECORDED DATA" : "AWAITING INPUT"}
                        </Badge>
                      </div>
                      <Ring
                        navigate={navigate}
                        hasData={!!capture}
                        hasModel={state.models.length > 0}
                      />
                    </section>
                    <section className="panel session-panel">
                      <div className="panel-label">
                        <span>THIS SESSION</span>
                        <CircleDot size={16} />
                      </div>
                      <h2>A little context.</h2>
                      <div className="session-row">
                        <span>Recording</span>
                        <strong>
                          {capture
                            ? capture.name.split("/").pop()
                            : "None selected"}
                        </strong>
                      </div>
                      <div className="session-row">
                        <span>Model</span>
                        <strong>
                          {state.models.length
                            ? state.models[0].name
                            : "Training needed"}
                        </strong>
                      </div>
                      <div className="session-row">
                        <span>Presence</span>
                        <strong className="muted">
                          {capture
                            ? "Run a compatible model"
                            : "Waiting for data"}
                        </strong>
                      </div>
                      <div className="small-divider" />
                      <span className="tiny-label">START WITH A QUESTION</span>
                      {[
                        ["Inspect a recording", "data"],
                        ["Explore signal processing", "dsp"],
                        ["Review research results", "results"],
                      ].map(([l, p], i) => (
                        <button
                          className="quick-step"
                          key={p}
                          onClick={() => navigate(p as Page)}
                        >
                          <span>{i + 1}</span>
                          <b>{l}</b>
                          <ChevronRight size={14} />
                        </button>
                      ))}
                    </section>
                  </div>
                  <div className="section-heading">
                    <h2>Pick a direction.</h2>
                    <span>Tools for the curious.</span>
                  </div>
                  <div className="destination-grid">
                    {[
                      {
                        p: "dsp",
                        icon: AudioLines,
                        color: "orange",
                        title: "Signal Studio",
                        text: "Get closer to the waveform.",
                        tags: "WINDOW · FILTER · SPECTRUM",
                      },
                      {
                        p: "learning",
                        icon: BrainCircuit,
                        color: "violet",
                        title: "Learning Lab",
                        text: "Look inside the learning process.",
                        tags: "ANN · GENETIC ALGORITHMS · FUZZY",
                      },
                      {
                        p: "replay",
                        icon: Play,
                        color: "cyan",
                        title: "Detect & replay",
                        text: "A recording, one window at a time.",
                        tags: "OFFLINE REPLAY · MODEL OUTPUT",
                      },
                    ].map((c) => (
                      <button
                        className={"destination " + c.color}
                        key={c.p}
                        onClick={() => navigate(c.p as Page)}
                      >
                        <div className="destination-top">
                          <span>
                            <c.icon size={23} />
                          </span>
                          <ArrowRight size={18} />
                        </div>
                        <h3>{c.title}</h3>
                        <p>{c.text}</p>
                        <small>{c.tags}</small>
                      </button>
                    ))}
                  </div>
                  <section className="evidence-preview">
                    <div>
                      <FlaskConical size={21} />
                      <div>
                        <h3>Good research keeps the context.</h3>
                        <p>
                          15 captures at 20 MHz · two dates · three models.
                          Explore the results and their limits.
                        </p>
                      </div>
                    </div>
                    <button
                      className="text-button"
                      onClick={() => navigate("results")}
                    >
                      View the evidence <ArrowRight size={17} />
                    </button>
                  </section>
                  {state.runs.length > 0 && (
                    <section className="panel">
                      <div className="section-heading">
                        <h2>Recent experiments</h2>
                        <span>Saved on this laptop</span>
                      </div>
                      {state.runs.slice(0, 4).map((r: Dict) => (
                        <div className="history-row" key={r.id}>
                          <Activity size={17} />
                          <strong>
                            {r.kind === "DSP" ? r.settings.operation : r.kind}
                          </strong>
                          <Badge tone="muted">{r.source}</Badge>
                          <span>{new Date(r.created).toLocaleString()}</span>
                          <a
                            href={"/api/export/run/" + r.id}
                            className="icon-btn"
                            aria-label="Export run"
                          >
                            <Download size={16} />
                          </a>
                        </div>
                      ))}
                    </section>
                  )}
                </>
              )}
              {(page === "data" || page === "upload") && (
                <DataPage
                  {...common}
                  phone={page === "upload"}
                  onDelete={setConfirmDelete}
                />
              )}
              {page === "dsp" && <DSPPage {...common} />}
              {page === "learning" && <LearningPage {...common} />}
              {page === "media" && <MediaPage {...common} />}
              {page === "replay" && <ReplayPage {...common} />}
              {page === "results" && (
                <ResultsPage {...common} evidence={evidence} />
              )}
              {page === "modes" && (
                <ModesPage navigate={navigate} evidence={evidence} />
              )}
              {page === "settings" && (
                <SettingsPage
                  notify={notify}
                  logout={async () => {
                    await api("logout", {});
                    setAuthed(false);
                    navigate("intro");
                  }}
                />
              )}
              <footer className="workspace-footer">
                <span>
                  <ShieldCheck size={13} /> Local-first. Evidence-led.
                </span>
                <span>
                  Orbit v1.1 <i /> Live hardware remains unverified.
                </span>
              </footer>
            </main>
          </div>
          <nav className="mobile-bottom">
            {nav
              .filter((n) =>
                ["overview", "data", "dsp", "learning", "replay"].includes(
                  n.id,
                ),
              )
              .map((n) => (
                <button
                  key={n.id}
                  className={page === n.id ? "active" : ""}
                  onClick={() => navigate(n.id as Page)}
                >
                  <n.icon size={18} />
                  <span>{n.label.split(" ")[0]}</span>
                </button>
              ))}
            <button onClick={() => setMobileMenu(!mobileMenu)}>
              <Menu size={18} />
              <span>More</span>
            </button>
          </nav>
        </div>
      )}
      {authOpen && (
        <div className="modal-backdrop">
          <form
            role="dialog"
            aria-modal="true"
            aria-label="Connect to local workspace"
            className="modal auth-modal"
            onSubmit={authenticate}
          >
            <button
              className="modal-close icon-btn"
              type="button"
              onClick={() => {
                setAuthOpen(false);
                navigate("intro");
              }}
              aria-label="Close"
            >
              <X size={20} />
            </button>
            <Mark />
            <Badge tone="green">PRIVATE LOCAL WORKSPACE</Badge>
            <h2>
              Your lab.
              <br />
              One simple connection.
            </h2>
            <p>
              Enter the access code printed in your laptop’s Orbit terminal.
              Your phone uses the same code.
            </p>
            <label>
              Session access code
              <input
                autoFocus
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Access code"
                autoComplete="off"
                maxLength={100}
                required
              />
            </label>
            {authError && <Note tone="red">{authError}</Note>}
            <Button type="submit" disabled={busy || !code}>
              {busy ? (
                <LoaderCircle className="spin" size={17} />
              ) : (
                <LockKeyhole size={17} />
              )}{" "}
              Connect to workspace
            </Button>
            <small>The code changes each time the server starts.</small>
          </form>
        </div>
      )}
      {confirmDelete && (
        <div className="modal-backdrop">
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Remove dataset confirmation"
            className="modal"
          >
            <h2>Remove this dataset?</h2>
            <p>
              The uploaded original, cached signals, and captures will be
              removed from this laptop. Saved model provenance remains
              available.
            </p>
            <div className="button-row">
              <Button secondary onClick={() => setConfirmDelete("")}>
                Keep dataset
              </Button>
              <Button
                onClick={async () => {
                  try {
                    await api("datasets/" + confirmDelete, undefined, "DELETE");
                    setConfirmDelete("");
                    await refresh();
                    notify("Dataset removed.");
                  } catch (e: any) {
                    notify(e.message);
                  }
                }}
              >
                Remove dataset
              </Button>
            </div>
          </div>
        </div>
      )}
      {toast && (
        <div className="toast" role="status">
          <Info size={17} />
          {toast}
          <button
            className="icon-btn"
            onClick={() => setToast("")}
            aria-label="Dismiss"
          >
            <X size={15} />
          </button>
        </div>
      )}
    </>
  );
}
function ArrowUpRight() {
  return <ExternalLink size={13} />;
}
type Common = {
  state: Dict;
  capture: any;
  selected: string;
  choose: (id: string) => void;
  navigate: (p: Page) => void;
  notify: (s: string) => void;
  refresh: () => Promise<void>;
  job: any;
};
function CaptureSelect({
  state,
  selected,
  choose,
}: {
  state: Dict;
  selected: string;
  choose: (id: string) => void;
}) {
  const active = state.captures.find((c: Dict) => c.id === selected);
  const [dataset, setDataset] = useState(active?.dataset_id || "");
  useEffect(() => {
    if (active) setDataset(active.dataset_id);
  }, [selected]);
  const captures = state.captures.filter(
    (c: Dict) => !dataset || c.dataset_id === dataset,
  );
  return (
    <div className="saved-source-picker">
      <label>
        Saved dataset
        <select
          value={dataset}
          onChange={(e) => {
            setDataset(e.target.value);
            const first = state.captures.find(
              (c: Dict) => c.dataset_id === e.target.value && c.windows > 0,
            );
            if (first) choose(first.id);
          }}
        >
          <option value="">All saved datasets</option>
          {state.datasets.map((d: Dict) => (
            <option key={d.id} value={d.id}>
              {d.name} · {d.captures} captures
            </option>
          ))}
        </select>
      </label>
      <label className="capture-select">
        Capture
        <select value={selected} onChange={(e) => choose(e.target.value)}>
          <option value="">Select a saved capture</option>
          {captures.map((c: Dict) => (
            <option key={c.id} value={c.id}>
              {c.name.replaceAll("\\", "/")} ·{" "}
              {c.present === null
                ? "Unlabelled"
                : c.present
                  ? "Person present"
                  : "No person"}
            </option>
          ))}
        </select>
      </label>
    </div>
  );
}

function DataPage({
  state,
  capture,
  selected,
  choose,
  navigate,
  notify,
  refresh,
  job,
  phone,
  onDelete,
}: Common & { phone: boolean; onDelete: (s: string) => void }) {
  const [matProfile, setMatProfile] = useState("inspect");
  const [matLabel, setMatLabel] = useState("unlabelled");
  const [dataTab, setDataTab] = useState(phone ? "new" : "saved");
  const [datasetFilter, setDatasetFilter] = useState("");
  const input = useRef<HTMLInputElement>(null);
  const [drag, setDrag] = useState(false);
  const [progress, setProgress] = useState(-1);
  const [uploadError, setUploadError] = useState("");
  const xhr = useRef<XMLHttpRequest | null>(null);
  const [search, setSearch] = useState("");
  const [bw, setBw] = useState("all");
  const [label, setLabel] = useState("all");
  const [view, setView] = useState<Dict | null>(null);
  const [sub, setSub] = useState(-1);
  const [start, setStart] = useState(0);
  useEffect(() => {
    if (!capture) {
      setView(null);
      return;
    }
    api(`captures/${capture.id}?start=${start}&subcarrier=${sub}`)
      .then(setView)
      .catch((e) => notify(e.message));
  }, [capture?.id, sub, start]);
  useEffect(() => {
    setStart(0);
    setSub(-1);
  }, [capture?.id]);
  const upload = (file?: File) => {
    if (!file) return;
    setUploadError("");
    if (!/\.(mat|zip)$/i.test(file.name)) {
      setUploadError("Choose a MATLAB .mat recording or a .zip dataset.");
      return;
    }
    if (file.size > 2 * 1024 ** 3) {
      setUploadError("The upload limit is 2 GiB.");
      return;
    }
    const form = new FormData();
    form.append("file", file);
    form.append("profile", matProfile);
    form.append("label", matLabel);
    const r = new XMLHttpRequest();
    xhr.current = r;
    r.open("POST", "/api/upload");
    r.upload.onprogress = (e) => {
      if (e.lengthComputable)
        setProgress(Math.round((e.loaded / e.total) * 100));
    };
    r.onload = () => {
      setProgress(-1);
      if (r.status >= 200 && r.status < 300) {
        refresh();
        notify("Upload received. The laptop is validating your recordings.");
      } else {
        try {
          setUploadError(JSON.parse(r.responseText).detail);
        } catch {
          setUploadError("Upload failed. Check the server connection.");
        }
      }
    };
    r.onerror = () => {
      setProgress(-1);
      setUploadError(
        "Connection interrupted. Check the local server and retry.",
      );
    };
    r.onabort = () => setProgress(-1);
    setProgress(0);
    r.send(form);
  };
  const filtered = state.captures.filter(
    (c: Dict) =>
      (!datasetFilter || c.dataset_id === datasetFilter) &&
      c.name.toLowerCase().includes(search.toLowerCase()) &&
      (bw === "all" || String(c.bandwidth) === bw) &&
      (label === "all" || String(c.present) === label),
  );
  return (
    <>
      <div className="tabs">
        <button
          aria-label="Use saved dataset"
          className={dataTab === "saved" ? "active" : ""}
          onClick={() => setDataTab("saved")}
        >
          <Database size={15} /> Saved datasets
        </button>
        <button
          aria-label="Drop new data"
          className={dataTab === "new" ? "active" : ""}
          onClick={() => setDataTab("new")}
        >
          <Upload size={15} /> New data
        </button>
        <button onClick={() => navigate("media")}>
          <FolderOpen size={15} /> Photos & videos
        </button>
      </div>
      {dataTab === "saved" && (
        <div className="saved-dataset-grid">
          {state.datasets.map((d: Dict) => {
            const caps = state.captures.filter(
              (c: Dict) => c.dataset_id === d.id,
            );
            return (
              <section
                className={
                  "panel saved-dataset " +
                  (datasetFilter === d.id ? "chosen" : "")
                }
                key={d.id}
              >
                <div className="panel-heading">
                  <Database size={25} />
                  <Badge tone="green">SAVED LOCALLY</Badge>
                </div>
                <h2>{d.name}</h2>
                <p>
                  {caps.length} captures ·{" "}
                  {caps
                    .reduce((n: number, c: Dict) => n + c.windows, 0)
                    .toLocaleString()}{" "}
                  accepted windows
                </p>
                <div className="dataset-chips">
                  <span>
                    {caps.filter((c: Dict) => c.present === true).length}{" "}
                    presence
                  </span>
                  <span>
                    {caps.filter((c: Dict) => c.present === false).length}{" "}
                    absence
                  </span>
                  <span>{(d.size / 1024 ** 2).toFixed(0)} MiB</span>
                </div>
                <div className="button-row">
                  <Button
                    onClick={() => {
                      setDatasetFilter(d.id);
                      const c = caps.find((c: Dict) => c.windows > 0);
                      if (c) choose(c.id);
                    }}
                  >
                    Select dataset <Check size={15} />
                  </Button>
                  <Button
                    secondary
                    onClick={() => {
                      const c = caps.find((c: Dict) => c.windows > 0);
                      if (c) choose(c.id);
                      navigate("replay");
                    }}
                  >
                    Run recording <Play size={15} />
                  </Button>
                </div>
              </section>
            );
          })}
          {!state.datasets.length && (
            <section className="panel">
              <Empty
                icon={Database}
                title="Your saved datasets appear here."
                action={
                  <Button onClick={() => setDataTab("new")}>
                    Drop new data
                  </Button>
                }
              >
                Import a dataset once; it remains available after restarting
                Orbit.
              </Empty>
            </section>
          )}
        </div>
      )}
      {dataTab === "new" && (
        <div className="two-column data-top">
          <section className="panel">
            <div className="panel-heading">
              <div>
                <Badge tone="cyan">LOCAL UPLOAD</Badge>
                <h2>
                  {phone ? "From phone to laptop." : "Bring your recordings."}
                </h2>
              </div>
              <Upload size={24} />
            </div>
            <div className="mat-profile">
              <label>
                Single MAT profile
                <select
                  value={matProfile}
                  onChange={(e) => setMatProfile(e.target.value)}
                >
                  <option value="inspect">
                    Inspect only · metadata unknown
                  </option>
                  <option value="ax20">Wi-Fi 6 AX · 20 MHz</option>
                  <option value="ax40">Wi-Fi 6 AX · 40 MHz</option>
                </select>
              </label>
              <label>
                Known label (optional)
                <select
                  value={matLabel}
                  onChange={(e) => setMatLabel(e.target.value)}
                >
                  <option value="unlabelled">
                    Unlabelled · inference only
                  </option>
                  <option value="true">Person present</option>
                  <option value="false">No person</option>
                </select>
              </label>
              <small>
                For single MAT files, choose the actual capture profile. ZIP
                imports use their own config.json.
              </small>
            </div>
            <div
              className={"dropzone " + (drag ? "drag" : "")}
              onDragOver={(e) => {
                e.preventDefault();
                setDrag(true);
              }}
              onDragLeave={() => setDrag(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDrag(false);
                if (progress < 0 && !job) upload(e.dataTransfer.files[0]);
              }}
            >
              <input
                ref={input}
                type="file"
                accept=".mat,.zip"
                hidden
                onChange={(e) => {
                  upload(e.target.files?.[0]);
                  e.target.value = "";
                }}
              />
              <div className="upload-circle">
                <FileUp size={26} />
              </div>
              <h3>
                {progress >= 0
                  ? "Sending to your laptop…"
                  : "Drop a recording here"}
              </h3>
              <p>MATLAB v7.3 / HDF5 or a dataset ZIP with config.json</p>
              {progress >= 0 ? (
                <>
                  <progress max={100} value={progress} />
                  <span>{progress}% transferred</span>
                  <Button secondary onClick={() => xhr.current?.abort()}>
                    Cancel upload
                  </Button>
                </>
              ) : (
                <Button
                  secondary
                  disabled={!!job}
                  onClick={() => input.current?.click()}
                >
                  Browse files <ArrowRight size={16} />
                </Button>
              )}
              <small>Up to 2 GiB · private local storage</small>
            </div>
            {uploadError && <Note tone="red">{uploadError}</Note>}
            {state.jobs
              .filter((j: Dict) => j.kind === "import" && j.status === "failed")
              .slice(0, 1)
              .map((j: Dict) => (
                <Note key={j.id} tone="red">
                  Import failed: {j.message}
                </Note>
              ))}
          </section>
          <section className="panel">
            <span className="eyebrow">GOOD DATA. CLEAR CONTEXT.</span>
            <h2>What Orbit reads.</h2>
            <ul className="check-list">
              <li>
                <Check size={16} /> Complex CSI in the HDF5 <code>capture</code>{" "}
                dataset
              </li>
              <li>
                <Check size={16} /> 256 or 512 subcarriers, with orientation
                checks
              </li>
              <li>
                <Check size={16} /> Labels, dates, modulation and bandwidth from
                config.json
              </li>
              <li>
                <Check size={16} /> Invalid columns and accepted/rejected
                feature windows
              </li>
            </ul>
            <Note>
              Single .mat uploads can be inspected. For training, import a ZIP
              containing captures and their config.json files with verified AX
              modulation, bandwidth and presence labels.
            </Note>
            <button
              className="subtle-action"
              onClick={() => navigate("settings")}
            >
              <Smartphone size={20} />
              <span>
                Uploading from a phone?
                <small>Get your laptop’s LAN address and QR code.</small>
              </span>
              <ArrowRight size={17} />
            </button>
          </section>
        </div>
      )}
      {state.references?.length > 0 && (
        <section className="panel reference-shelf">
          <span className="tiny-label">PROJECT REFERENCE FILES</span>
          {state.references.map((r: Dict) => (
            <a
              key={r.id}
              className="reference-download"
              href={"/api/references/" + r.id + "/file"}
            >
              <BookOpen size={17} />
              {r.name}
              <Download size={15} />
            </a>
          ))}
        </section>
      )}
      <div className="section-heading">
        <h2>
          Recording library{" "}
          <span className="count">{state.captures.length}</span>
        </h2>
        <span>Persistent library · available on laptop and phone</span>
      </div>
      <div className="filter-bar">
        <select
          aria-label="Saved dataset filter"
          value={datasetFilter}
          onChange={(e) => setDatasetFilter(e.target.value)}
        >
          <option value="">All saved datasets</option>
          {state.datasets.map((d: Dict) => (
            <option key={d.id} value={d.id}>
              {d.name}
            </option>
          ))}
        </select>
        <div className="search-field">
          <Search size={17} />
          <input
            placeholder="Find a recording…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          aria-label="Filter bandwidth"
          value={bw}
          onChange={(e) => setBw(e.target.value)}
        >
          <option value="all">All bandwidths</option>
          <option value="20">20 MHz</option>
          <option value="40">40 MHz</option>
        </select>
        <select
          aria-label="Filter label"
          value={label}
          onChange={(e) => setLabel(e.target.value)}
        >
          <option value="all">All labels</option>
          <option value="true">Person present</option>
          <option value="false">No person</option>
          <option value="null">Unlabelled</option>
        </select>
      </div>
      <section className="panel table-panel">
        {filtered.length ? (
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  <th>Recording</th>
                  <th>Bandwidth</th>
                  <th>Packets</th>
                  <th>Valid</th>
                  <th>Label</th>
                  <th>Windows</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {filtered.map((c: Dict) => (
                  <tr
                    key={c.id}
                    className={selected === c.id ? "selected-row" : ""}
                  >
                    <td>
                      <button
                        className="table-link"
                        onClick={() => choose(c.id)}
                      >
                        <span className="file-icon">
                          <AudioLines size={17} />
                        </span>
                        <span>
                          {c.name.split("/").pop()}
                          <small>
                            {c.date} · {c.name}
                          </small>
                        </span>
                      </button>
                    </td>
                    <td>{c.bandwidth} MHz</td>
                    <td>{c.packets.toLocaleString()}</td>
                    <td>
                      <Badge tone={c.valid_fraction > 0.9 ? "green" : "amber"}>
                        {percent(c.valid_fraction)}
                      </Badge>
                    </td>
                    <td>
                      {c.present === null
                        ? "Unlabelled"
                        : c.present
                          ? "Person present"
                          : "No person"}
                    </td>
                    <td>{c.windows}</td>
                    <td>
                      <button
                        className="round-btn small"
                        onClick={() => choose(c.id)}
                        aria-label={"Inspect " + c.name}
                      >
                        <ArrowRight size={16} />
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <Empty
            icon={FolderOpen}
            title={
              state.captures.length
                ? "No matching recordings"
                : "A fresh start for your research."
            }
          >
            Upload your first recording to inspect the signal and its quality.
            No raw dataset is bundled with Orbit.
          </Empty>
        )}
      </section>
      {capture && view && (
        <>
          <div className="section-heading">
            <h2>Inside the recording</h2>
            <Button secondary onClick={() => navigate("dsp")}>
              Open in Signal Studio <ArrowRight size={16} />
            </Button>
          </div>
          <section className="panel">
            <div className="panel-heading">
              <div>
                <Badge>RECORDED DATA</Badge>
                <h2>{capture.name}</h2>
              </div>
              <label>
                Subcarrier
                <select
                  value={sub}
                  onChange={(e) => setSub(Number(e.target.value))}
                >
                  <option value={-1}>Median across subcarriers</option>
                  {Array.from({ length: capture.subcarriers }, (_, i) => (
                    <option key={i} value={i}>
                      Subcarrier {i}
                    </option>
                  ))}
                </select>
              </label>
            </div>
            <Chart
              series={[{ name: "CSI amplitude", data: view.trace }]}
              x={view.packet}
              exportName="csi-amplitude"
            />
            <div className="playback-controls">
              <Button
                secondary
                disabled={start === 0}
                onClick={() => setStart(Math.max(0, start - 1024))}
              >
                <ChevronLeft size={16} /> Previous
              </Button>
              <span>
                Packets {start}–{Math.min(start + 1024, capture.packets)}
              </span>
              <Button
                secondary
                disabled={start + 1024 >= capture.packets}
                onClick={() => setStart(start + 1024)}
              >
                Next <ChevronRight size={16} />
              </Button>
            </div>
          </section>
          <div className="two-column">
            <section className="panel">
              <h2>Across the subcarriers</h2>
              <p>
                Sampled heatmap for display; all packets remain available to the
                analysis.
              </p>
              <Chart
                heatmap={view.heatmap}
                labels={{ x: view.heatmap_packet, y: view.heatmap_subcarrier }}
                exportName="csi-heatmap"
              />
            </section>
            <section className="panel">
              <h2>Quality & provenance</h2>
              <div className="metadata-grid">
                {[
                  ["Shape", `${capture.subcarriers} × ${capture.packets}`],
                  ["Date", capture.date],
                  ["Modulation", capture.modulation],
                  ["All-zero packets", capture.zero_packets],
                  ["Invalid packets", capture.invalid_packets],
                  ["Accepted windows", capture.windows],
                  ["Rejected windows", capture.rejected_windows],
                  ["SHA-256", capture.sha256],
                ].map(([k, v]) => (
                  <div key={k}>
                    <span>{k}</span>
                    <strong>{v}</strong>
                  </div>
                ))}
              </div>
              {view.packet_audit && <div className="packet-audit">
                <h3>Packet-loss / invalid-column audit</h3>
                <p>{view.packet_audit.zero_packets} all-zero · {view.packet_audit.nonfinite_packets} nonfinite · {view.packet_audit.longest_burst} longest unusable burst</p>
                <p>{view.packet_audit.protocol}</p>
                <details><summary>Unusable packet ranges</summary><pre>{JSON.stringify(view.packet_audit.bursts, null, 2)}</pre></details>
                <p>Invalid trace samples are gaps, not measured zero amplitude. Model quality contract v2 rejects windows below 90% validity.</p>
              </div>}
              {capture.warnings.map((w: string) => (
                <Note key={w}>{w}</Note>
              ))}
            </section>
          </div>
        </>
      )}
      {state.datasets.length > 0 && (
        <section className="panel">
          <h2>Imported datasets</h2>
          {state.datasets.map((d: Dict) => (
            <div key={d.id} className="dataset-row">
              <Database size={20} />
              <div>
                <strong>{d.name}</strong>
                <p>
                  {d.captures} captures · {(d.size / 1024 ** 2).toFixed(1)} MiB
                  · {new Date(d.created).toLocaleString()}
                </p>
                {d.errors?.map((e: Dict, i: number) => (
                  <small key={i} className="error-text">
                    {e.file}: {e.error}
                  </small>
                ))}
              </div>
              <button
                className="icon-btn"
                onClick={() => onDelete(d.id)}
                title="Remove dataset"
              >
                <Trash2 size={17} />
              </button>
            </div>
          ))}
        </section>
      )}
    </>
  );
}
function DSPPage({
  state,
  capture,
  selected,
  choose,
  navigate,
  notify,
  refresh,
}: Common) {
  const [demo, setDemo] = useState(false);
  const [operation, setOperation] = useState("moving_average");
  const [taps, setTaps] = useState(15);
  const [windowType, setWindowType] = useState("hann");
  const [cutoff, setCutoff] = useState(0.1);
  const [kind, setKind] = useState("lowpass");
  const [factor, setFactor] = useState(2);
  const [length, setLength] = useState(1024);
  const [start, setStart] = useState(0);
  const [sub, setSub] = useState(-1);
  const [win, setWin] = useState(256);
  const [hop, setHop] = useState(128);
  const [result, setResult] = useState<Dict | null>(null);
  const [features, setFeatures] = useState<Dict | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  useEffect(() => {
    setResult(null);
    setFeatures(null);
  }, [
    operation,
    taps,
    windowType,
    cutoff,
    kind,
    factor,
    length,
    start,
    sub,
    win,
    hop,
  ]);
  const source = demo ? null : capture;
  const settings = () => ({
    capture_id: source?.id || null,
    operation,
    taps,
    window: windowType,
    cutoff,
    kind,
    factor,
    length,
    start: source ? start : 0,
    subcarrier: source ? sub : -1,
  });
  const run = async () => {
    if (!source && !demo) return;
    setLoading(true);
    setError("");
    try {
      setResult(await api("dsp", settings()));
      if (source)
        setFeatures(
          await api(
            `captures/${source.id}?start=${start}&length=${length}&window=${win}&hop=${hop}&subcarrier=${sub}`,
          ),
        );
      else setFeatures(null);
    } catch (e: any) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };
  useEffect(() => {
    setResult(null);
    setFeatures(null);
    setStart(0);
    setSub(-1);
  }, [source?.id, demo]);
  const ops = [
    ["moving_average", "Moving-average FIR"],
    ["shootout", "Filter shootout"],
    ["fir", "Windowed FIR design"],
    ["butterworth", "Butterworth IIR"],
    ["fft", "Direct DFT vs radix-2 FFT"],
    ["convolution", "Linear vs circular convolution"],
    ["multirate", "Anti-aliased decimation"],
    ["interpolation", "Polyphase interpolation"],
    ["hilbert", "Hilbert envelope"],
    ["stft", "STFT spectrogram"],
    ["q15", "Q15 coefficients"],
  ];
  const graph = (name: string, children: React.ReactNode) => (
    <section className="panel">
      <div className="panel-heading">
        <h2>{name}</h2>
        <Badge tone="muted">{result?.source}</Badge>
      </div>
      {children}
    </section>
  );
  return (
    <>
      <div className="studio-source">
        <CaptureSelect {...{ state, selected, choose }} />
        <div className="segmented">
          <button
            className={!demo ? "active" : ""}
            onClick={() => setDemo(false)}
          >
            Recorded CSI
          </button>
          <button
            className={demo ? "active" : ""}
            onClick={() => setDemo(true)}
          >
            Teaching signal
          </button>
        </div>
        <Badge tone={demo ? "amber" : "cyan"}>
          {demo ? "EDUCATIONAL DEMO" : "RECORDED DATA"}
        </Badge>
      </div>
      {demo && (
        <Note>
          A deterministic synthetic signal: two sinusoids plus seeded noise. It
          is an educational example, with no presence labels or detection
          claims.
        </Note>
      )}
      {!source && !demo ? (
        <section className="panel">
          <Empty
            title="Start with a signal."
            action={
              <div className="button-row">
                <Button onClick={() => navigate("data")}>
                  <Upload size={16} /> Add recording
                </Button>
                <Button secondary onClick={() => setDemo(true)}>
                  Use teaching signal
                </Button>
              </div>
            }
          >
            Choose an imported CSI recording, or explore the tools with a
            clearly labelled synthetic signal.
          </Empty>
        </section>
      ) : (
        <>
          <section className="panel dsp-controls">
            <div className="panel-heading">
              <div>
                <span className="eyebrow orange-text">
                  THE EXPERIMENT BENCH
                </span>
                <h2>One change. A new perspective.</h2>
              </div>
              <SlidersHorizontal size={22} />
            </div>
            <div className="control-grid">
              <label className="wide">
                Operation
                <select
                  value={operation}
                  onChange={(e) => setOperation(e.target.value)}
                >
                  {ops.map(([v, l]) => (
                    <option key={v} value={v}>
                      {l}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                Window function
                <select
                  value={windowType}
                  onChange={(e) => setWindowType(e.target.value)}
                >
                  {[
                    ["boxcar", "Rectangular"],
                    ["triang", "Triangular"],
                    ["hann", "Hann"],
                    ["hamming", "Hamming"],
                    ["blackman", "Blackman"],
                  ].map(([v, l]) => (
                    <option key={v} value={v}>
                      {l}
                    </option>
                  ))}
                </select>
              </label>
              {[
                "moving_average",
                "fir",
                "convolution",
                "q15",
                "shootout",
              ].includes(operation) && (
                <label>
                  Filter taps
                  <input
                    type="number"
                    min={3}
                    max={127}
                    step={2}
                    value={taps}
                    onChange={(e) => setTaps(Number(e.target.value))}
                  />
                </label>
              )}
              {["fir", "butterworth", "q15"].includes(operation) && (
                <label>
                  Cutoff · cycles/packet
                  <input
                    type="number"
                    min={0.005}
                    max={0.495}
                    step={0.005}
                    value={cutoff}
                    onChange={(e) => setCutoff(Number(e.target.value))}
                  />
                </label>
              )}
              {operation === "butterworth" && (
                <label>
                  Filter type
                  <select
                    value={kind}
                    onChange={(e) => setKind(e.target.value)}
                  >
                    <option value="lowpass">Low-pass</option>
                    <option value="highpass">High-pass</option>
                    <option value="bandpass">
                      Band-pass (cutoff/2 to cutoff)
                    </option>
                  </select>
                </label>
              )}
              {["multirate", "interpolation"].includes(operation) && (
                <label>
                  Rate factor
                  <input
                    type="number"
                    value={factor}
                    min={2}
                    max={8}
                    onChange={(e) => setFactor(Number(e.target.value))}
                  />
                </label>
              )}
              <label>
                Display packets
                <select
                  value={length}
                  onChange={(e) => setLength(Number(e.target.value))}
                >
                  {[256, 512, 1024, 2048, 4096].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
              </label>
              {source && (
                <>
                  <label>
                    Start packet
                    <input
                      type="number"
                      min={0}
                      max={source.packets - 32}
                      value={start}
                      onChange={(e) => setStart(Number(e.target.value))}
                    />
                  </label>
                  <label>
                    Trace
                    <select
                      value={sub}
                      onChange={(e) => setSub(Number(e.target.value))}
                    >
                      <option value={-1}>Median across subcarriers</option>
                      {Array.from({ length: source.subcarriers }, (_, i) => (
                        <option key={i} value={i}>
                          Subcarrier {i}
                        </option>
                      ))}
                    </select>
                  </label>
                  <label>
                    Inspection window
                    <input
                      type="number"
                      value={win}
                      min={16}
                      max={2048}
                      onChange={(e) => setWin(Number(e.target.value))}
                    />
                  </label>
                  <label>
                    Inspection hop
                    <input
                      type="number"
                      value={hop}
                      min={1}
                      max={win}
                      onChange={(e) => setHop(Number(e.target.value))}
                    />
                  </label>
                </>
              )}
            </div>
            <div className="controls-footer">
              <span>
                Frequency stays in normalized units until a packet rate is
                verified.
              </span>
              <Button disabled={loading} onClick={run}>
                {loading ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Play size={16} />
                )}{" "}
                Recalculate experiment
              </Button>
            </div>
            {error && <Note tone="red">{error}</Note>}
          </section>
          {result ? (
            <>
              <Note tone="cyan">{result.note}</Note>
              <div className="metric-grid">
                {Object.entries(result.metrics).map(([k, v]) => (
                  <div className="metric-card" key={k}>
                    <span>{k.replaceAll("_", " ")}</span>
                    <strong>{pretty(v, 5)}</strong>
                  </div>
                ))}
              </div>
              {graph(
                "Time domain · amplitude",
                <Chart
                  series={[
                    {
                      name: "Raw amplitude",
                      data: result.raw,
                      color: "#4f7dff",
                    },
                    {
                      name: "Processed",
                      data: result.processed,
                      color: "#fb923c",
                      x: result.processed.map(
                        (_: any, i: number) =>
                          result.start +
                          i * (result.extra.output_packet_spacing || 1),
                      ),
                    },
                    ...(result.extra.fir_trace
                      ? [
                          {
                            name: "Windowed FIR",
                            data: result.extra.fir_trace,
                            color: "#34d399",
                          },
                          {
                            name: "Butterworth IIR",
                            data: result.extra.butterworth_trace,
                            color: "#a78bfa",
                          },
                        ]
                      : []),
                    ...(result.extra.circular
                      ? [
                          {
                            name: "Circular convolution",
                            data: result.extra.circular,
                            color: "#a78bfa",
                            dashed: true,
                          },
                        ]
                      : []),
                    ...(result.extra.naive
                      ? [
                          {
                            name: "Naive decimation",
                            data: result.extra.naive,
                            color: "#a78bfa",
                            dashed: true,
                            x: result.extra.naive.map(
                              (_: any, i: number) => result.start + i * factor,
                            ),
                          },
                        ]
                      : []),
                  ]}
                  x={result.raw.map((_: any, i: number) => i + result.start)}
                  exportName="orbit-time-domain"
                />,
              )}
              <div className="two-column">
                {graph(
                  "Spectrum · mean removed",
                  <Chart
                    series={[
                      {
                        name: "Raw",
                        data: result.raw_spectrum,
                        color: "#4f7dff",
                      },
                      {
                        name: "Processed",
                        data: result.processed_spectrum,
                        color: "#fb923c",
                      },
                    ]}
                    x={result.frequency}
                    axis={
                      ["multirate", "interpolation"].includes(operation)
                        ? "Cycles / sample (each signal’s own rate)"
                        : "Cycles / packet"
                    }
                    exportName="orbit-spectrum"
                  />,
                )}
                {[
                  "moving_average",
                  "fir",
                  "butterworth",
                  "convolution",
                  "q15",
                ].includes(operation) ? (
                  graph(
                    "Filter frequency response",
                    <Chart
                      series={[
                        {
                          name: "Magnitude · dB",
                          data: result.response_db,
                          color: "#fb923c",
                        },
                      ]}
                      x={result.response_frequency}
                      axis="Cycles / packet"
                      exportName="orbit-filter-response"
                    />,
                  )
                ) : (
                  <section className="panel">
                    <h2>Experiment notes</h2>
                    <p>{result.note}</p>
                    {Object.entries(result.extra)
                      .filter(([, v]) => typeof v === "number")
                      .map(([k, v]) => (
                        <div className="session-row" key={k}>
                          <span>{k.replaceAll("_", " ")}</span>
                          <strong>{pretty(v, 8)}</strong>
                        </div>
                      ))}
                    <Note tone="cyan">
                      Plots use the actual numerical output. Export any plot as
                      PNG using its download control.
                    </Note>
                  </section>
                )}
              </div>
              {result.extra.stft &&
                graph(
                  "Short-time spectrum",
                  <Chart
                    height={310}
                    yName="Cycles / packet"
                    heatmap={result.extra.stft.magnitude}
                    labels={{
                      x: result.extra.stft.packet.map((v: number) =>
                        Math.round(v + result.start),
                      ),
                      y: result.extra.stft.frequency.map((v: number) =>
                        v.toFixed(3),
                      ),
                    }}
                    exportName="orbit-stft"
                  />,
                )}
              {features && (
                <section className="panel">
                  <div className="panel-heading">
                    <h2>Feature inspector</h2>
                    <Badge>RECORDED WINDOW</Badge>
                  </div>
                  <p>
                    Packets {features.feature_window.start}–
                    {features.feature_window.end} ·{" "}
                    {features.inspection_windows.length} full inspection windows
                    at {win}/{hop}. These inspection settings do not alter the
                    saved model contract.
                  </p>
                  <div className="metric-grid">
                    {[
                      "Mean amplitude",
                      "Standard deviation",
                      "Mean absolute difference",
                      "P90 − P10",
                    ].map((l, i) => (
                      <div className="metric-card" key={l}>
                        <span>{l} · subcarrier average</span>
                        <strong>{pretty(features.feature_means[i], 5)}</strong>
                      </div>
                    ))}
                  </div>
                  <details>
                    <summary>
                      Inspect the full feature vector (
                      {features.feature_vector.length} values)
                    </summary>
                    <pre>
                      {JSON.stringify(features.feature_vector, null, 1)}
                    </pre>
                  </details>
                </section>
              )}
              {[
                "moving_average",
                "fir",
                "convolution",
                "q15",
                "shootout",
              ].includes(operation) && (
                <section className="panel">
                  <h2>Filter coefficients</h2>
                  <div className="coefficient-list">
                    {result.coefficients.map((v: number, i: number) => (
                      <span key={i}>
                        <small>b[{i}]</small>
                        {v.toFixed(7)}
                      </span>
                    ))}
                  </div>
                </section>
              )}
              <div className="button-row end">
                <Button
                  secondary
                  onClick={async () => {
                    try {
                      await api("runs", settings());
                      await refresh();
                      notify("Experiment settings and metrics saved locally.");
                    } catch (e: any) {
                      notify(e.message);
                    }
                  }}
                >
                  <CheckCircle2 size={17} /> Save this experiment
                </Button>
              </div>
            </>
          ) : (
            <section className="panel">
              <Empty
                icon={SlidersHorizontal}
                title="Set it up. Then see it change."
              >
                Choose an operation and press Recalculate experiment to run the
                scientific pipeline on this source.
              </Empty>
            </section>
          )}
        </>
      )}
    </>
  );
}
function LearningPage({
  state,
  capture,
  selected,
  choose,
  navigate,
  notify,
  refresh,
  job,
}: Common) {
  const [tab, setTab] = useState("models");
  const [bw, setBw] = useState(20);
  const [split, setSplit] = useState("date");
  const [dataset, setDataset] = useState("");
  const [modelKind, setModelKind] = useState("all");
  const [pop, setPop] = useState(8);
  const [gen, setGen] = useState(6);
  const [mutation, setMutation] = useState(0.03);
  const [options, setOptions] = useState<Dict[]>([]);
  const [trainError, setTrainError] = useState("");
  const [trainId, setTrainId] = useState("");
  useEffect(() => { api("train/options").then(setOptions).catch(() => setOptions([])); }, [state.captures]);
  useEffect(() => { setTrainError(""); setTrainId(""); }, [dataset, bw, split, modelKind, tab, pop, gen, mutation]);
  useEffect(() => { const failed = state.jobs.find((j: Dict) => j.id === trainId && j.status === "failed"); if (failed) setTrainError(failed.message); }, [state.jobs, trainId]);
  const optionFor = (kind: string, bandwidth = bw, datasetId = dataset) => options.find((o: Dict) => o.dataset_id === datasetId && o.bandwidth === bandwidth && o.split === split && o.kind === kind);
  const check = optionFor(tab === "ga" ? "ga_rf" : modelKind === "all" ? "lr" : modelKind);

  const [variation, setVariation] = useState(0.4);
  const [motion, setMotion] = useState(0.6);
  const [fuzzyResult, setFuzzyResult] = useState<Dict | null>(null);
  const [rules, setRules] = useState<Dict[]>([
    { variation: "low", motion: "low", output: "low" },
    { variation: "medium", motion: "medium", output: "medium" },
    { variation: "high", motion: "high", output: "high" },
    { variation: "high", motion: "medium", output: "high" },
    { variation: "medium", motion: "high", output: "high" },
  ]);
  const [feature, setFeature] = useState<Dict | null>(null);
  const [fuzzyError, setFuzzyError] = useState("");
  useEffect(() => {
    if (tab === "fuzzy") {
      const t = setTimeout(
        () =>
          api("fuzzy", { variation, motion, rules })
            .then((r) => {
              setFuzzyResult(r);
              setFuzzyError("");
            })
            .catch((e) => setFuzzyError(e.message)),
        160,
      );
      return () => clearTimeout(t);
    }
  }, [variation, motion, rules, tab]);
  useEffect(() => {
    if (tab === "features" && capture)
      api("captures/" + capture.id + "/features")
        .then(setFeature)
        .catch((e) => notify(e.message));
    else setFeature(null);
  }, [tab, capture?.id]);
  const train = async () => {
    try {
      setTrainError("");
      const queued = await api("train", {
        dataset_id: dataset || null,
        bandwidth: bw,
        split,
        kinds:
          tab === "ga"
            ? ["rf", "ga_rf"]
            : modelKind === "all"
              ? ["lr", "rf", "mlp"]
              : [modelKind],
        population: pop,
        generations: gen,
        mutation,
      });
      setTrainId(queued.id);
      await refresh();
      notify(
        "Training queued. Progress appears above; results are saved locally.",
      );
    } catch (e: any) {
      setTrainError(e.message);
    }
  };
  const models = state.models.filter((m: Dict) => m.contract.bandwidth === bw && m.contract.version === "orbit-amplitude-v2");
  return (
    <>
      <p className="helper">Learning Lab contains the soft-computing tools: ANN & model bench, Genetic algorithms and Fuzzy logic. Signal Studio contains DSP. Fuzzy rules are currently an educational sandbox, not a validated model-fusion or quality gate.</p>
      <div className="tabs">
        {[
          ["models", "ANN & model bench"],
          ["ga", "Genetic algorithms"],
          ["fuzzy", "Fuzzy logic"],
          ["features", "Feature explorer"],
        ].map(([id, l]) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={tab === id ? "active" : ""}
          >
            {l}
          </button>
        ))}
      </div>
      {(tab === "models" || tab === "ga") && (
        <>
          <div className="two-column">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <Badge tone="violet">RECORDED DATA EXPERIMENT</Badge>
                  <h2>
                    {tab === "ga"
                      ? "Let the features compete."
                      : "Train. Compare. Question."}
                  </h2>
                </div>
                <BrainCircuit size={24} />
              </div>
              <p>
                {tab === "ga"
                  ? "GA feature selection runs inside each training fold. Held-out recordings stay outside the search. Compare its capture metrics with all-feature RF on the same outer split."
                  : "Logistic Regression, Random Forest and an ANN with two hidden layers. Scaling is fitted within each training fold."}
              </p>
              <div className="control-grid">
                <label className="wide">
                  Training data
                  <select
                    value={dataset}
                    onChange={(e) => setDataset(e.target.value)}
                  >
                    <option value="">
                      All imported datasets · deduplicated by hash
                    </option>
                    {state.datasets.map((d: Dict) => (
                      <option key={d.id} value={d.id} disabled={!options.some((o: Dict) => o.dataset_id === d.id && o.valid)}>
                        {d.name}
                      </option>
                    ))}
                  </select>
                </label>
                <label>
                  Bandwidth
                  <select
                    value={bw}
                    onChange={(e) => setBw(Number(e.target.value))}
                  >
                    <option value={20} disabled={!options.some((o: Dict) => o.dataset_id === dataset && o.bandwidth === 20 && o.valid)}>20 MHz / 256 subcarriers</option>
                    <option value={40} disabled={!options.some((o: Dict) => o.dataset_id === dataset && o.bandwidth === 40 && o.valid)}>40 MHz / 512 subcarriers</option>
                  </select>
                </label>
                <label>
                  Outer evaluation
                  <select
                    value={split}
                    onChange={(e) => setSplit(e.target.value)}
                  >
                    <option value="date">Leave one recording date out</option>
                    <option value="capture">
                      Leave one capture out · exploratory
                    </option>
                  </select>
                </label>
                {tab === "models" ? (
                  <label className="wide">
                    Models
                    <select
                      value={modelKind}
                      onChange={(e) => setModelKind(e.target.value)}
                    >
                      <option value="all" disabled={!optionFor("lr")?.valid}>Compare LR + RF + ANN / MLP</option>
                      <option value="lr" disabled={!optionFor("lr")?.valid}>Logistic Regression</option>
                      <option value="rf" disabled={!optionFor("rf")?.valid}>Random Forest</option>
                      <option value="mlp" disabled={!optionFor("mlp")?.valid}>
                        ANN / MLP · 64 → 32 hidden units
                      </option>
                    </select>
                  </label>
                ) : (
                  <>
                    <label>
                      Population
                      <input
                        type="number"
                        min={4}
                        max={16}
                        value={pop}
                        onChange={(e) => setPop(Number(e.target.value))}
                      />
                    </label>
                    <label>
                      Generations
                      <input
                        type="number"
                        min={1}
                        max={15}
                        value={gen}
                        onChange={(e) => setGen(Number(e.target.value))}
                      />
                    </label>
                    <label>
                      Mutation probability
                      <input
                        type="number"
                        min={0}
                        max={0.3}
                        step={0.01}
                        value={mutation}
                        onChange={(e) => setMutation(Number(e.target.value))}
                      />
                    </label>
                  </>
                )}
              </div>
              <Button
                disabled={!!job || !check?.valid}
                onClick={train}
              >
                {job ? (
                  <LoaderCircle className="spin" size={17} />
                ) : (
                  <Play size={16} />
                )}{" "}
                {tab === "ga"
                  ? "Run nested GA + RF comparison"
                  : "Train & evaluate"}
              </Button>
              {state.datasets.filter((d: Dict) => !options.some((o: Dict) => o.dataset_id === d.id && o.valid)).map((d: Dict) => <p className="helper" key={d.id}>{d.name}: {options.find((o: Dict) => o.dataset_id === d.id)?.reason || "Checking training eligibility…"}</p>)}
              {!check?.valid && <p className="helper" role="status">{check?.reason || "Checking compatible training choices…"}</p>}
              {trainError && <Note tone="red">Next step: {trainError}</Note>}
              {!state.captures.length && (
                <p className="helper">
                  Import labelled captures to enable training.
                </p>
              )}
            </section>
            <section className="panel">
              <span className="eyebrow violet-text">
                THE VALIDATION CONTRACT
              </span>
              <h2>Keep the test set honest.</h2>
              <ul className="check-list">
                <li>
                  <ShieldCheck size={17} /> All windows of a capture stay in one
                  outer fold.
                </li>
                <li>
                  <ShieldCheck size={17} /> Date splits hold out a complete
                  recording date.
                </li>
                <li>
                  <ShieldCheck size={17} /> Duplicated captures are removed by
                  content hash.
                </li>
                <li>
                  <ShieldCheck size={17} /> Feature order and bandwidth are
                  checked at inference.
                </li>
              </ul>
              <Note>
                {tab === "ga"
                  ? "GA uses inner capture-grouped validation, with balanced capture accuracy and a small feature-count penalty. It needs at least two training captures per class in each outer fold. A seeded random-feature baseline uses the same number of features and the same held-out folds."
                  : "Small datasets produce uncertain estimates. The 40 MHz historical dataset is date/class confounded. Its reported 100% accuracy does not establish generalization."}
              </Note>
              {tab === "models" && (
                <div className="network-diagram">
                  <span>
                    Input<small>1,024 / 2,048</small>
                  </span>
                  <ArrowRight size={18} />
                  <b>64</b>
                  <ArrowRight size={18} />
                  <b>32</b>
                  <ArrowRight size={18} />
                  <span>
                    Output<small>2 classes</small>
                  </span>
                </div>
              )}
              {tab === "ga" && (
                <div className="historical-callout">
                  <Badge tone="muted">EARLIER RECORDED EXPERIMENT</Badge>
                  <strong>8 & 12 features</strong>
                  <p>
                    Selected in the two historical date folds. Earlier GA + RF
                    capture accuracy: 80.0%; balanced accuracy: 81.25%; raw RF: 73.3%. Protocol: leave-one-recording-date-out, capture majority vote. A small-data
                    exploratory result, from a different run than the latest
                    comparison.
                  </p>
                </div>
              )}
            </section>
          </div>
          <div className="section-heading">
            <h2>
              Your model shelf <span className="count">{models.length}</span>
            </h2>
            <span>Quality contract v2 · legacy artifacts preserved, retraining required</span>
          </div>
          {models.length ? (
            <>
              {models.map((m: Dict) => (
                <section className="panel model-card" key={m.id}>
                  <div className="panel-heading">
                    <div>
                      <Badge tone="violet">{m.source}</Badge>
                      <h2>{m.name}</h2>
                      <p>
                        {m.contract.bandwidth} MHz · {m.split} ·{" "}
                        {m.captures.length} independent captures
                      </p>
                    </div>
                    <a
                      className="button secondary"
                      href={"/api/export/model/" + m.id}
                    >
                      <Download size={16} /> Manifest & results
                    </a>
                  </div>
                  <div className="metric-grid">
                    {["accuracy", "balanced_accuracy", "f1", "macro_f1"].map(
                      (k) => (
                        <div className="metric-card" key={k}>
                          <span>Capture {k.replaceAll("_", " ")}</span>
                          <small>{m.split} · majority vote</small>
                          <strong>{percent(m.metrics[k])}</strong>
                        </div>
                      ),
                    )}
                  </div>
                  {m.random_feature_baseline && (
                    <Note tone="violet">
                      Matched random-feature RF baseline: capture accuracy{" "}
                      {percent(m.random_feature_baseline.metrics.accuracy)},
                      balanced accuracy{" "}
                      {percent(
                        m.random_feature_baseline.metrics.balanced_accuracy,
                      )}
                      . Same outer folds and feature count.
                    </Note>
                  )}
                  {m.loss_curve?.length > 0 && (
                    <Chart
                      series={[
                        {
                          name: "Training loss",
                          data: m.loss_curve,
                          color: "#a78bfa",
                        },
                      ]}
                      axis="Iteration"
                      exportName="ann-loss"
                    />
                  )}
                  {m.convergence?.length > 0 && (
                    <Chart
                      series={[
                        {
                          name: "Final-fit inner fitness · not test accuracy",
                          data: m.convergence,
                          color: "#a78bfa",
                        },
                      ]}
                      axis="Generation"
                      exportName="ga-convergence"
                    />
                  )}
                  {m.selected_features && (
                    <details>
                      <summary>
                        {m.selected_features.length} final-fit selected feature
                        indices
                      </summary>
                      <pre>{JSON.stringify(m.selected_features)}</pre>
                    </details>
                  )}
                  <div className="two-column">
                    <Confusion matrix={m.metrics.confusion_matrix} />
                    <div>
                      {m.caveats.map((w: string) => (
                        <Note key={w}>{w}</Note>
                      ))}
                    </div>
                  </div>
                  <details>
                    <summary>
                      Inspect independent folds and capture predictions
                    </summary>
                    <pre>
                      {JSON.stringify(
                        { folds: m.folds, predictions: m.capture_predictions },
                        null,
                        2,
                      )}
                    </pre>
                  </details>
                </section>
              ))}
            </>
          ) : (
            <section className="panel">
              <Empty
                icon={BrainCircuit}
                title="A model earns its place here."
                action={
                  <Button secondary onClick={() => navigate("data")}>
                    Import training recordings <ArrowRight size={16} />
                  </Button>
                }
              >
                No trained artifact was bundled in the research repository.
                Import labelled data, then train a compatible model.
              </Empty>
            </section>
          )}
        </>
      )}
      {tab === "fuzzy" && (
        <>
          <Note>
            Educational Mamdani rule system on normalized inputs. This score is
            not a presence prediction or a calibrated probability.
          </Note>
          <div className="two-column">
            <section className="panel">
              <Badge tone="violet">EDUCATIONAL DEMO</Badge>
              <h2>Rules you can read.</h2>
              <label>
                Illustrative amplitude variation <b>{variation.toFixed(2)}</b>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={variation}
                  onChange={(e) => setVariation(Number(e.target.value))}
                />
              </label>
              <label>
                Illustrative motion input <b>{motion.toFixed(2)}</b>
                <input
                  type="range"
                  min={0}
                  max={1}
                  step={0.01}
                  value={motion}
                  onChange={(e) => setMotion(Number(e.target.value))}
                />
              </label>
              <div className="fuzzy-verdict">
                <span>CENTROID DEFUZZIFICATION</span>
                <strong>
                  {fuzzyResult?.value == null
                    ? "No rule fired"
                    : fuzzyResult.value.toFixed(3)}
                </strong>
                <p>Illustrative activity score</p>
              </div>
              <p>
                AND uses minimum. Rules clip their output membership;
                aggregation uses maximum. The centroid gives the resulting
                score.
              </p>
            </section>
            <section className="panel">
              <h2>The membership landscape</h2>
              {fuzzyResult && (
                <Chart
                  x={fuzzyResult.universe}
                  series={Object.entries(fuzzyResult.memberships)
                    .map(([name, data]) => ({
                      name,
                      data: data as number[],
                      color: undefined as string | undefined,
                    }))
                    .concat([
                      {
                        name: "Aggregated output",
                        data: fuzzyResult.aggregate,
                        color: "#fb923c",
                      },
                    ])}
                  axis="Normalized value"
                  exportName="fuzzy-memberships"
                />
              )}
            </section>
          </div>
          <section className="panel">
            <div className="panel-heading">
              <h2>Edit the rule base</h2>
              <Button
                secondary
                disabled={rules.length >= 20}
                onClick={() =>
                  setRules([
                    ...rules,
                    { variation: "medium", motion: "low", output: "medium" },
                  ])
                }
              >
                <Plus size={16} /> Add rule
              </Button>
            </div>
            {rules.map((rule, i) => (
              <div className="fuzzy-rule" key={i}>
                <span>IF variation</span>
                <select
                  aria-label={"Rule " + (i + 1) + " variation"}
                  value={rule.variation}
                  onChange={(e) =>
                    setRules(
                      rules.map((r, j) =>
                        j === i ? { ...r, variation: e.target.value } : r,
                      ),
                    )
                  }
                >
                  {["low", "medium", "high"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
                <span>AND motion</span>
                <select
                  aria-label={"Rule " + (i + 1) + " motion"}
                  value={rule.motion}
                  onChange={(e) =>
                    setRules(
                      rules.map((r, j) =>
                        j === i ? { ...r, motion: e.target.value } : r,
                      ),
                    )
                  }
                >
                  {["low", "medium", "high"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
                <span>THEN score</span>
                <select
                  aria-label={"Rule " + (i + 1) + " output"}
                  value={rule.output}
                  onChange={(e) =>
                    setRules(
                      rules.map((r, j) =>
                        j === i ? { ...r, output: e.target.value } : r,
                      ),
                    )
                  }
                >
                  {["low", "medium", "high"].map((v) => (
                    <option key={v}>{v}</option>
                  ))}
                </select>
                <Badge
                  tone={
                    fuzzyResult?.rules[i]?.strength > 0 ? "violet" : "muted"
                  }
                >
                  {pretty(fuzzyResult?.rules[i]?.strength, 2)} firing
                </Badge>
                <button
                  className="icon-btn"
                  disabled={rules.length === 1}
                  onClick={() => setRules(rules.filter((_, j) => j !== i))}
                  aria-label={"Delete rule " + (i + 1)}
                >
                  <X size={16} />
                </button>
              </div>
            ))}
            {fuzzyError && <Note tone="red">{fuzzyError}</Note>}
          </section>
        </>
      )}
      {tab === "features" && (
        <>
          <CaptureSelect {...{ state, selected, choose }} />
          {feature ? (
            <>
              <section className="panel">
                <h2>Four families of signal features.</h2>
                <p>
                  Actual accepted feature windows · {feature.group_means.length}{" "}
                  windows · {feature.contract.window}/{feature.contract.hop}{" "}
                  contract
                </p>
                <Chart
                  series={[
                    "Mean",
                    "Standard deviation",
                    "Mean absolute difference",
                    "P90 − P10",
                  ].map((name, i) => ({
                    name,
                    data: feature.group_means.map((row: number[]) => row[i]),
                  }))}
                  axis="Accepted window index"
                  exportName="feature-groups"
                />
              </section>
              <section className="panel">
                <h2>Correlation between feature-group averages</h2>
                {feature.correlation.length ? (
                  <div className="correlation-grid">
                    {feature.correlation.flatMap((r: number[], i: number) =>
                      r.map((v, j) => (
                        <div
                          key={`${i}-${j}`}
                          style={{
                            background: `rgba(167,139,250,${0.08 + Math.abs(v) * 0.5})`,
                          }}
                          title={`${["Mean", "Std", "Difference", "Range"][i]} / ${["Mean", "Std", "Difference", "Range"][j]}`}
                        >
                          {v.toFixed(3)}
                          <small>
                            {["Mean", "Std", "Diff", "Range"][i]} /{" "}
                            {["Mean", "Std", "Diff", "Range"][j]}
                          </small>
                        </div>
                      )),
                    )}
                  </div>
                ) : (
                  <Note>
                    At least two accepted windows are required for correlation.
                  </Note>
                )}
                <Note tone="cyan">
                  Descriptive within-recording correlation does not show
                  causation or out-of-domain performance.
                </Note>
              </section>
            </>
          ) : (
            <section className="panel">
              <Empty icon={Layers3} title="Pick a recording to explore.">
                Feature values and correlations come from the selected capture’s
                actual accepted windows.
              </Empty>
            </section>
          )}
        </>
      )}
    </>
  );
}
function Confusion({ matrix }: { matrix: number[][] }) {
  return (
    <div className="confusion">
      <span className="tiny-label">CAPTURE CONFUSION MATRIX</span>
      <div className="matrix-label">Predicted →</div>
      <div className="matrix-grid">
        <span />
        <small>No person</small>
        <small>Present</small>
        <small>No person</small>
        <strong className="correct">{matrix[0][0]}</strong>
        <strong>{matrix[0][1]}</strong>
        <small>Present</small>
        <strong>{matrix[1][0]}</strong>
        <strong className="correct">{matrix[1][1]}</strong>
      </div>
      <small>Rows = actual label · columns = predicted label</small>
    </div>
  );
}
function ReplayPage({
  state,
  capture,
  selected,
  choose,
  navigate,
  notify,
  refresh,
}: Common) {
  const [model, setModel] = useState("raw");
  const [mode, setMode] = useState("held_out");
  const [comparison, setComparison] = useState<Dict[]>([]);
  const [result, setResult] = useState<Dict | null>(null);
  const [view, setView] = useState<Dict | null>(null);
  const [index, setIndex] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [speed, setSpeed] = useState(1);
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    setIndex(0);
    setResult(null);
    setComparison([]);
    setPlaying(false);
  }, [capture?.id, model, mode]);
  const step = capture?.bandwidth === 40 ? 512 : 128;
  const count = Math.max(
    0,
    capture
      ? Math.floor(
          (capture.packets - (capture.bandwidth === 40 ? 256 : 256)) / step,
        ) + 1
      : 0,
  );
  const windowSize = capture?.bandwidth === 40 ? 512 : 256;
  useEffect(() => {
    let active = true; setView(null);
    if (capture) api(`captures/${capture.id}?start=${index * step}&length=${windowSize}`)
      .then((v) => { if (active) setView(v); }).catch((e) => { if (active) notify(e.message); });
    return () => { active = false; };
  }, [capture?.id, index]);
  useEffect(() => {
    if (!playing || !count) return;
    const timer = setInterval(
      () =>
        setIndex((i) => {
          if (i >= count - 1) {
            setPlaying(false);
            return i;
          }
          return i + 1;
        }),
      1000 / speed,
    );
    return () => clearInterval(timer);
  }, [playing, speed, count]);
  const qualitySkipped = model !== "raw" && !!view && view.packet?.length > 0 && (view.packet.length < 256 || view.invalid_indices.length / view.packet.length > 0.1);
  const currentPrediction = result?.windows.find(
    (w: Dict) => w.start === index * step,
  );
  const compatible = state.models.filter(
    (m: Dict) => m.contract.bandwidth === capture?.bandwidth && m.contract.version === "orbit-amplitude-v2" && (mode !== "held_out" || !!m.held_out_windows?.[capture?.sha256]),
  );
  return (
    <>
      <div className="studio-source">
        <CaptureSelect {...{ state, selected, choose }} />
        <label>
          Prediction protocol
          <select value={mode} onChange={(e) => setMode(e.target.value)}>
            <option value="held_out">Held-out predictions · default</option>
            <option value="seen">Seen in training / final model inference</option>
          </select>
        </label>
        <label>
          Available model
          <select value={model} onChange={(e) => setModel(e.target.value)}>
            <option value="all">Compare all available classifiers</option>
            <option value="raw">Raw CSI · no classifier</option>
            {compatible.map((m: Dict) => (
              <option key={m.id} value={m.id}>
                {m.name} · {m.contract.bandwidth} MHz
              </option>
            ))}
          </select>
        </label>
        <Button
          disabled={!capture || !model || loading || (model !== "raw" && !compatible.length)}
          onClick={async () => {
            setLoading(true);
            try {
              if (model === "raw") {
                setResult(null);
                setComparison([]);
                return;
              }
              if (model === "all") {
                const response = await api("predict/compare", {
                  capture_id: capture.id,
                  mode,
                });
                setComparison(response.results);
                setResult(
                  response.results.find(
                    (r: Dict) => r.model_name === "Random Forest",
                  ) || response.results[0],
                );
              } else {
                const response = await api("predict", {
                  capture_id: capture.id,
                  model_id: model,
                });
                setResult(response);
                setComparison([]);
              }
              await refresh();
            } catch (e: any) {
              notify(e.message);
            } finally {
              setLoading(false);
            }
          }}
        >
          {loading ? (
            <LoaderCircle className="spin" size={17} />
          ) : (
            <Play size={16} />
          )}{" "}
          {model === "all"
            ? "Run all classifiers"
            : model === "raw"
              ? "Inspect raw signal"
              : "Run selected model"}
        </Button>
      </div>
      {capture && !compatible.length && <Note>Retrain a compatible model under the current quality contract to save held-out predictions. For a new upload, use the explicitly labelled final-model inference option.</Note>}
      {comparison.length > 0 && (
        <div className="comparison-cards">
          {comparison.map((r: Dict) => (
            <button
              key={r.id}
              className={"panel " + (result?.id === r.id ? "chosen" : "")}
              onClick={() => setResult(r)}
            >
              <span>{r.model_name}</span>
              <strong>{r.prediction ? "Person present" : "No person"}</strong>
              <small>Mean P(presence): {percent(r.mean_probability)}</small>
              <small>{r.validation_protocol}</small>
              <Badge tone="violet">
                {r.in_training ? "TRAINING RECORDING" : "MODEL OUTPUT"}
              </Badge>
            </button>
          ))}
        </div>
      )}
      {!capture ? (
        <section className="panel">
          <Empty
            icon={Play}
            title="A recording, ready to revisit."
            action={
              <Button secondary onClick={() => navigate("data")}>
                Choose a recording <ArrowRight size={16} />
              </Button>
            }
          >
            Recorded-data replay works independently of a classifier.
            Predictions become available only after compatible training.
          </Empty>
        </section>
      ) : (
        <>
          <div className="replay-grid">
            <section className="panel">
              <div className="panel-heading">
                <div>
                  <Badge>RECORDED REPLAY</Badge>
                  <h2>{capture.name.split("/").pop()}</h2>
                </div>
                <span className="mono">
                  {String(index + 1).padStart(3, "0")} / {count} windows
                </span>
              </div>
              {view && (
                <Chart
                  series={[{ name: "Median CSI amplitude", data: view.trace }]}
                  x={view.packet}
                  exportName="replay-window"
                />
              )}
              <input
                aria-label="Replay position"
                type="range"
                min={0}
                max={Math.max(0, count - 1)}
                value={index}
                disabled={!count}
                onChange={(e) => {
                  setPlaying(false);
                  setIndex(Number(e.target.value));
                }}
              />
              <div className="playback-controls">
                <div className="button-row">
                  <button
                    className="icon-btn"
                    disabled={index === 0}
                    onClick={() => {
                      setPlaying(false);
                      setIndex((i) => i - 1);
                    }}
                    aria-label="Previous window"
                  >
                    <ChevronLeft size={20} />
                  </button>
                  <Button
                    disabled={!count}
                    onClick={() => {
                      if (index >= count - 1) setIndex(0);
                      setPlaying(!playing);
                    }}
                  >
                    {playing ? <Pause size={17} /> : <Play size={17} />}{" "}
                    {playing ? "Pause" : "Play recording"}
                  </Button>
                  <button
                    className="icon-btn"
                    disabled={index >= count - 1}
                    onClick={() => {
                      setPlaying(false);
                      setIndex((i) => i + 1);
                    }}
                    aria-label="Next window"
                  >
                    <ChevronRight size={20} />
                  </button>
                </div>
                <select
                  aria-label="Playback speed"
                  value={speed}
                  onChange={(e) => setSpeed(Number(e.target.value))}
                >
                  {[0.5, 1, 2, 4].map((s) => (
                    <option key={s} value={s}>
                      {s}× replay
                    </option>
                  ))}
                </select>
              </div>
              <p className="helper">
                Packet windows advance at the chosen demonstration speed. This
                is not the original capture timing.
              </p>
            </section>
            <section className="panel verdict-panel">
              <span className="tiny-label">{qualitySkipped ? "Window skipped (quality)" : !result ? (model === "raw" ? "No model selected" : "Model ready · run to predict") : !currentPrediction ? "Window skipped (quality)" : "Prediction"}</span>
              <div className="verdict-icon">
                <CircleDot size={35} />
              </div>
              <h2>
                {qualitySkipped ? "Window skipped (quality)" : currentPrediction
                  ? currentPrediction.prediction
                    ? "Person present"
                    : "No person"
                  : result
                    ? "Window skipped (quality)"
                    : model === "raw" ? "No model selected" : "Run a model to predict"}
              </h2>
              <p>
                {qualitySkipped ? "This window has fewer than 256 packets or less than 90% usable packets. Choose another window." : currentPrediction
                  ? `Uncalibrated P(presence): ${percent(currentPrediction.probability)}`
                  : result
                    ? "This window was not accepted by the model quality contract."
                    : "Train and run a compatible model to enable a presence verdict."}
              </p>
              <Badge tone={currentPrediction ? "violet" : "muted"}>
                {currentPrediction ? "MODEL OUTPUT" : "NO PREDICTION"}
              </Badge>
              {result && <p className="helper">{result.validation_protocol}</p>}
              {!compatible.length && (
                <button
                  className="text-button"
                  onClick={() => navigate("learning")}
                >
                  Open the model bench <ArrowRight size={16} />
                </button>
              )}
            </section>
          </div>
          {result && (
            <>
              <Note tone={result.in_training ? "amber" : "cyan"}>
                {result.validation_protocol}. {result.caveat}
              </Note>
              <section className="panel">
                <div className="panel-heading">
                  <h2>Prediction timeline</h2>
                  <Badge tone="violet">
                    MODEL OUTPUT · {result.model_name}
                  </Badge>
                </div>
                <Chart
                  series={[
                    {
                      name: "Uncalibrated P(presence)",
                      data: result.windows.map((w: Dict) => w.probability),
                      color: "#a78bfa",
                    },
                    {
                      name: "Window verdict (0/1)",
                      data: result.windows.map((w: Dict) => w.prediction),
                      color: "#22d3ee",
                    },
                  ]}
                  x={result.windows.map((w: Dict) => w.start)}
                  axis="Window start · packet index"
                  exportName="prediction-timeline"
                />
                <div className="controls-footer">
                  <p>
                    Capture majority vote:{" "}
                    <b>{result.prediction ? "Person present" : "No person"}</b>
                  </p>
                  <a
                    className="button secondary"
                    href={"/api/export/run/" + result.id}
                  >
                    <Download size={16} /> Export timeline CSV
                  </a>
                </div>
              </section>
            </>
          )}
          {!result && (
            <Note tone="cyan">
              You can inspect and replay this recording without a trained model.
              No presence decision is inferred from the shape of the waveform.
            </Note>
          )}
        </>
      )}
    </>
  );
}
function ResultsPage({
  state,
  evidence,
  navigate,
}: Common & { evidence: Dict }) {
  const [tab, setTab] = useState("models");
  const [bandwidth, setBandwidth] = useState("20");
  const [chosen, setChosen] = useState("Random Forest");
  const [query, setQuery] = useState("");
  const historical = evidence.presence_model_comparison_by_bandwidth || [];
  const rows = historical.filter((r: Dict) => r.bandwidth_mhz === bandwidth);
  const selected = rows.find((r: Dict) => r.model === chosen) || rows[0];
  const fullTable = (items: Dict[], key: string) => {
    const data = items.filter((r) =>
      JSON.stringify(r).toLowerCase().includes(query.toLowerCase()),
    );
    return (
      <>
        <div className="filter-bar">
          <div className="search-field">
            <Search size={16} />
            <input
              placeholder="Search this evidence table…"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
            />
          </div>
          <a className="button secondary" href={"/api/export/evidence/" + key}>
            <Download size={16} /> Original CSV
          </a>
        </div>
        <div className="panel table-panel">
          <div className="table-scroll">
            <table>
              <thead>
                <tr>
                  {Object.keys(items[0] || {}).map((k) => (
                    <th key={k}>{k.replaceAll("_", " ")}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.map((r, i) => (
                  <tr key={i}>
                    {Object.values(r).map((v, j) => (
                      <td key={j}>{String(v || "—")}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </>
    );
  };
  return (
    <>
      <div className="tabs">
        {[
          ["models", "Recorded models"],
          ["simulator", "AX / BF simulator"],
          ["domains", "Domain transfer"],
          ["audit", "Quality & splits"],
          ["local", "My experiments"],
        ].map(([id, l]) => (
          <button
            key={id}
            className={tab === id ? "active" : ""}
            onClick={() => {
              setTab(id);
              setQuery("");
            }}
          >
            {l}
          </button>
        ))}
      </div>
      {tab === "models" && (
        <>
          <div className="evidence-title">
            <div>
              <Badge tone="muted">HISTORICAL RESEARCH · SAVED CSV</Badge>
              <h2>A score is only part of the story.</h2>
            </div>
            <div className="segmented">
              {["20", "40"].map((b) => (
                <button
                  key={b}
                  className={bandwidth === b ? "active" : ""}
                  onClick={() => setBandwidth(b)}
                >
                  {b} MHz
                </button>
              ))}
            </div>
          </div>
          <Note>
            {bandwidth === "20"
              ? "15 captures from only two dates. Leave-one-recording-date-out evaluation limits overlap leakage, but generalization remains uncertain. ANN ties RF in the latest run."
              : "The 40 MHz subset has 11 captures with perfectly associated date and class. The reported 100% scores are confounded; they are not evidence of date-independent generalization. Do not rank bandwidths using these different protocols."}
          </Note>
          <section className="panel table-panel">
            <div className="table-scroll">
              <table>
                <thead>
                  <tr>
                    <th>Model</th>
                    <th>Capture accuracy</th>
                    <th>Balanced accuracy</th>
                    <th>Presence F1</th>
                    <th>Macro-F1</th>
                    <th>Support</th>
                  </tr>
                </thead>
                <tbody>
                  {rows.map((r: Dict) => (
                    <tr
                      key={r.model}
                      className={chosen === r.model ? "selected-row" : ""}
                      onClick={() => setChosen(r.model)}
                    >
                      <td>
                        <button
                          className="table-link"
                          onClick={() => setChosen(r.model)}
                        >
                          <BrainCircuit size={19} />
                          <b>{r.model}</b>
                        </button>
                      </td>
                      <td>{percent(r.capture_accuracy)}</td>
                      <td>{percent(r.capture_balanced_accuracy)}</td>
                      <td>{pretty(Number(r.capture_f1_presence), 4)}</td>
                      <td>{pretty(Number(r.capture_macro_f1), 4)}</td>
                      <td>{r.capture_count} captures</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          {selected && (
            <div className="two-column">
              <section className="panel">
                <div className="panel-heading">
                  <h2>{selected.model}</h2>
                  <Badge tone="muted">{bandwidth} MHz</Badge>
                </div>
                <Confusion
                  matrix={[
                    [
                      Number(selected.true_negative),
                      Number(selected.false_positive),
                    ],
                    [
                      Number(selected.false_negative),
                      Number(selected.true_positive),
                    ],
                  ]}
                />
              </section>
              <section className="panel">
                <span className="eyebrow">METHOD ATTACHED</span>
                <h2>Read the fine print.</h2>
                <div className="session-row">
                  <span>Evaluation unit</span>
                  <strong>Capture · {selected.capture_count} total</strong>
                </div>
                <div className="session-row">
                  <span>Protocol</span>
                  <strong>{selected.validation_protocol}</strong>
                </div>
                <div className="session-row">
                  <span>Window accuracy · secondary</span>
                  <strong>{percent(selected.window_accuracy)}</strong>
                </div>
                <p>{selected.research_caveat}</p>
                <a
                  className="button secondary"
                  href="/api/export/evidence/presence_model_comparison_by_bandwidth"
                >
                  <Download size={16} /> Export source metrics
                </a>
              </section>
            </div>
          )}
          <section className="panel">
            <h2>Keep the negative results.</h2>
            <div className="three-column">
              <div>
                <span className="mini-num orange-text">DSP</span>
                <h3>Smoother ≠ better.</h3>
                <p>
                  The earlier 15-tap FIR experiment did not improve RF capture
                  metrics and reduced Logistic Regression performance.
                </p>
              </div>
              <div>
                <span className="mini-num violet-text">SC</span>
                <h3>Promising, preliminary.</h3>
                <p>
                  Earlier GA + RF and fuzzy rules each reached 80% capture
                  accuracy on the small 20 MHz experiment. These are separate
                  historical runs.
                </p>
              </div>
              <div>
                <span className="mini-num cyan-text">DOMAIN</span>
                <h3>Context travels poorly.</h3>
                <p>
                  The hybrid beat both baselines in 1/12 presence directions and
                  4/12 activity directions. Transfer was domain-dependent.
                </p>
              </div>
            </div>
          </section>
          {fullTable(
            evidence.capture_level_model_predictions || [],
            "capture_level_model_predictions",
          )}
        </>
      )}
      {tab === "simulator" && (
        <>
          <Badge tone="amber">
            SIMULATOR · PARTIAL NS-3.40 RESEARCH IMPLEMENTATION
          </Badge>
          <h2 className="standalone-title">
            A network experiment. Its own kind of evidence.
          </h2>
          <Note>
            MAC sensing reports are not human-presence accuracy. BF report
            latency is not inference or application latency. Five runs per
            configuration are exploratory; workloads and topology layouts are
            not guaranteed identical.
          </Note>
          <div className="simulator-cards">
            {(evidence.ax_bf_simulation_summary || []).map((r: Dict) => (
              <section className="panel" key={r.configuration}>
                <Badge tone="muted">{r.runs} RUNS</Badge>
                <h2>{r.configuration}</h2>
                <div className="sim-value">
                  <span>BF sensing-report latency</span>
                  <strong>
                    {r.mean_bf_latency_ms
                      ? Number(r.mean_bf_latency_ms).toFixed(4)
                      : "—"}
                    <small>{r.mean_bf_latency_ms ? "ms" : "BF disabled"}</small>
                  </strong>
                </div>
                <div className="sim-value">
                  <span>AX user-data throughput</span>
                  <strong>
                    {r.mean_ax_throughput_mbps
                      ? Number(r.mean_ax_throughput_mbps).toFixed(4)
                      : "—"}
                    <small>
                      {r.mean_ax_throughput_mbps ? "Mbps" : "Not measured"}
                    </small>
                  </strong>
                </div>
              </section>
            ))}
          </div>
          <div className="two-column">
            <section className="panel">
              <h2>BF latency across configurations</h2>
              <Chart
                series={[
                  {
                    name: "BF report latency · ms",
                    data: (evidence.ax_bf_simulation_summary || [])
                      .filter((r: Dict) => r.mean_bf_latency_ms)
                      .map((r: Dict) => Number(r.mean_bf_latency_ms)),
                  },
                ]}
                axis="0 = BF-only · 1 = Mixed AX+BF"
                exportName="bf-latency"
              />
            </section>
            <section className="panel">
              <h2>What changed in mixed mode?</h2>
              <div className="metric-grid">
                <div className="metric-card">
                  <span>AX throughput below AX-only</span>
                  <strong>~1.10%</strong>
                </div>
                <div className="metric-card">
                  <span>BF report latency vs BF-only</span>
                  <strong>~9.4×</strong>
                </div>
              </div>
              <p>
                These describe this simulator configuration. They do not
                establish physical 802.11bf operation, standards conformance, or
                through-wall sensing.
              </p>
              <a
                className="button secondary"
                href="/api/export/evidence/ax_bf_simulation_runs"
              >
                <Download size={16} /> Download run-level CSV
              </a>
            </section>
          </div>
          {fullTable(
            evidence.ax_bf_simulation_summary || [],
            "ax_bf_simulation_summary",
          )}
        </>
      )}
      {tab === "domains" && (
        <>
          <Badge tone="muted">HISTORICAL DOMAIN TRANSFER</Badge>
          <h2 className="standalone-title">A new environment is a new test.</h2>
          <Note>
            LOS/NLOS and BQ/PIFA comparisons use saved domain experiments. A
            strong within-domain result does not prove transfer or physical
            through-wall detection.
          </Note>
          {fullTable(
            evidence.cross_domain_transfer_metrics || [],
            "cross_domain_transfer_metrics",
          )}
        </>
      )}
      {tab === "audit" && (
        <>
          <Badge tone="muted">SAVED DATA AUDIT</Badge>
          <h2 className="standalone-title">
            Check the inputs. Check the split.
          </h2>
          {fullTable(
            evidence.csi_capture_quality_audit || [],
            "csi_capture_quality_audit",
          )}
          <h2>Validation fold details</h2>
          {fullTable(
            evidence.model_validation_fold_details || [],
            "model_validation_fold_details",
          )}
          <a
            className="button secondary"
            href="/api/export/evidence/csi_window_quality_audit"
          >
            <Download size={16} /> Download window-level audit
          </a>
        </>
      )}
      {tab === "local" && (
        <>
          {state.runs.length ? (
            state.runs.map((r: Dict) => (
              <section className="panel" key={r.id}>
                <div className="panel-heading">
                  <div>
                    <Badge tone="muted">{r.source}</Badge>
                    <h2>{r.kind === "DSP" ? r.settings.operation : r.kind}</h2>
                    <p>{new Date(r.created).toLocaleString()}</p>
                  </div>
                  <a
                    className="button secondary"
                    href={"/api/export/run/" + r.id}
                  >
                    <Download size={16} /> Export CSV
                  </a>
                </div>
                <p>
                  {r.note ||
                    r.caveat ||
                    "Model evaluation stored in the local model shelf."}
                </p>
                <details>
                  <summary>Settings & provenance</summary>
                  <pre>{JSON.stringify(r, null, 2)}</pre>
                </details>
              </section>
            ))
          ) : (
            <section className="panel">
              <Empty
                icon={FlaskConical}
                title="Your notebook starts here."
                action={
                  <Button secondary onClick={() => navigate("dsp")}>
                    Open Signal Studio <ArrowRight size={16} />
                  </Button>
                }
              >
                Save a DSP experiment, train a model, or run inference to
                collect local research evidence.
              </Empty>
            </section>
          )}
        </>
      )}
    </>
  );
}
function ModesPage({
  navigate,
  evidence,
}: {
  navigate: (p: Page) => void;
  evidence: Dict;
}) {
  return (
    <>
      <div className="three-column mode-cards">
        {[
          {
            icon: Wifi,
            tone: "cyan",
            title: "Wi-Fi 6",
            sub: "802.11ax CSI",
            status: "RECORDED DATA",
            text: "Inspect supported recorded CSI, apply DSP, train models and replay compatible recordings.",
            limitation: "Live capture on the intended adapter is unverified.",
            action: "Explore recordings",
            page: "data",
          },
          {
            icon: Radio,
            tone: "amber",
            title: "802.11bf",
            sub: "Research & simulator",
            status: "SIMULATOR",
            text: "Inspect AX/BF simulator measurements and explore the recorded network-level tradeoffs.",
            limitation:
              "Physical BF hardware compatibility and standards conformance are unverified.",
            action: "View simulator evidence",
            page: "results",
          },
          {
            icon: GitBranch,
            tone: "violet",
            title: "Adaptive",
            sub: "Proposed architecture",
            status: "PROPOSED",
            text: "A research direction for selecting an available sensing interface based on context.",
            limitation: "No validated hardware switching logic is active.",
            action: "Review system status",
            page: "settings",
          },
        ].map((m) => (
          <section className={"panel mode-card " + m.tone} key={m.title}>
            <span className="mode-icon">
              <m.icon size={30} />
            </span>
            <Badge tone={m.tone}>{m.status}</Badge>
            <h2>{m.title}</h2>
            <span className="mode-subtitle">{m.sub}</span>
            <p>{m.text}</p>
            <Note>{m.limitation}</Note>
            <Button secondary onClick={() => navigate(m.page as Page)}>
              {m.action}
              <ArrowRight size={16} />
            </Button>
          </section>
        ))}
      </div>
      <section className="panel">
        <h2>Technology is one thing. Input source is another.</h2>
        <div className="source-legend">
          {[
            [
              "RECORDED DATA",
              "Actual imported CSI or saved research recordings.",
            ],
            ["MODEL OUTPUT", "An actual compatible model’s computed result."],
            [
              "SIMULATOR",
              "Network measurements from the recorded ns-3 experiments.",
            ],
            [
              "EDUCATIONAL DEMO",
              "An explicitly synthetic scientific teaching example.",
            ],
            [
              "PROPOSED",
              "A research plan awaiting implementation and validation.",
            ],
            [
              "UNVERIFIED",
              "A hardware or sensing capability that has not been tested.",
            ],
          ].map(([a, b]) => (
            <div key={a}>
              <Badge tone="muted">{a}</Badge>
              <p>{b}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="panel">
        <h2>Research references</h2>
        <div className="reference-list">
          {[
            ["CSI dataset · Zenodo", "https://zenodo.org/records/17225694"],
            [
              "SHARPax reference implementation",
              "https://github.com/francescamen/SHARPax",
            ],
            [
              "Integrated sensing and communications · Meneghello et al.",
              "https://doi.org/10.1109/MCOM.001.2200806",
            ],
            [
              "ns-3 BF research implementation",
              "https://github.com/idolumbantobing/IEEE_802.11bf",
            ],
            [
              "Project repository",
              "https://github.com/Sahil-droid-spec/wifi6-csi-human-detection",
            ],
          ].map(([l, u]) => (
            <a key={u} href={u} target="_blank" rel="noreferrer">
              {l}
              <ExternalLink size={15} />
            </a>
          ))}
        </div>
      </section>
    </>
  );
}
function MediaPage({
  state,
  capture,
  selected,
  choose,
  navigate,
  notify,
  refresh,
}: Common) {
  const input = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [title, setTitle] = useState("");
  const [notes, setNotes] = useState("");
  const [dataset, setDataset] = useState("");
  const [captureId, setCaptureId] = useState("");
  const [progress, setProgress] = useState(-1);
  const [message, setMessage] = useState("");
  const [filter, setFilter] = useState("all");
  const [search, setSearch] = useState("");
  const [drag, setDrag] = useState(false);
  const xhr = useRef<XMLHttpRequest | null>(null);
  const send = () => {
    if (!file) return;
    const data = new FormData();
    data.append("file", file);
    data.append("title", title || file.name);
    data.append("notes", notes);
    data.append("dataset_id", dataset);
    data.append("capture_id", captureId);
    const request = new XMLHttpRequest();
    xhr.current = request;
    request.open("POST", "/api/media");
    setProgress(0);
    setMessage("");
    request.upload.onprogress = (e) => {
      if (e.lengthComputable)
        setProgress(Math.round((e.loaded / e.total) * 100));
    };
    request.onload = async () => {
      setProgress(-1);
      if (request.status >= 200 && request.status < 300) {
        setMessage("Saved to your recording library.");
        setFile(null);
        setTitle("");
        setNotes("");
        await refresh();
      } else {
        try {
          setMessage(JSON.parse(request.responseText).detail);
        } catch {
          setMessage("Upload failed. Please retry.");
        }
      }
    };
    request.onerror = () => {
      setProgress(-1);
      setMessage("Connection interrupted. Reconnect and retry.");
    };
    request.onabort = () => setProgress(-1);
    request.send(data);
  };
  const items = (state.media || []).filter(
    (m: Dict) =>
      (filter === "all" || m.type.startsWith(filter)) &&
      (m.title + " " + m.notes).toLowerCase().includes(search.toLowerCase()),
  );
  return (
    <>
      <div className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <Badge tone="green">LOCAL RECORDING LIBRARY</Badge>
              <h2>Keep the context with the signal.</h2>
            </div>
            <FolderOpen size={26} />
          </div>
          <p>
            Store experiment videos, photos and audio alongside your CSI
            recordings. These files are references, not radio measurements.
          </p>
          <div
            className={"dropzone " + (drag ? "drag" : "")}
            onDragOver={(e) => {
              e.preventDefault();
              setDrag(true);
            }}
            onDragLeave={() => setDrag(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDrag(false);
              const next = e.dataTransfer.files[0];
              if (next) {
                setFile(next);
                setTitle(next.name);
              }
            }}
          >
            <input
              ref={input}
              type="file"
              hidden
              accept="image/jpeg,image/png,image/webp,image/gif,video/mp4,video/quicktime,video/webm,audio/wav,audio/mpeg"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  setFile(f);
                  setTitle(f.name);
                }
                e.target.value = "";
              }}
            />
            <FileUp size={30} />
            <h3>{file ? file.name : "Drop a photo, video or audio file"}</h3>
            <p>JPG · PNG · WebP · GIF · MP4 · MOV · WebM · WAV · MP3</p>
            <Button
              secondary
              disabled={progress >= 0}
              onClick={() => input.current?.click()}
            >
              Choose recording
            </Button>
            <small>Stored on this laptop · up to 1 GiB per file</small>
          </div>
        </section>
        <section className="panel">
          <h2>Give this recording a home.</h2>
          <div className="control-grid">
            <label className="wide">
              Title
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={160}
                placeholder="e.g. Classroom experiment — one person"
              />
            </label>
            <label>
              Dataset (optional)
              <select
                value={dataset}
                onChange={(e) => {
                  setDataset(e.target.value);
                  setCaptureId("");
                }}
              >
                <option value="">General experiment library</option>
                {state.datasets.map((d: Dict) => (
                  <option key={d.id} value={d.id}>
                    {d.name}
                  </option>
                ))}
              </select>
            </label>
            <label>
              CSI capture (optional)
              <select
                value={captureId}
                onChange={(e) => setCaptureId(e.target.value)}
              >
                <option value="">No specific capture</option>
                {state.captures
                  .filter((c: Dict) => !dataset || c.dataset_id === dataset)
                  .map((c: Dict) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
              </select>
            </label>
            <label className="wide">
              Experiment notes
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                maxLength={2000}
                rows={4}
                placeholder="Location, people, activity, and anything useful for your presentation."
              />
            </label>
          </div>
          {progress >= 0 ? (
            <div className="media-progress">
              <progress value={progress} max={100} />
              <span>{progress}% uploaded</span>
              <Button secondary onClick={() => xhr.current?.abort()}>
                Cancel
              </Button>
            </div>
          ) : (
            <Button disabled={!file} onClick={send}>
              <Upload size={16} /> Save to recording library
            </Button>
          )}
          {message && (
            <p className="upload-feedback" role="status">
              {message}
            </p>
          )}
        </section>
      </div>
      <div className="section-heading">
        <h2>
          Your recordings{" "}
          <span className="count">{state.media?.length || 0}</span>
        </h2>
        <button className="text-button" onClick={() => navigate("settings")}>
          <Smartphone size={16} /> Send from phone
        </button>
      </div>
      <div className="filter-bar">
        <div className="search-field">
          <Search size={16} />
          <input
            placeholder="Search saved recordings…"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
        </div>
        <select
          aria-label="Media type"
          value={filter}
          onChange={(e) => setFilter(e.target.value)}
        >
          <option value="all">All recordings</option>
          <option value="image">Photos</option>
          <option value="video">Videos</option>
          <option value="audio">Audio</option>
        </select>
      </div>
      {items.length ? (
        <div className="media-grid">
          {items.map((m: Dict) => (
            <section className="panel media-card" key={m.id}>
              <div className="media-preview">
                {m.type.startsWith("image") ? (
                  <img
                    src={"/api/media/" + m.id + "/file"}
                    alt={m.title}
                    loading="lazy"
                  />
                ) : m.type.startsWith("video") ? (
                  <video
                    controls
                    playsInline
                    preload="metadata"
                    src={"/api/media/" + m.id + "/file"}
                  />
                ) : (
                  <audio
                    controls
                    preload="metadata"
                    src={"/api/media/" + m.id + "/file"}
                  />
                )}
              </div>
              <div className="media-description">
                <Badge tone="muted">{m.type.split("/")[0].toUpperCase()}</Badge>
                <h3>{m.title}</h3>
                <p>{m.notes || "No notes added."}</p>
                <small>
                  {(m.size / 1024 ** 2).toFixed(1)} MiB ·{" "}
                  {new Date(m.created).toLocaleString()}
                </small>
                <div className="button-row">
                  {m.capture_id && (
                    <Button
                      secondary
                      onClick={() => {
                        choose(m.capture_id);
                        navigate("replay");
                      }}
                    >
                      Open paired capture <Play size={14} />
                    </Button>
                  )}
                  <a
                    className="text-button"
                    href={"/api/media/" + m.id + "/file"}
                    target="_blank"
                    rel="noreferrer"
                  >
                    Open original <ExternalLink size={14} />
                  </a>
                </div>
              </div>
            </section>
          ))}
        </div>
      ) : (
        <section className="panel">
          <Empty icon={FolderOpen} title="A place for the whole experiment.">
            Your uploaded videos, images and audio recordings will stay here,
            with optional links to their CSI dataset.
          </Empty>
        </section>
      )}
    </>
  );
}

function SettingsPage({
  notify,
  logout,
}: {
  notify: (s: string) => void;
  logout: () => void;
}) {
  const [server, setServer] = useState<Dict | null>(null);
  const [downloads, setDownloads] = useState<Dict[]>([]);
  useEffect(() => {
    const load = async () => {
      try {
        const [server, catalog] = await Promise.all([
          api("server"),
          api("downloads"),
        ]);
        setServer(server);
        setDownloads(catalog);
      } catch {}
    };
    load();
    const timer = setInterval(load, 5000);
    return () => clearInterval(timer);
  }, []);
  return (
    <>
      {downloads.length > 0 && (
        <section className="panel">
          <div className="panel-heading">
            <div>
              <Badge tone="green">PHONE & LAPTOP DOWNLOADS</Badge>
              <h2>Take Orbit with you.</h2>
              <p>
                The Android companion connects to the laptop server. Use the
                small CSI archive to rehearse a real file transfer.
              </p>
            </div>
            <Download size={24} />
          </div>
          <div className="download-grid">
            {downloads.map((file: Dict) => (
              <a className="download-card" key={file.name} href={file.url}>
                <span>{file.title}</span>
                <strong>{file.name}</strong>
                <small>
                  {(file.size / 1024 ** 2).toFixed(1)} MiB{" "}
                  <Download size={14} />
                </small>
              </a>
            ))}
          </div>
        </section>
      )}
      <div className="two-column">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <Badge tone={server?.enabled ? "green" : "muted"}>
                {server?.enabled ? "LAN ENABLED" : "LAPTOP ONLY"}
              </Badge>
              <h2>One lab. Two screens.</h2>
            </div>
            <Smartphone size={27} />
          </div>
          <div className="sharing-control">
            <span>
              {server?.enabled ? "Phone sharing is on" : "Phone sharing is off"}
            </span>
            <Button
              secondary
              onClick={async () => {
                try {
                  setServer(
                    await api("server/sharing", { enabled: !server?.enabled }),
                  );
                } catch (e: any) {
                  notify(e.message);
                }
              }}
            >
              {server?.enabled ? "Switch sharing off" : "Enable phone sharing"}
            </Button>
          </div>
          <p className="helper">
            To start LAN mode after a laptop-only launch, double-click{" "}
            <b>Start-Orbit-Server.cmd</b> in the app folder.
          </p>
          <p>
            Connect your phone and laptop to the same trusted Wi-Fi network.
            Open the laptop’s LAN address, enter the terminal access code, and
            send a recording.
          </p>
          {server?.enabled && server.addresses.length ? (
            <>
              <div className="qr-layout">
                <img
                  src="/api/qr"
                  alt="QR code for the laptop phone upload address"
                />
                <div>
                  <span className="tiny-label">SCAN TO UPLOAD</span>
                  <p>
                    No cloud hand-off. Your phone sends the file directly to
                    this laptop.
                  </p>
                </div>
              </div>
              {server.addresses.map((address: string) => (
                <div className="address-row" key={address}>
                  <code>{address}</code>
                  <button
                    className="text-button"
                    onClick={() =>
                      navigator.clipboard
                        .writeText(address)
                        .then(() => notify("LAN address copied."))
                        .catch(() =>
                          notify("Select and copy the displayed address."),
                        )
                    }
                  >
                    Copy
                  </button>
                </div>
              ))}
            </>
          ) : (
            <div className="setup-card">
              <Network size={28} />
              <h3>Enable trusted-LAN access.</h3>
              <p>Stop the local server, then start Orbit with:</p>
              <code>python -m orbit --lan</code>
              <p>
                A LAN address and QR code appear here after reconnecting. Allow
                Python through Windows Firewall on private networks if prompted.
              </p>
            </div>
          )}
          <Note>
            This server is for a trusted private network. Do not forward its
            port or publish a public tunnel. A physical phone transfer still
            needs to be verified on your network.
          </Note>
        </section>
        <section className="panel">
          <Badge tone="green">LOCAL PROCESSING</Badge>
          <h2>The details that matter.</h2>
          <div className="metadata-grid">
            {[
              ["Workspace", server?.local_url || "Connecting…"],
              ["Upload limit", `${server?.max_upload_mib || 256} MiB`],
              ["Storage", server?.storage || "Connecting…"],
              ["Model storage", "Internal artifacts only"],
              ["Analysis", "CPU · Python / NumPy / SciPy"],
              ["Live hardware", "Unverified · unavailable"],
            ].map(([l, v]) => (
              <div key={l}>
                <span>{l}</span>
                <strong>{v}</strong>
              </div>
            ))}
          </div>
          <p>
            Imports, jobs, experiments and model manifests persist on this
            laptop. All connected devices share the same library. The access
            code changes on every restart.
          </p>
          <Button secondary onClick={logout}>
            <LockKeyhole size={16} /> Disconnect this browser
          </Button>
        </section>
      </div>
      <section className="panel">
        <h2>A quick guide to your first experiment.</h2>
        <div className="three-column">
          <div>
            <span className="mini-num">01</span>
            <h3>Bring a recording</h3>
            <p>
              Upload a supported .mat or ZIP dataset. Use config.json for
              bandwidth, modulation and presence labels.
            </p>
          </div>
          <div>
            <span className="mini-num">02</span>
            <h3>Explore the signal</h3>
            <p>
              Inspect valid packets and feature windows. Compare filter outputs
              and spectra in Signal Studio.
            </p>
          </div>
          <div>
            <span className="mini-num">03</span>
            <h3>Earn a verdict</h3>
            <p>
              Train on labelled, independent captures, inspect held-out results,
              then run a compatible model in Replay.
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
createRoot(document.getElementById("root")!).render(<App />);
