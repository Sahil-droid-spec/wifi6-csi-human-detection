# ORBIT canonical checklist — 5.0 spatial milestone — 2026-11-09

## 5.1 Shared Command Centre V2 — 2026-11-10

- IMPLEMENTED: detailed CC0 rigged human mesh and idle/walk/jog/gesture clips;
  independent exact 0/1/2-person scenarios, mixed activity, custom up to four,
  server-owned short scenario tour, shared numeric furniture editing/save/reload.
- IMPLEMENTED: authenticated WebSocket state, explicit controller ownership,
  revisions, idempotent commands, reconnect snapshots, shared playback/processing,
  bounded background jobs that discard superseded results, received-file routing
  and real existing transfer graphs inside Command Centre.
- TESTED: **193 Python tests passed**, **5 frontend timeline tests passed**, frontend
  build and ruff pass. Browser clients on separate local origins demonstrated a
  scenario change propagating to the other client, real tiny-NPZ upload, and
  received 32-packet input reprocessed with 7-tap Hamming FIR. This is not a physical
  handset acceptance test. See outputs/Orbit-5.1-Tests.txt in the release package.
- VISUAL EVIDENCE: actual browser canvas recording with one standing, two standing,
  two walking and mixed activity; all64source frames sequentially decoded and
  transition frames inspected. Variable/low frame rate reflects browser background
  throttling; no universal FPS guarantee. Native Windows window also rendered;
  user interaction was detected and further native UI automation stopped.
- ACOUSTIC SOFTWARE: packing before AES-GCM reduces this exact1,698-byte teaching
  payload to42.18s/13frames at400bit/s without FEC. Carrier-estimated clock fallback
  adds tested generated3500/-7250ppm echo/noise cases. Original hash/authentication
  checks remain mandatory. Microphone submissions retain their actual WAV in the
  local Library even when normal decoding fails. Native download setting is now
  included in rebuilt Orbit.exe; a scene video also saves a Library copy.
- NOT VERIFIED: actual phone speaker→laptop microphone and reverse, handset QR/
  GPU/microphone acceptance, live CSI/SDR/native802.11bf, through-wall localization,
  clinical measurements and original missing SmartCSI trained artifacts.
- PARTIAL: full image-job synchronization, presenter-camera sharing, 3D furniture
  drag gizmos, foot-locking IK/collision-aware avatar paths, full universal version
  comparison/revert UI and complete plot configuration export. The supplied
  master specification is **not100%complete**.

Full source comparison and acceptance limits: [ORBIT_SHARED_V2_PARITY.md](ORBIT_SHARED_V2_PARITY.md).
Simple faculty demo: [ORBIT_5_1_DEMO.md](ORBIT_5_1_DEMO.md).

2026-11-10 addition: tiny walking sound example (1,698-byte NPZ, 32 amplitude
samples, one subcarrier and supplied generated trajectory). Encrypted generated
PCM WAV → hash-exact reconstruction → shared Library → 3D-session data and FIR
analysis passed in `tests/test_tiny_walking.py`; 21 targeted sensing tests passed.
New direct inbox-to-3D button builds successfully; new button interaction and
physical handset acoustic delivery NOT EXECUTED. At 400 bit/s without FEC the
generated transmission is 52.18 s / 16 frames. This does not implement activity
inference or fix the unresolved microphone transfer. See
[the sound demo guide](ORBIT_TINY_WALKING_SOUND_DEMO.md).

This is a merged progress entry; all earlier rows remain below. The new authoritative requirements are recorded in the [parity matrix](REFERENCE_VIDEO_FEATURE_MATRIX.md). **The project is not100%complete.** Hardware acceptance and explicit PARTIAL rows remain.

| Scope | Status | Evidence / remaining limit |
|---|---|---|
| Genuine 3D articulated human/room, orbit/pan/zoom, TX/RX, styles | IMPLEMENTED & TESTED | SpatialScene WebGL render, controls and source-labelled export; visual audit below. |
| Shared simulation/recorded packet cursor, CSI/DSP/spectrum/motion tabs | IMPLEMENTED & TESTED | Source-bound software tests and real browser renders; no inferred recorded pose. |
| Reproducible seeded complex multipath simulation and13controls | IMPLEMENTED & TESTED | Determinism, effects of channel controls, jitter, missing packets, buffer bounds. |
| Gap-safe FIR/Butterworth/notch, LP/HP/BP/BS, FFT/STFT | IMPLEMENTED & TESTED | Same-window SciPy/NumPy reference tests and stated processing protocol. |
| JSON/NPZ reopen; CSV/JSON/NPZ source-preserving export; Library save | IMPLEMENTED & TESTED | Roundtrip, hashes, source flags and hostile archive rejection tests. |
| Full reference-video parity | PARTIAL | Every observed page/control is accounted for in the parity matrix; no silent optional downgrade. |
| Physical phone, acoustic both ways, live RF/CSI, clinical validation | IMPLEMENTED / HARDWARE UNVERIFIED or BLOCKED | Unchanged explicit physical/artifact limitations; software clients do not establish acceptance. |

Additional verified this checkpoint: scene-level shared transport, portrait camera fit, all18palette/body-contrast checks, manual2Drecovery, source-labelled PNG/WebM, exact segment boundary, saved generated trajectories/calibration and one-click shared-Library routing. Full regression180passed; frontend cursor tests5passed; Android address tests13passed. Physical acceptance remains NOTEXECUTED.

Detailed evidence: [acceptance results](ORBIT_ACCEPTANCE_RESULTS.md), [visual audit](ORBIT_VISUAL_AUDIT.md), [demo](ORBIT_DEMO_GUIDE.md). Earlier progress follows verbatim.

---

# Orbit canonical checklist — 4.4 — 2026-11-08

This replaces the active checklist. The [4.2 checklist](archive/ORBIT_PROJECT_CHECKLIST_4_2.md) is preserved as history. A software test is not physical phone, RF or medical acceptance. No 100% completion claim is made.

Statuses: **VERIFIED WORKING**, **IMPLEMENTED / HARDWARE UNVERIFIED**, **PARTIAL**, **PLANNED**, **BLOCKED**. Each status below is bounded by its evidence.

| Scope | Status | Evidence and remaining boundary |
|---|---|---|
| Command center and spatial explainer | VERIFIED WORKING (software) | Actual selected-data graphs, gap-aware contiguous filtering/spectrum, run save/export, desktop/phone-width browser checks. Procedural human scene is illustration, not inferred pose. Physical handset acceptance remains unverified. |
| Existing menus, themes, navigation, interactions and research graphs | VERIFIED WORKING | Existing design retained; additive workbench and Ctrl+K. Browser checked real generated result and search-to-diagnostics navigation. |
| Local server, QR, normal file exchange, SHA-256, resume, duplicates, chat | VERIFIED WORKING (software) | Regression suite and two native Windows HTTP software sessions. Actual handset acceptance remains unverified. |
| APK phone connection/upload/download/microphone | IMPLEMENTED / HARDWARE UNVERIFIED | APK 4.3 build/sign/alignment and private-address parser checks. Requires a physical phone. |
| Shared media IDs, context actions, original/derivative links | VERIFIED WORKING | Existing media registry reused by Audio, Speech, image, I/Q, camera and workflow outputs. |
| Single cross-kind registry for every CSI and media artifact | PARTIAL | CSI captures and trained models retain their established registry and contracts; media-to-CSI routing uses the existing wizard. |
| Streaming import, save/discard, rename, provenance export, Trash/restore/delete | VERIFIED WORKING for shared media | Size/free-space checks, parent protection and linked exchange/acoustic export revocation. Already downloaded copies cannot be remotely erased; transfer originals can be retained independently on disk. |
| File transfer graphs | VERIFIED WORKING | Actual accepted offsets/timestamps, hash and browser application timing. Not RF strength or PHY throughput. |
| Laptop WLAN snapshot | VERIFIED WORKING on this host | Actual Windows radio type, link rates and signal percentage; no SSID/MAC retained. Does not compare AX with BF. |
| AES-GCM BFSK text/binary reconstruction | VERIFIED WORKING (codec) | Exact supplied-WAV reconstruction, hash, tamper, wrong-key and incomplete-recording tests; clipped-preamble repair verified against supplied screen-recording audio. Not a microphone acceptance claim. Maximum payload 8192 bytes; slower/FEC profiles can hit the 300-second cap earlier. |
| SECDED FEC and modem rates | VERIFIED WORKING | Hamming (8,4), every single-bit position corrected in tests, double-bit rejection plus inner CRC; 100/200/400 bit/s. Sync/length are not fully error protected. |
| Return ACK, sender binding and bounded retries | VERIFIED WORKING (software protocol) | Matching decoded ACK must come from original sender session; generated/playback alone is not acknowledgement. Three-attempt playback loop, cancellation, no Wi-Fi fallback. |
| Physical sound in both directions | IMPLEMENTED / HARDWARE UNVERIFIED | Must test the real phone speaker and laptop microphone, then reverse direction. Generated WAV tests are not this result. |
| Acoustic-only independence from the laptop HTTP service | PARTIAL | Audio contains payload/ACK, but this companion implementation still uses the laptop for processing and session state. |
| Adaptive acoustic / AgentLink | PARTIAL | Deterministic common-profile negotiation and selectable rates/FEC. No validated adaptive channel estimator or autonomous AI conversation. |
| Transport recommendation and manual override | VERIFIED WORKING (software) | Rule-based size/duration advice; acoustic-only preference preserved. No hardware MCS control. |
| Encrypted/plain/FEC/rate comparison | VERIFIED WORKING for generated WAVs | Same SHA only, real generation time/frames/WAV duration, explicit conditions. Not a physical channel benchmark. |
| Offline speech-to-text | VERIFIED WORKING on generated English fixture | Local Vosk model produced actual words and timings; no cloud service or unmeasured WER. Human/accent accuracy requires references. |
| Speech → text → encrypted modem → text → ACK | VERIFIED WORKING (software) | Full chain executed in frozen Windows build using generated speech. |
| Known-track audio mixer | VERIFIED WORKING | Gains, add/subtract, resampling, stereo handling, clipping and both-parent links. |
| Unknown-source separation | PARTIAL | Two-channel instantaneous-mixture FastICA executed on generated independent sources; mono/reverberant/moving-speaker separation is not promised. |
| Mic/photo/video/screen recording manager | IMPLEMENTED / HARDWARE UNVERIFIED | Explicit permissions, preview/save/discard, duration limits; screen pause where supported. No background recording. Actual capture acceptance remains to be done. |
| Phone photo on HTTP | IMPLEMENTED / HARDWARE UNVERIFIED | System camera returns an accepted thumbnail, then explicit shared-Library save. Full-resolution images can be imported separately. |
| Calls and live camera sharing | IMPLEMENTED / HARDWARE UNVERIFIED | Bounded two-member WebRTC signaling/media path and verified local TLS listener. Both devices must trust the installation CA and grant media permissions. No physical call was claimed. |
| Advanced iris/gaze/gesture/object recognition | PARTIAL | Existing face/eye candidates, QR and motion are retained. Full validated landmark/gesture/object models are not supplied by those boxes. |
| Search / Ctrl+K / keyboard / favourites / recents | VERIFIED WORKING within tested scope | Studios, saved files, experiments, help shortcuts, pinned tools and navigation/file recents; browser tested search/Enter navigation. |
| Loading, errors, progress, cancellation, reduced motion | VERIFIED WORKING within tested scope | Real job progress, bounded operations and next steps; cancellation is cooperative. Blocking native recognition/MATLAB work cannot always stop mid-call. |
| Basic signals, DFT/inverse/phase, sampling/aliasing/sinc, quantisation/SNR, Hilbert | VERIFIED WORKING — SIMULATION | Parameterized numerical practicals with actual outputs, source labels and finite-record limits. |
| FIR LP/HP and windows; Butterworth LP/HP/BP/notch | VERIFIED WORKING | Existing studios plus new practical controls; SciPy comparisons. |
| Laplace s-plane responses | VERIFIED WORKING — SIMULATION | Proper rational coefficients, actual continuous impulse/step and poles/zeros; distinct from digital z-plane. |
| Linear/circular convolution and own FFT | VERIFIED WORKING (existing tools) | Numerical tests retained; same-input MATLAB cross-check added. More custom-sequence UI is a refinement. |
| ASK/BPSK/DPSK/QPSK/16QAM/generic OFDM | VERIFIED WORKING — SIMULATION | Known bits, seeded AWGN, actual errors/counts/BER and sweep. Generic OFDM is not IEEE 802.11ax. |
| Existing LR/RF/ANN/GA/fuzzy and date-held-out CSI | VERIFIED WORKING on stated cohorts | Existing contracts, dataset restrictions and training-only GA/scaling retained; no new accuracy invented. |
| Hamming versus baseline CSI | VERIFIED WORKING on existing cohort | Same features, masks, seeds and held-out dates; separate from generated data. |
| Arbitrary new DSP/feature tuning and comparison workflows | PARTIAL | Existing fixed Hamming and model comparisons retained; broader claimed improvements need matched fresh experiments. |
| Workflow builder and reproducibility notebook | VERIFIED WORKING | Audio filter, image edges, I/Q-FM and generated practicals; input hashes, parameters, seeds, provenance, notes, rerun, JSON/CSV/print reports. CSI and Acoustic templates link to actual existing studios. |
| MATLAB practical equivalents | VERIFIED WORKING on installed R2026b | Ten same-input arrays compared: FFT, FIR, Butterworth filtering, Hilbert, convolution, quantisation and Laplace. Filtering uses identical Python-designed coefficients. |
| Simulink | VERIFIED fixed model; broader authoring PARTIAL | R2026b executed the 64-value gain fixture with maximum absolute difference 0 against Python. Arbitrary Simulink authoring is not implemented; license/toolbox checked per execution. |
| SAGE V3 / AX-BF research | VERIFIED archived evidence | Gallery preserved. No new operational radio controller or new SAGE simulation result claimed. |
| Exact original SmartCSI inference | BLOCKED | Original trained RF, GA mask, fuzzy parameters and preprocessing artifacts were not available in the accessible archive. Existing app models are separate, not invented replacements. |
| Retinal processing / reference metrics | VERIFIED WORKING (software) | Same-size binary TP/TN/FP/FN/Dice/IoU; tested generated geometry. Not independent real-clinical validation. |
| Independent retinal clinical validation | BLOCKED | Requires licensed expert masks and defined held-out protocol. No webcam BP or diagnosis. |
| Experimental RGB pulse and reference comparison | VERIFIED WORKING on generated sample | Quality gate and actual error against supplied reference. Real synchronized reference measurements are still needed. |
| Live SDR | IMPLEMENTED / HARDWARE UNVERIFIED | Bounded SoapySDR RX adapter; compatible driver/device absent. |
| External CSI receive | IMPLEMENTED / HARDWARE UNVERIFIED | IP-filtered bounded UDP schema for a compatible external source. Ordinary phone/file upload does not capture CSI. |
| Native 802.11bf / through-wall / general live presence claim | BLOCKED | Needs supported capture hardware, labels and validation. |
| Windows/offline/APK packaging | VERIFIED within this host's checks | Frozen EXE, offline Python environment, signed APK and byte-level ZIP verification; not every Windows/Android machine. |
| Physical final acceptance | NOT EXECUTED | Follow release guide on the user's actual devices. No software test can substitute for it. |

## Evidence and preservation

Commands and observed outputs are recorded in ORBIT_ULTIMATE_TEST_RESULTS.md and the release's native acceptance log. The update does not overwrite the existing orbit-data database, recordings, datasets or trained models. Generated examples are clearly labelled and excluded from recorded Evidence.

External runtime references: [Vosk model and license](https://alphacephei.com/vosk/models), [SoapySDR Python API](https://github.com/pothosware/SoapySDR/wiki/PythonSupport), [browser media security](https://developer.mozilla.org/en-US/docs/Web/API/MediaDevices/getUserMedia).
