import {
  Component,
  Suspense,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import {
  BufferGeometry,
  CanvasTexture,
  Color,
  Group,
  Line,
  LineBasicMaterial,
  Vector3,
} from "three";
import "./spatial-scene.css";

export type SceneFrame = {
  time: number;
  scenario: string;
  positions?: number[][];
  playing: boolean;
  reduced: boolean;
  source: string;
  packet?: number;
  trails?: number[][][];
  activity?: number;
};
type Palette = {
  background: string;
  surface: string;
  text: string;
  muted: string;
  blue: string;
  cyan: string;
  line: string;
};
type Options = {
  grid: boolean;
  axes: boolean;
  room: boolean;
  signals: boolean;
  labels: boolean;
  people: boolean;
  quality: string;
  style: string;
  preset: string;
  reset: number;
  width: number;
  depth: number;
  tx: number;
  rx: number;
  pan: number;
  zoom: number;
  floor: boolean;
  joints: boolean;
  particles: boolean;
  scan: boolean;
  trails: boolean;
  markers: boolean;
  environment: string;
  pose: string;
};
const initial: Options = {
  grid: true,
  axes: false,
  room: true,
  signals: true,
  labels: true,
  people: true,
  quality: "balanced",
  style: "hologram",
  preset: "perspective",
  reset: 0,
  width: 7,
  depth: 5,
  tx: -2.8,
  rx: 2.8,
  pan: 0,
  zoom: 1,
  floor: true,
  joints: true,
  particles: true,
  scan: false,
  trails: true,
  markers: true,
  environment: "open",
  pose: "scenario",
};
function palette(): Palette {
  const s = getComputedStyle(document.documentElement),
    v = (key: string, fallback: string) =>
      s.getPropertyValue("--" + key).trim() || fallback;
  return {
    background: v("bg", "#f5f7fc"),
    surface: v("surface", "#ffffff"),
    text: v("text", "#18263c"),
    muted: v("muted", "#5e697b"),
    blue: v("blue", "#0072b2"),
    cyan: v("cyan", "#009e73"),
    line: v("line", "#b8c3d4"),
  };
}

class SceneBoundary extends Component<
  { children: ReactNode; onFail: () => void },
  { failed: boolean }
> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  componentDidCatch() {
    this.props.onFail();
  }
  render() {
    return this.state.failed ? null : this.props.children;
  }
}
function ContextGuard({onLoss}:{onLoss:()=>void}){const {gl}=useThree();useEffect(()=>{const handler=(event:Event)=>{event.preventDefault();onLoss();};gl.domElement.addEventListener('webglcontextlost',handler);return()=>gl.domElement.removeEventListener('webglcontextlost',handler);},[gl,onLoss]);return null;}
function Controls({ options }: { options: Options }) {
  const { camera, gl, invalidate } = useThree();
  const ref = useRef<OrbitControls | null>(null);
  useEffect(() => {
    const c = new OrbitControls(camera, gl.domElement);
    c.target.set(0, 1, 0);
    c.enableDamping = true;
    c.dampingFactor = 0.08;
    c.minDistance = 2;
    c.maxDistance = 24;
    c.maxPolarAngle = Math.PI * 0.49;
    ref.current = c;
    return () => {
      c.dispose();
      ref.current = null;
    };
  }, [camera, gl]);
  useEffect(() => {
    const p: Record<string, number[]> = {
      perspective: [5, 3.8, 6],
      human: [3.2, 2.7, 4.2],
      top: [0.001, 12, 0.001],
      front: [0, 2.5, 10],
      side: [10, 2.5, 0],
    };
    camera.position.fromArray(p[options.preset] || p.perspective);
    ref.current?.target.set(0, 1, 0);
    ref.current?.update();
    invalidate();
  }, [options.preset, options.reset, camera, invalidate]);
  const lastPan = useRef(options.pan);
  useEffect(() => {
    const shift = options.pan - lastPan.current;
    lastPan.current = options.pan;
    camera.position.x += shift;
    if (ref.current) ref.current.target.x += shift;
    ref.current?.update();
  }, [options.pan, camera]);
  useEffect(() => {
    camera.zoom = options.zoom;
    camera.updateProjectionMatrix();
  }, [options.zoom, camera]);
  useFrame(() => ref.current?.update());
  return null;
}
function Limb({
  position,
  rotation,
  color,
  wire,
  joints,
  length = 0.5,
}: {
  position: [number, number, number];
  rotation?: [number, number, number];
  color: string;
  wire: boolean;
  joints: boolean;
  length?: number;
}) {
  return (
    <group position={position} rotation={rotation}>
      <mesh position={[0, -length / 2, 0]}>
        <capsuleGeometry args={[0.075, length - 0.15, 5, 12]} />
        <meshStandardMaterial
          color={color}
          roughness={0.36}
          metalness={0.35}
          wireframe={wire}
        />
      </mesh>
      {joints && (
        <mesh>
          <sphereGeometry args={[0.085, 12, 10]} />
          <meshStandardMaterial color={color} />
        </mesh>
      )}
    </group>
  );
}
function Person({
  position,
  phase,
  style,
  color,
  moving,
  joints,
}: {
  position: number[];
  phase: number;
  style: string;
  color: string;
  moving: boolean;
  joints: boolean;
}) {
  const swing = moving ? Math.sin(phase * 5) * 0.65 : 0,
    wire = style === "wireframe";
  return (
    <group
      position={[position[0] || 0, 0, position[1] || 0]}
      rotation={[0, position[2] || 0, 0]}
    >
      <mesh position={[0, 1.78, 0]}>
        <sphereGeometry args={[0.17, 24, 20]} />
        <meshStandardMaterial
          color={color}
          wireframe={wire}
          metalness={0.35}
          roughness={0.3}
        />
      </mesh>
      <mesh position={[0, 1.58, 0]}>
        <cylinderGeometry args={[0.075, 0.09, 0.17, 16]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, 1.01, 0]} scale={[1, 0.65, 0.7]}>
        <sphereGeometry args={[0.24, 20, 16]} />
        <meshStandardMaterial color={color} wireframe={wire} />
      </mesh>
      {[-1, 1].map((sign) => (
        <mesh key={"eye" + sign} position={[sign * 0.059, 1.81, 0.148]}>
          <sphereGeometry args={[0.018, 10, 8]} />
          <meshStandardMaterial
            color={color}
            emissive={color}
            emissiveIntensity={0.7}
          />
        </mesh>
      ))}
      <mesh position={[0, 1.37, 0]} scale={[1, 0.95, 0.6]}>
        <capsuleGeometry args={[0.22, 0.3, 8, 20]} />
        <meshStandardMaterial
          color={color}
          wireframe={wire}
          transparent={style === "hologram"}
          opacity={style === "hologram" ? 0.7 : 1}
          metalness={0.4}
          roughness={0.35}
        />
      </mesh>
      <Limb
        position={[-0.29, 1.53, 0]}
        rotation={[swing, 0, -0.08]}
        color={color}
        wire={wire}
        joints={joints}
      />
      <Limb
        position={[0.29, 1.53, 0]}
        rotation={[-swing, 0, 0.08]}
        color={color}
        wire={wire}
        joints={joints}
      />
      <group position={[-0.29, 1.53, 0]} rotation={[swing, 0, -0.08]}>
        <Limb
          position={[0, -0.5, 0]}
          rotation={[-0.2, 0, 0]}
          length={0.36}
          color={color}
          wire={wire}
          joints={joints}
        />
      </group>
      <group position={[0.29, 1.53, 0]} rotation={[-swing, 0, 0.08]}>
        <Limb
          position={[0, -0.5, 0]}
          rotation={[-0.2, 0, 0]}
          length={0.36}
          color={color}
          wire={wire}
          joints={joints}
        />
      </group>
      {[-1, 1].map((sign) => (
        <group
          key={sign}
          position={[sign * 0.13, 1.03, 0]}
          rotation={[sign * swing * 0.7, 0, 0]}
        >
          <Limb
            position={[0, 0, 0]}
            length={0.48}
            color={color}
            wire={wire}
            joints={joints}
          />
          <group
            position={[0, -0.48, 0]}
            rotation={[Math.max(0, -sign * swing), 0, 0]}
          >
            <Limb
              position={[0, 0, 0]}
              length={0.46}
              color={color}
              wire={wire}
              joints={joints}
            />
            <mesh position={[0, -0.44, 0.07]}>
              <boxGeometry args={[0.16, 0.1, 0.29]} />
              <meshStandardMaterial color={color} wireframe={wire} />
            </mesh>
          </group>
        </group>
      ))}
      {style === "hologram" &&
        Array.from({ length: 15 }, (_, i) => (
          <mesh
            key={i}
            position={[0, 0.15 + i * 0.115, 0]}
            rotation={[-Math.PI / 2, 0, 0]}
          >
            <ringGeometry args={[0.25, 0.256, 48]} />
            <meshBasicMaterial
              color={color}
              transparent
              opacity={0.35}
              depthWrite={false}
            />
          </mesh>
        ))}
    </group>
  );
}
function NodeLabel({
  text,
  x,
  colors,
}: {
  text: string;
  x: number;
  colors: Palette;
}) {
  const texture = useMemo(() => {
    const c = document.createElement("canvas");
    c.width = 256;
    c.height = 64;
    const ctx = c.getContext("2d")!;
    ctx.fillStyle = colors.surface;
    ctx.fillRect(0, 0, 256, 64);
    ctx.strokeStyle = colors.line;
    ctx.strokeRect(1, 1, 254, 62);
    ctx.fillStyle = colors.text;
    ctx.font = "bold 30px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(text, 128, 43);
    return new CanvasTexture(c);
  }, [text, colors]);
  useEffect(() => () => texture.dispose(), [texture]);
  return (
    <sprite position={[x, 1.08, 0]} scale={[0.88, 0.22, 1]}>
      <spriteMaterial map={texture} transparent depthTest={false} />
    </sprite>
  );
}
function Beacon({ x, color }: { x: number; color: string }) {
  return (
    <group position={[x, 0, 0]}>
      <mesh position={[0, 0.18, 0]}>
        <cylinderGeometry args={[0.15, 0.22, 0.35, 24]} />
        <meshStandardMaterial color={color} metalness={0.5} roughness={0.3} />
      </mesh>
      <mesh position={[0, 0.55, 0]}>
        <cylinderGeometry args={[0.018, 0.018, 0.45, 10]} />
        <meshStandardMaterial color={color} />
      </mesh>
      <mesh position={[0, 0.8, 0]}>
        <sphereGeometry args={[0.055, 12, 12]} />
        <meshBasicMaterial color={color} />
      </mesh>
    </group>
  );
}
function Trail({ points, color }: { points: number[][]; color: string }) {
  const object = useMemo(
    () =>
      new Line(
        new BufferGeometry(),
        new LineBasicMaterial({ color, transparent: true, opacity: 0.65 }),
      ),
    [color],
  );
  useEffect(() => {
    object.geometry.dispose();
    object.geometry = new BufferGeometry().setFromPoints(
      points.map((p) => new Vector3(p[0], 0.03, p[1])),
    );
  }, [points, object]);
  useEffect(
    () => () => {
      object.geometry.dispose();
      object.material.dispose();
    },
    [object],
  );
  return <primitive object={object} dispose={null} />;
}
function World({
  frame,
  options,
  colors,
  onFps,
}: {
  frame: SceneFrame;
  options: Options;
  colors: Palette;
  onFps: (fps: number) => void;
}) {
  const signals = useRef<Group>(null),
    particles = useRef<Group>(null),
    scan = useRef<Group>(null),
    stats = useRef({ elapsed: 0, frames: 0 });
  useFrame((_, dt) => {
    stats.current.elapsed += dt;
    stats.current.frames++;
    if (stats.current.elapsed >= 1) {
      onFps(Math.round(stats.current.frames / stats.current.elapsed));
      stats.current = { elapsed: 0, frames: 0 };
    }
    if (particles.current)
      particles.current.rotation.y = frame.reduced ? 0 : frame.time * 0.06;
    if (scan.current)
      scan.current.position.x = frame.reduced
        ? 0
        : Math.sin(frame.time * 0.5) * options.width * 0.42;
    if (signals.current)
      signals.current.children.forEach((child, i) => {
        const scale = frame.reduced
          ? 1 + i * 0.24
          : 0.3 + ((frame.time * 0.7 + i * 0.24) % 1) * 1.9;
        child.scale.setScalar(scale);
      });
  });
  const moving = ["walking", "two", "crossing", "moving"].includes(
      frame.scenario,
    ),
    count =
      frame.scenario === "empty"
        ? 0
        : frame.scenario === "two" || frame.scenario === "crossing"
          ? 2
          : 1;
  const positions =
    frame.positions ||
    Array.from({ length: count }, (_, i) => [i ? 1 : -0.3, 0, 0]);
  return (
    <>
      <color attach="background" args={[new Color(colors.background)]} />
      <ambientLight intensity={1.8} />
      <directionalLight position={[3, 7, 5]} intensity={3} />
      <pointLight position={[-3, 3, -2]} color={colors.blue} intensity={15} />
      <Controls options={options} />
      {options.floor && (
        <mesh
          rotation={[-Math.PI / 2, 0, 0]}
          position={[0, -0.035, 0]}
          receiveShadow
        >
          <planeGeometry args={[options.width + 2, options.depth + 2]} />
          <meshStandardMaterial color={colors.surface} roughness={0.95} />
        </mesh>
      )}
      {options.grid && (
        <gridHelper
          args={[
            Math.max(options.width, options.depth) + 1,
            16,
            colors.muted,
            colors.line,
          ]}
          position={[0, -0.015, 0]}
        />
      )}
      {options.axes && <axesHelper args={[2]} />}
      {options.room && (
        <group>
          <mesh position={[0, 1.5, -options.depth / 2]}>
            <boxGeometry args={[options.width, 3, 0.055]} />
            <meshStandardMaterial
              color={colors.blue}
              transparent
              opacity={0.13}
              depthWrite={false}
              side={2}
            />
          </mesh>
          <mesh position={[-options.width / 2, 1.5, 0]}>
            <boxGeometry args={[0.055, 3, options.depth]} />
            <meshStandardMaterial
              color={colors.blue}
              transparent
              opacity={0.1}
              depthWrite={false}
              side={2}
            />
          </mesh>
          <mesh position={[0, 0.015, 0]} rotation={[-Math.PI / 2, 0, 0]}>
            <ringGeometry args={[0.015, 0.02, 32]} />
            <meshBasicMaterial color={colors.blue} />
          </mesh>
        </group>
      )}
      {options.markers && (
        <>
          <Beacon x={options.tx} color={colors.blue} />
          <Beacon x={options.rx} color={colors.cyan} />
        </>
      )}
      {options.labels && options.markers && (
        <>
          <NodeLabel text="TX" x={options.tx} colors={colors} />
          <NodeLabel text="RX" x={options.rx} colors={colors} />
        </>
      )}
      {options.signals && (
        <group ref={signals} position={[options.tx, 0.15, 0]}>
          {[0, 1, 2, 3].map((i) => (
            <mesh key={i} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[0.98, 1, 64]} />
              <meshBasicMaterial
                color={colors.blue}
                transparent
                opacity={0.12 + Math.min(0.3, (frame.activity || 0) * 0.04)}
                depthWrite={false}
              />
            </mesh>
          ))}
        </group>
      )}
      {options.trails &&
        frame.trails?.map((points, i) => (
          <Trail
            key={i}
            points={points}
            color={i ? colors.blue : colors.cyan}
          />
        ))}
      {options.scan && (
        <group ref={scan}>
          <mesh position={[0, 1.2, 0]} rotation={[0, Math.PI / 2, 0]}>
            <planeGeometry args={[options.depth, 2.4]} />
            <meshBasicMaterial
              color={colors.blue}
              transparent
              opacity={0.08}
              side={2}
              depthWrite={false}
            />
          </mesh>
        </group>
      )}
      {options.particles && (
        <group ref={particles}>
          {Array.from(
            { length: options.quality === "low" ? 24 : 64 },
            (_, i) => (
              <mesh
                key={i}
                position={[
                  Math.sin(i * 12.98) * 2.6,
                  0.15 + (((i * 37) % 100) / 100) * 2.2,
                  Math.cos(i * 7.12) * 1.8,
                ]}
              >
                <sphereGeometry args={[0.012, 5, 4]} />
                <meshBasicMaterial
                  color={colors.cyan}
                  transparent
                  opacity={0.35}
                />
              </mesh>
            ),
          )}
        </group>
      )}
      {options.environment !== "open" && (
        <group>
          {[-1, 1].map((sign) => (
            <group
              key={sign}
              position={[sign * 2, 0, -options.depth / 2 + 0.6]}
            >
              <mesh position={[0, 0.83, 0]}>
                <boxGeometry args={[1.4, 0.1, 0.7]} />
                <meshStandardMaterial color={colors.surface} roughness={0.5} />
              </mesh>
              {[-0.55, 0.55].map((x) => (
                <mesh key={x} position={[x, 0.4, 0]}>
                  <boxGeometry args={[0.07, 0.8, 0.5]} />
                  <meshStandardMaterial color={colors.muted} />
                </mesh>
              ))}
              {options.environment === "lab" && (
                <mesh position={[0, 1.03, 0]}>
                  <boxGeometry args={[0.4, 0.3, 0.3]} />
                  <meshStandardMaterial
                    color={colors.blue}
                    metalness={0.4}
                    roughness={0.5}
                  />
                </mesh>
              )}
            </group>
          ))}
        </group>
      )}
      {options.people &&
        positions.map((p, i) => (
          <Person
            key={i}
            position={p}
            phase={frame.reduced ? 0 : frame.time + i}
            style={options.style}
            color={i ? colors.blue : colors.cyan}
            moving={moving && options.pose === "scenario"}
            joints={options.joints}
          />
        ))}
    </>
  );
}
export default function SpatialScene({ frame }: { frame: SceneFrame }) {
  const [options, setOptions] = useState(initial),
    [colors, setColors] = useState(palette),
    [fps, setFps] = useState(0),
    [failed, setFailed] = useState(false),
    [message, setMessage] = useState(""),
    [recording, setRecording] = useState(false);
  const root = useRef<HTMLDivElement>(null),
    canvas = useRef<HTMLCanvasElement | null>(null),
    recorder = useRef<MediaRecorder | null>(null),
    recordTimer = useRef<ReturnType<typeof setTimeout> | null>(null),
    stream = useRef<MediaStream | null>(null),
    recordFrame = useRef(0),
    frameRef = useRef(frame);
  frameRef.current = frame;
  useEffect(() => {
    const sync = () => setColors(palette());
    window.addEventListener("orbit-theme", sync);
    const observer = new MutationObserver(sync);
    observer.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme", "style"],
    });
    return () => {
      window.removeEventListener("orbit-theme", sync);
      observer.disconnect();
    };
  }, []);
  useEffect(
    () => () => {
      cancelAnimationFrame(recordFrame.current);
      if (recordTimer.current) clearTimeout(recordTimer.current);
      if (recorder.current?.state === "recording") recorder.current.stop();
      stream.current?.getTracks().forEach((t) => t.stop());
    },
    [],
  );
  useEffect(()=>{if(failed&&recorder.current?.state==='recording')recorder.current.stop();},[failed]);
  const update = <K extends keyof Options>(key: K, value: Options[K]) =>
    setOptions((o) => ({ ...o, [key]: value }));
  const download = (blob: Blob, name: string) => {
    const url = URL.createObjectURL(blob),
      a = document.createElement("a");
    a.href = url;
    a.download = name;
    a.click();
    setTimeout(() => URL.revokeObjectURL(url), 30000);
  };
  const drawExport = (target: HTMLCanvasElement) => {
    const original = canvas.current;
    if (!original) return;
    target.width = original.width;
    target.height = original.height + 76;
    const ctx = target.getContext("2d");
    if (!ctx) return;
    ctx.fillStyle = colors.surface;
    ctx.fillRect(0, 0, target.width, target.height);
    ctx.drawImage(original, 0, 48);
    ctx.fillStyle = colors.text;
    ctx.font = "16px sans-serif";
    ctx.fillText(
      "ORBIT · " +
        frameRef.current.source +
        " · " +
        (frameRef.current.packet === undefined
          ? "Illustration"
          : "Packet " + frameRef.current.packet),
      18,
      29,
    );
    ctx.font = "12px sans-serif";
    ctx.fillText(
      "Procedural visualization. Not a recovered human pose or measured position.",
      18,
      target.height - 10,
    );
  };
  const saveImage = () => {
    const target = document.createElement("canvas");
    drawExport(target);
    target.toBlob((b) => {
      if (b)
        download(
          b,
          "Orbit-" + frame.source.replaceAll(" ", "-") + "-scene.png",
        );
    });
  };
  const record = () => {
    if (recording) {
      recorder.current?.stop();
      return;
    }
    try {
      if (!canvas.current?.captureStream || !window.MediaRecorder)
        throw Error(
          "This browser cannot record the scene. Use Save image instead.",
        );
      const target = document.createElement("canvas");
      drawExport(target);
      const animate = () => {
        drawExport(target);
        recordFrame.current = requestAnimationFrame(animate);
      };
      recordFrame.current = requestAnimationFrame(animate);
      const s = target.captureStream(30);
      stream.current = s;
      const r = new MediaRecorder(s),
        chunks: BlobPart[] = [];
      recorder.current = r;
      r.ondataavailable = (e) => {
        if (e.data.size) chunks.push(e.data);
      };
      r.onstop = () => {
        cancelAnimationFrame(recordFrame.current);
        download(
          new Blob(chunks, { type: r.mimeType }),
          "Orbit-" + frame.source.replaceAll(" ", "-") + "-scene.webm",
        );
        s.getTracks().forEach((t) => t.stop());
        if (recordTimer.current) clearTimeout(recordTimer.current);
        setRecording(false);
      };
      r.start();
      recordTimer.current = setTimeout(() => {
        if (r.state === "recording") r.stop();
      }, 60000);
      setRecording(true);
      setMessage(
        "Recording this visualization only, without microphone or camera. Stops after 60 seconds.",
      );
    } catch (e) {
      setMessage((e as Error).message);
    }
  };
  return (
    <section
      className="spatial-studio"
      ref={root}
      aria-label="Interactive WebGL 3D sensing environment"
    >
      <div className="spatial-toolbar">
        <span className="spatial-chip">
          {failed ? "2D fallback" : "WEBGL · 3D"}
        </span>
        {["perspective", "human", "top", "front", "side"].map((v) => (
          <button
            key={v}
            title={
              "Move the 3D camera to the " +
              v +
              " view. Drag to orbit; right-drag or two-finger drag to pan; scroll to zoom."
            }
            aria-pressed={options.preset === v}
            onClick={() => update("preset", v)}
          >
            {v}
          </button>
        ))}
        <button
          title="Restore the camera position without changing data."
          onClick={() =>
            setOptions((o) => ({ ...o, reset: o.reset + 1, zoom: 1 }))
          }
        >
          Reset view
        </button>
        <button
          title="Zoom the actual perspective camera closer. Scroll or pinch also zooms."
          onClick={() => update("zoom", Math.min(3, options.zoom + 0.2))}
        >
          Zoom +
        </button>
        <button
          title="Zoom the actual perspective camera farther away."
          onClick={() => update("zoom", Math.max(0.5, options.zoom - 0.2))}
        >
          Zoom −
        </button>
        <button
          title="Pan camera and target left in world coordinates."
          onClick={() => update("pan", options.pan - 0.4)}
        >
          Pan ←
        </button>
        <button
          title="Pan camera and target right in world coordinates."
          onClick={() => update("pan", options.pan + 0.4)}
        >
          Pan →
        </button>
        <button
          title="Use a lightweight static 2D compatibility view without losing your data or charts."
          onClick={() => setFailed(true)}
        >
          2D view
        </button>
        <span
          className="spatial-fps"
          title="Actual browser render frames per second, averaged over the last second. Not a sensing or transmission rate."
        >
          {failed ? "Unavailable" : fps + " FPS"}
        </span>
      </div>
      <div className="spatial-viewport">
        {failed ? (
          <div className="spatial-fallback">
            <h3>2D compatibility view</h3>
            <p>
              Your data and graphs remain available. Return to 3D below; if
              WebGL failed, enable graphics acceleration or try another browser.
            </p>
            <button
              onClick={() => {
                setFailed(false);
                update("reset", options.reset + 1);
              }}
            >
              Try WebGL again
            </button>
            <svg
              viewBox="0 0 500 240"
              role="img"
              aria-label="Static 2D room fallback, not recovered position"
            >
              <path
                d="M40 170 250 230 460 170 250 105Z M40 170V50L250 5 460 50V170"
                fill="none"
                stroke="currentColor"
              />
              <circle
                cx="250"
                cy="65"
                r="17"
                fill="none"
                stroke="currentColor"
              />
              <path
                d="M250 82V145M215 105H285M250 145 225 190M250 145 275 190"
                stroke="currentColor"
                strokeWidth="6"
              />
            </svg>
          </div>
        ) : (
          <SceneBoundary onFail={() => setFailed(true)}>
            <Suspense fallback={<p>Preparing the 3D renderer…</p>}>
              <Canvas
                dpr={
                  options.quality === "low"
                    ? 1
                    : options.quality === "high"
                      ? [1, 2]
                      : [1, 1.5]
                }
                camera={{ position: [5, 3.8, 6], fov: 45, near: 0.1, far: 100 }}
                gl={{
                  antialias: options.quality !== "low",
                  preserveDrawingBuffer: true,
                  alpha: false,
                }}
                onCreated={({ gl }) => {
                  canvas.current = gl.domElement;

                }}
              >
                <ContextGuard onLoss={()=>setFailed(true)}/>
                <World
                  frame={frame}
                  options={options}
                  colors={colors}
                  onFps={setFps}
                />
              </Canvas>
            </Suspense>
          </SceneBoundary>
        )}
        <div className="spatial-overlay">
          <span>{frame.source}</span>
          <span>
            {frame.packet === undefined
              ? "Illustrative scene"
              : "Packet " + frame.packet}
          </span>
        </div>
        {options.labels && (
          <div className="spatial-legend">
            <span>● TX · transmitter</span>
            <span>● RX · receiver</span>
            <span>
              {frame.scenario === "empty"
                ? "Empty room"
                : "Procedural avatar · not a recovered pose"}
            </span>
          </div>
        )}
      </div>
      <div className="spatial-toolbar">
        <label>
          Appearance
          <select
            value={options.style}
            onChange={(e) => update("style", e.target.value)}
          >
            <option>hologram</option>
            <option>solid</option>
            <option>wireframe</option>
          </select>
        </label>
        <label>
          Render quality
          <select
            value={options.quality}
            onChange={(e) => update("quality", e.target.value)}
          >
            <option>low</option>
            <option>balanced</option>
            <option>high</option>
          </select>
        </label>
        <button
          disabled={failed}
          title="Save the current visualization as a PNG, not as sensing evidence."
          onClick={saveImage}
        >
          Save image
        </button>
        <button disabled={failed} onClick={record}>
          {recording ? "Stop & save video" : "Record scene"}
        </button>
        <button
          onClick={() => {
            const p = root.current?.requestFullscreen();
            p?.catch(() =>
              setMessage(
                "Fullscreen is unavailable in this window. Open Orbit in a browser.",
              ),
            );
          }}
        >
          Fullscreen
        </button>
      </div>
      <details className="spatial-options">
        <summary>Scene controls & help</summary>
        <p>
          Drag to orbit · scroll / pinch to zoom · right-drag / two fingers to
          pan. Scene geometry is an illustration, not measured location or
          through-wall reconstruction.
        </p>
        <div className="spatial-toolbar">
          <label>
            Environment
            <select
              value={options.environment}
              onChange={(e) => update("environment", e.target.value)}
            >
              <option value="open">Open sensing room</option>
              <option value="lab">Lab benches</option>
              <option value="studio">Studio tables</option>
            </select>
          </label>
          <label>
            Pose animation
            <select
              value={options.pose}
              onChange={(e) => update("pose", e.target.value)}
            >
              <option value="scenario">Scenario motion</option>
              <option value="static">Standing pose</option>
            </select>
          </label>
        </div>
        <div className="spatial-checks">
          {(
            [
              "grid",
              "floor",
              "axes",
              "room",
              "signals",
              "labels",
              "people",
              "joints",
              "particles",
              "scan",
              "trails",
              "markers",
            ] as const
          ).map((k) => (
            <label key={k}>
              <input
                type="checkbox"
                checked={options[k]}
                onChange={(e) => update(k, e.target.checked)}
              />
              {k}
            </label>
          ))}
        </div>
        <div className="spatial-measures">
          {(
            [
              ["width", "Room width", 4, 12],
              ["depth", "Room depth", 3, 10],
              ["tx", "TX position", -5, -0.5],
              ["rx", "RX position", 0.5, 5],
            ] as const
          ).map(([k, label, min, max]) => (
            <label key={k}>
              {label} · {options[k]} m
              <input
                type="range"
                min={min}
                max={max}
                step={0.1}
                value={options[k]}
                onChange={(e) => update(k, +e.target.value)}
              />
            </label>
          ))}
        </div>
        <p>
          Room, furniture, particles and scanning plane are illustrative. Room
          and device controls adjust this illustration. The simulator’s channel
          settings are separate and explicitly applied.
        </p>
      </details>
      {message && <p role="status">{message}</p>}
    </section>
  );
}
