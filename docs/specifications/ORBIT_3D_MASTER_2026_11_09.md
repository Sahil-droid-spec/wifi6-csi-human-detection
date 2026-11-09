# ORBIT ULTIMATE — REFERENCE-VIDEO FEATURE PARITY + ORIGINAL 3D SIGNAL INTELLIGENCE + COMPLETE PLATFORM

## THE MISSION

You are the lead engineer for my existing **ORBIT Ultimate** codebase, covering React/TypeScript, FastAPI/Python, Windows app, Android client, scientific visualization, three-dimensional graphics, DSP, communications, Wi-Fi 6 research, test engineering, and product UX.

**Repository:** https://github.com/Sahil-droid-spec/wifi6-csi-human-detection

**This prompt supersedes any older instruction suggesting that a 3D human view is optional. It is MANDATORY.**

I gave you a video of the WI-SENSE X reference application (`videoplayback.mp4`, approximately 2 minutes 55 seconds). Treat **ALL visibly demonstrated features and controls in that video as the MINIMUM FUNCTIONAL BASELINE** for ORBIT. Then deliver an ORIGINAL and substantially more capable ORBIT app, not a lookalike or clone. Preserve all the added ORBIT communication, sensing, DSP, AI, SDR, MATLAB, camera, acoustic, security, and research features in my earlier master requirements. Do not sacrifice already-working functionality for appearance.

**Never claim 100% parity if the video was not inspected or a visible feature was not tested.** If the video is unavailable in your workspace, mark the video audit blocked and request access to the actual file. Do not hallucinate what it contains. Do not copy WI-SENSE X's brand, exact interface composition, graphics assets, source code, typography or CSS.

### THE MAIN OUTCOME

ORBIT must allow a user to (a) view a compelling interactive 3D human-in-room wireless sensing scene; (b) inspect the real/simulated CSI signals behind it; (c) change scenarios and processing settings with live responsive graphs; (d) record/replay/save/analyze datasets and use DSP theory; and (e) go beyond the reference with real phone communication, encrypted acoustic sound transfer, universal file workflows, MATLAB, SDR, Soft Computing, Wi-Fi 6 sensing and properly attributed research.

## A. FIRST: EXHAUSTIVE VIDEO-TO-APP AUDIT

1. Watch the complete supplied reference video at normal and slower playback, not merely one screenshot.
2. Sample screens at important state transitions and inspect the small text/controls where possible.
3. Create `docs/REFERENCE_VIDEO_FEATURE_MATRIX.md` listing every visible page, control, chart, selector, toolbar, interaction, data field, playback action and status indicator.
4. Each matrix entry must include: timestamp(s), reference capability, ORBIT-equivalent page, current status, implementation tasks, evidence/test, and a short difference showing original ORBIT design.
5. The video visibly includes these page categories; these are the mandatory initial inventory, not the exhaustive limit:
   - Command Center
   - Live Human Sensing
   - 3D Hologram Studio
   - CSI Explorer
   - DSP Laboratory
   - FFT Spectrum Analyzer
   - Motion Analysis
   - Experiment Studio
   - Dataset Recordings
   - System Diagnostics
   - DSP Theory & Viva
   - Simulation/scenario controls and playback
   - Detection event logs and signal charts
6. Capture before/after screenshots and short screen recordings of the actual rendered ORBIT app. Create a parity test checklist for each item. Implement missing functionality, not just similarly named navigation links.
7. Never report that something visible in the reference works in ORBIT unless the real interaction is tested. Avoid claiming unseen reference functionality.
8. Inspect the **latest local working tree, including uncommitted changes**, before relying on the public GitHub default branch. Preserve the latest Codex results and checklist; do not overwrite with older source.

## B. ORIGINAL VISUAL LANGUAGE: RECOGNIZABLE ORBIT, NOT WI-SENSE X

I like ORBIT's current menus, search, click interactions, themes and familiar navigation. Preserve their behavior wherever possible. Improve the product's polish and reorganize genuinely awkward pages, but do not replace everything with the same left-sidebar/card proportions as WI-SENSE X.

Use an original ORBIT identity: signal-orbit motifs, waveform-derived visual language, restrained midnight navy/indigo/blue scientific palette, accessible contrasting colors, precise typography, generous spacing, clean charts, strong information hierarchy, professional status treatment, and consistent component tokens. Maintain and improve the current multi-theme system. No copied wireframe graphics, copied character model, copied assets or branded wording. Favor clarity over neon/glass gimmicks. Build original diagrams and 3D geometry or use assets with verified license and attribution.

Improve command palette (`Ctrl+K`), global search, recent items, favorites, breadcrumbs only where helpful, right-click actions, responsive layout, keyboard shortcuts, undo/trash, dark/light themes, reduced-motion preferences, accessibility, honest loading and empty/error states. Do not create more navigation systems than needed.

## C. THE NON-NEGOTIABLE CENTERPIECE: ORBIT 3D HUMAN + WIRELESS SCENE

Implement a **real interactive 3D viewport**, not a pre-rendered picture, looping video, fake CSS pseudo-3D, or a direct copy of the reference. Prefer Three.js + React Three Fiber if compatible with the existing React frontend and Windows WebView2; verify WebGL compatibility, performance, size and license. Make it a lazy-loaded, modular feature with meaningful 2D fallback.

Scene elements:
- Original, clean, rigged or procedurally modeled 3D human avatar; neutral and visually professional.
- Ground plane, configurable room bounds/grid, optional semitransparent walls and reference axes.
- Wi-Fi transmitter (AP/router) and receiver/node markers with clear roles.
- Configurable device placement, room size and distances where simulation supports them.
- Conceptual animated propagation paths/rings/paths, clearly identified as illustrative unless computed from an actual physical channel model.
- Optional subcarrier/CSI heatmap or signal texture in a side panel; never invent real measured spatial localization.
- Human motion states: empty scene, standing/still, walking, moving, and two-person **simulated** examples; add seated/crossing or other scenarios if scientifically modelled.
- Smooth original animations, visible motion trails in simulation, subtle changes in signal indicators tied to actual simulation/replay values, and simple animated transitions.
- Orbit camera rotate, zoom, pan, preset isometric/top/side/front views, reset camera, fullscreen, pause and play.
- Show/hide grid, signals, labels, person, room and device markers.
- Pointer and touch interactions, view presets and readable on-scene labels. Ensure no overlapping controls.
- Model quality states, camera controls, FPS/performance guards, WebGL context-loss handling, reduced-motion setting and graceful fallback for mobile/low-end devices.
- Optional scene screenshot/export and recording of a *labelled visualization*, subject to platform capabilities.

Link this 3D scene to app data **honestly**:
- In simulation, generated motion and synthetic CSI may drive the scenario; show an unavoidable SIMULATED badge.
- In recorded CSI replay, synchronize time/window selection, detection decision, motion score, subcarrier graphs and the 3D *illustrative scenario*. Label the avatar behavior as **illustrative**, not reconstructed pose.
- In hardware CSI mode, show actual capture health, receive timestamps, provenance and measured CSI. A model's binary present/absent prediction may highlight presence status, but must NOT be represented as precise 3D skeleton pose, trajectory or room coordinates.
- If a separate consenting camera/pose-estimation source produces actual skeletal landmarks, that may drive a pose avatar, with explicit CAMERA SOURCE labeling, never passed off as CSI-only tracking.
- Never claim through-wall human skeleton tracking or multi-person localization from unsupported inputs.

Create a dedicated **3D Sensing Studio** and an integrated live sensing view. They should share a single 3D rendering core rather than duplicating it. Provide a Split View: 3D scene on the left, synchronized CSI/motion/evidence on the right, with resizable panels where practical.

### 3D ACCEPTANCE TESTS

The viewport must actually render on Windows and supported phone/browser clients, respond to orbit/zoom/pan, switch scenes, animate standing-to-walking and empty-room mode, synchronize with a recorded timeline, stop/reset, show TX/RX markers, preserve origin labels, respond to resize and survive route navigation. Include screenshots/recordings and automated tests for state/controls. Test fallback when WebGL is unavailable. No dead controls.

## D. MINIMUM REFERENCE-VIDEO FUNCTIONAL PARITY

Implement all of these in addition to the 3D scene. The reference video is the final source of truth for its visible interface features; this list is not a substitute for the frame-by-frame audit.

### D1. Mission/Command Center
- Live or clearly simulated session clock and scenario status.
- The central 3D scene and current input source.
- Key metric cards with units and honest source labels; do not fake live readings.
- Current motion/presence verdict, threshold and confidence/quality where meaningful.
- Signal charts, temporal frequency analysis and event log.
- Quick actions for Record, Pause, Reset, Open Experiment and Present.

### D2. Live Human Sensing
- Enter/view live hardware (when actually supported), recorded CSI replay and simulation modes.
- Time-aligned raw/processed CSI, motion score, threshold, detection decision and events.
- Visible signal provenance, packet/sample/window quality, dropped/invalid windows and timestamps.
- Source switcher, clear run/pause/replay/speed controls, calibration in supported simulation/hardware contexts, and no claim of unsupported live CSI.

### D3. CSI Explorer
- Amplitude and optional phase where present/valid; subcarrier/time matrix heatmaps, packet index selection and crosshair values.
- Zoom/pan, selection range, FFT/STFT and phase/magnitude charts where mathematically appropriate.
- Per-window quality masks; downsample for rendering without corrupting underlying data.
- Export the selected actual data and plot.

### D4. DSP Laboratory
- Controllable low-pass, high-pass, band-pass and band-stop/notch filter experiments where supported.
- Filter type, cutoff(s) in correct units, order/taps, window (Hamming, Hann, Blackman, etc.), STFT window/overlap, input rate and source selection.
- Apply/Reset, input vs filtered waveform, frequency response, phase/group delay if meaningful, spectrum and spectrogram.
- Validate parameter constraints and avoid nonsense combos. Proper pass/stop units.
- Save each processing output as a new file/version and re-open in MATLAB.

### D5. FFT Spectrum Analyzer
- Actual FFT magnitude, frequency axis, optional phase, peak detection, correct sample rate, window leakage demonstrations, time/frequency comparison and export.
- Live or replay status and zero-signal/invalid-data handling.

### D6. Motion Analysis
- Motion score vs adaptive/fixed threshold; activity windows, event list, configurable detection thresholds, sensitivity and smoothing.
- Show corresponding raw/filtered CSI, false positives and missing/invalid windows.
- Explain simulated activity vs validated activity labels.

### D7. Experiment Studio — Functional Synthetic Channel Controls
- Scenario selector and meaningful Play/Pause/Restart/Step/speed controls.
- Packet rate, OFDM subcarrier count, noise amplitude, motion intensity, virtual speed, multipath components, channel gain, packet-loss *simulation*, threshold multiplier, simulation speed, sampling jitter and random seed (the video displays these controls).
- Apply & Restart, seed reproducibility and calibration/empty-room baseline controls.
- Every control must change the actual synthetic signal-generating model consistently, or be disabled with an explanation if physically incompatible; never implement slider-only cosmetics.
- Distinguish simulation packet loss from actual PHY packet loss.
- Allow saving the experiment settings and generated data with synthetic=true provenance.

### D8. Dataset Recordings
- Start/Stop/Pause where supported; name, date, scenario, label, notes, file metadata, sample rate and source.
- List, search, preview, replay, rename, export, import, save, trash, restore and delete.
- Include recording status, session summary and metadata panel.
- Keep real recordings, synthetic recordings and archive results separate.

### D9. System Diagnostics
- Backend, LAN, phone pairing, microphone, speaker, camera, audio permissions, storage, MATLAB license/toolboxes, SDR devices, live CSI interface and WebGL capability.
- Actual connectivity reports and concrete troubleshooting actions.

### D10. DSP Theory & Viva
- Searchable correct concepts, formulas, derivations where appropriate, diagrams, interactive explanations, quick recall questions and answers.
- CSI/OFDM, multipath, sampling, DFT/FFT, STFT, filtering, threshold detection, BER and relevant course DSP exercises.
- Cross-link theory to real experiment controls, not generic disconnected pages.

### D11. Cross-Cutting Video Features
- Scenario presets; reproducible demo/replay mode; mode badges; graphs with tooltips; metric units; event logs; visible recording controls; Presentation mode; responsive and keyboard-accessible controls; correct empty/loading/error states.

## E. MAKE ORBIT SIGNIFICANTLY BETTER — CONNECTED END-TO-END WORKFLOWS

ORBIT's original advantage must be **one data object across multiple scientific studios**:

Capture/import/receive data -> authenticate/verify -> Library -> inspect -> choose processing -> change parameters -> actual computation -> compare -> save processed child version -> open in another compatible studio -> export/report/trash/restore/delete.

Build a central manifest/metadata contract: source type, filename, MIME/type, hash, size, sample rate/channels or CSI shape, unit, source/provenance, parent-child version IDs, timestamp, experiment settings and access permissions. Avoid exposing a user file from stale previews after deletion. Respect stored scientific provenance. Preserve originals by default.

Provide context-aware **Analyze This File**, file-type routing, recent history, favorite experiments, simple experiment templates and a lightweight signal pipeline builder. Reuse actual algorithms and code across modules. Build a synced timeline/selected-window contract so the 3D viewer, waveform plots, motion score and replay verdict never refer to different time windows.

## F. WIFI AND PHONE COMMUNICATION — REAL DATA PATH

- Physically verify authenticated QR pairing and two-way phone/laptop transfers; do not mistake two browser clients on one laptop for a physical phone test.
- Send/download arbitrary text, images, audio, video, PDF/ZIP/documents and small data files; resume, cancel, recover, verify SHA-256; safe file paths and file size limits.
- Show actual received bytes vs time, throughput, elapsed time, integrity, retries and connection health. Do NOT label this as measured CSI or Wi-Fi PHY rate.
- One-click analyze transferred files; preserve all previous working functionality.
- Add real two-way chat, optional voice/video calls/screenshare where platforms/permissions support them.
- Show each communication method's actual source and state.

## G. ACOUSTICLINK — NORMAL, ENCRYPTED AND AI-TO-AI SOUND

Implement true speaker-to-microphone transmission, in both directions (phone -> laptop and laptop -> phone), not a WAV upload over Wi-Fi.

- User can type arbitrary UTF-8 Unicode text (English/Hindi/numbers/symbols/emoji), or speak and transcribe with user correction where an STT engine is available. Recorded voice bytes are a distinct, larger payload type.
- Normal acoustic mode, authenticated encrypted acoustic mode, Wi-Fi mode, and explicit user-approved hybrid mode.
- Modem: educational BFSK + optional clearly identified ggwave reference; packet format, preamble/sync, symbol timing, CRC, IDs, chunking, sequencing, partial-receive progress, ACK/NACK and bounded retry; no unlimited-length guarantee in physical time.
- Security: vetted AEAD such as AES-256-GCM, authenticated pairing/key agreement, unique nonces, anti-replay, wrong-key rejection, no hardcoded keys. No silent Wi-Fi payload fallback when acoustic-only selected.
- Live transmitted/recorded waveforms, spectrogram, FFT, bit decisions, error statistics, actual throughput, encryption overhead and saved acoustic audio.
- Allow noise/distance/filter comparisons using matched recordings, valid reference bits for BER, and an experimental adaptive modem tested against fixed BFSK.
- AgentLink: two agents negotiate an acoustic protocol, exchange actual data-over-sound, optional real AI model integration; differentiate deterministic scripted agents and genuine generative AI.
- Small-file acoustic transfer with segmented/reassembled integrity; clearly warn that arbitrary large files and raw voice through sound are impractically slow compared with Wi-Fi.

## H. COMPLETE DSP, MATLAB, DIGITAL COMMUNICATION AND SDR

Preserve all existing tools and add what's missing:

**Seven DSP practicals:** (1) continuous-time signal generation, (2) sampling theorem and aliasing, (3) N-point DFT magnitude/phase, (4) linear/circular convolution, (5) FIR LPF/HPF via multiple windows, (6) Butterworth IIR LPF/HPF from specifications, and (7) Hilbert transform/analytic signal; plus quantization, Laplace basics, FFT/STFT, resampling, filters, correlation/equalization and audio before/after listening.

**Digital communications:** ASK, BFSK, BPSK, QPSK, QAM, DPSK, OFDM, pulse shaping, matched filters, AWGN/fading, timing synchronization, eye patterns, BER/SER vs SNR, constellation diagrams and correct source labels.

**MATLAB Studio:** actual MATLAB Engine execution when installed/licensed, shared Library inputs/outputs, numerical comparisons, optional runnable Simulink examples; no startup dependency on MATLAB.

**SDR Studio:** generated/recorded I/Q and verified live receiver modes; spectrum/waterfall, tune/scan, AM/FM demodulation, saved I/Q and recovered audio; detect real hardware, drivers and capabilities. Never assume RX-only hardware transmits or enable unapproved RF TX.

**Audio/image/video:** waveform, spectrogram, filtering, image enhancement/segmentation, video capture and streaming, compression experiments, source separation as exploratory when ground truth exists, and user-controlled saving/deletion.

## I. INTELLIGENT SENSING AND RESEARCH ACCURACY

Central reproducible experiment: selected recorded Wi-Fi 6 CSI -> quality audit -> baseline preprocess vs Hamming FIR -> consistent features -> RF/GA/ANN/Fuzzy comparisons -> held-out date/capture prediction -> Replay and Evidence. Keep the same splitting/tuning rules; filtering may hurt, and that is a valid result.

Preserve distinct historic SmartCSI 73.33 / 86.67 / 93.33 percent figures and current repository validations with their exact experimental protocols; never mix scores or present trained models as originals if original artifacts are missing. Historical 15-capture research is preliminary.

Preserve archived SAGE V3 vs IdealWifiManager Wi-Fi 6 ns-3 comparisons and sensing-report tradeoff; experimental SAGE-Fuzzy V4, AX vs AX+BF, OBSS-PD and SARA, with accurate provenance and no fabricated improvements. These are ns-3 results and do not automatically control a physical Wi-Fi NIC.

**Live hardware CSI** must be explicitly verified with a supported Wi-Fi CSI capture interface and correct 802.11ax frame provenance. File transfer alone is not CSI. Do not label synthetic CSI as live sensing.

## J. CAMERA, HUMAN VISION AND RESPONSIBLE HEALTH RESEARCH

- Real camera permission, face/eye/iris landmarks, blinking, hand gestures, object/motion detection, QR scans, images/video, screen recording where supported, source-aware saving and deletion.
- Video-to-video-device transfer with actual network metrics.
- Educational rPPG extraction with signal-quality checks and reference comparisons; no unvalidated diagnosis.
- Retinal/fundus image research only from genuine fundus photos and licensed datasets, vessel/optic-disc segmentation and reference-mask evaluation; ordinary webcam does NOT image the retina. Do not claim unvalidated blood-pressure readings.
- If camera landmark source is used to animate 3D pose, clearly disclose it is camera-based, not derived from Wi-Fi CSI.

## K. PROFESSIONAL EXPERIENCE & QUALITY

- Keep and improve existing theme system, menu search/click behavior; maintain a recognizable ORBIT identity.
- Responsive desktop/phone and WebView2; readable desktop charts and mobile touch targets; keyboard support, reduced motion, screen-reader labels, chart alt summaries, export and performance.
- Global search and command palette across tools, datasets, experiments and help; favorites/recent; one-click Analyze; safe file actions.
- Device diagnostics; actual source badges and reliable errors; no fake 'Connected' indicators.
- Background jobs, cancel, resource limits, progress, lazy-load 3D/heavy labs, visible graph performance, failure recovery and good offline behavior.
- Research Notebook: save inputs, hashes, parameters, software versions, random seed, method, metrics, plots, limitations, reproducibility and notes.
- Visual Experiment Builder: small set of actual compatible processing chains; no pretend universal no-code execution engine.
- Experimental Comparison: same payload across Wi-Fi/sound; raw/filtered CSI on same held-out cohorts; fixed/adaptive modem under matched noise; Python/MATLAB same inputs; SAGE matched ns-3 conditions.
- Security: authenticated pairing, secure storage, correct deletion/trash/restore, explicit camera/mic permissions, no secret logging, no silent internet exposure, input validation.

## L. IMPLEMENTATION PRIORITIES AND RELEASE PHASES

**P0a — Reference baseline and ORIGINAL 3D centerpiece:** audit full video; implement and verify original interactive 3D human+room+transmitter/receiver, scenarios, camera controls, synchronization, simulated/recorded provenance and fallbacks. Create feature matrix and screenshots.

**P0b — Reference-video parity:** functional Mission Control, live/recorded/simulated sensing, CSI Explorer, DSP/FFT, Motion Analysis, Experiment Studio controls, Dataset Recordings, Diagnostics, Theory & Viva, event logs, playback.

**P0c — Real platform foundation:** actual phone transfer, graphs, shared Library, source/versions and end-to-end analysis flow.

**P0d — Unique communication differentiator:** physical two-way normal and encrypted AcousticLink, reliable frames and measurements.

**P1 — Research and scientific labs:** CSI-window microscope, fair baseline/Hamming model testing, proper SAGE/SmartCSI evidence, 7 DSP practicals, MATLAB and SDR integrations.

**P1 — Product differentiation:** Signal Journey, AgentLink, research notebook, comparing experiments, capture/recording management, report/presentation mode.

**P2 — Advanced extensions:** full phone voice/video calls, live video capture sharing, additional modulation/ML/health experiments, optional exploratory hardware and advanced UI refinements.

If a task is already implemented and passes tests, **reuse it** instead of spending tokens rebuilding it. Where no hardware/license is available, implement testable adapters, sample replay, diagnostics and honest blocking status without pretending validation.

Work one slice at a time with functioning integration. Do not attempt an enormous untested rewrite, and never silently break something already working.

## M. REQUIRED TEST MATRIX AND EVIDENCE

For EACH reference-video feature, mark: IMPLEMENTED & TESTED / IMPLEMENTED, HARDWARE UNVERIFIED / PARTIAL / MISSING / BLOCKED. Record direct test evidence and screenshot link in `docs/REFERENCE_VIDEO_FEATURE_MATRIX.md`.

Required acceptance categories:
1. Reference-visible page navigation and every clickable control.
2. Real 3D render, animations, orbit/pan/zoom, scenarios, metrics sync, WebGL fallback and mobile responsiveness.
3. Synthetic-parameter reproducibility: same seed+configuration -> same data; parameter changes affect generated data as intended.
4. Selected CSI time-window synchronization between 3D, raw, filtered, features, model prediction, event log and Replay.
5. Validated no-fake-live source badges and scientifically honest chart units.
6. Real phone pairing, upload and download on physical hardware (must test manually with user device; two local clients aren't enough).
7. Real acoustic laptop->phone AND phone->laptop; normal and encrypted sound, wrong key and tamper tests; do not call WAV loopback real acoustic.
8. Signal calculations matched against reference tests; unfiltered/filtered comparisons on matched held-out data; saved provenance.
9. Library import, save, version, export, trash, restore, delete; all relevant file types.
10. MATLAB and SDR dependency detection, correctly blocked state and real execution when hardware/licenses available.
11. Frontend TypeScript build, Python tests/lint, Windows packaging, Android build, regression/performance/accessibility/visual tests.
12. Presentation script demonstrable without hidden fake measurements or invented accuracy.

Deliver **before/after screenshots** on desktop and phone, plus an optional screen recording of ORBIT. Do not claim any screen was visually inspected if there is no real render/capture. Explicitly record unresolved testing requirements.

## N. REPORTING, FILES AND HANDOFF

Maintain/merge the existing local `docs/ORBIT_PROJECT_CHECKLIST.md` (do not overwrite it); create/update:
- `docs/REFERENCE_VIDEO_FEATURE_MATRIX.md`
- `docs/ORBIT_ULTIMATE_STATUS.md`
- `docs/ORBIT_VISUAL_AUDIT.md`
- `docs/ORBIT_3D_DESIGN_AND_PROVENANCE.md`
- `docs/ORBIT_ACCEPTANCE_RESULTS.md`
- `docs/ORBIT_DEMO_GUIDE.md`

After each milestone report: what was implemented; files changed; exact tests and results; screenshot/visual verification; what was NOT verified; regressions/limitations; and next smallest concrete task. Preserve datasets, models, secrets, saved sessions and user library. Back up before data migrations. Commit changes incrementally on an appropriate working branch if available and safe; do not force-push/overwrite user work.

## O. EXACT NEXT ACTION — BEGIN IMPLEMENTING NOW

1. Locate and view the actual 175-second reference video. Build the exhaustive page/control parity matrix. If unavailable, mark the video audit blocked; never invent it.
2. Inspect latest local ORBIT source, local changes and current tests.
3. Produce a concise gap map and capture current screenshots.
4. **Implement the original ORBIT 3D HUMAN + ROOM SCENE FIRST**, including real orbit/pan/zoom, standing/walking/empty simulations, TX/RX nodes, play/pause, scene switches, clear simulated/recorded source badges, 2D fallback and integration with one existing replay timeline.
5. Test, build, render, capture screenshots; fix problems found. Ensure this scene is not a copy of WI-SENSE X.
6. Then implement remaining reference-video parity and the integration improvements, reusing working code.
7. Continue through the priority queue, updating the matrix and master checklist after each verified step.

**FINAL CONTRACT:** The features in the reference video are the **minimum benchmark**, not the finish line. The fully interactive 3D human environment is MANDATORY. ORBIT must keep its unique identity and deliver substantially better scientific traceability, cross-lab workflows, original visualizations and verified communication experiments. Produce functioning integrated code, tests and visual proof—not placeholder pages, copied styling, undocumented simulations or inflated claims.
