# ORBIT5.0 acceptance results — 2026-11-09

This is a verified software milestone, not100%completion of the master project or physical acceptance. See [reference parity](REFERENCE_VIDEO_FEATURE_MATRIX.md), [visual evidence](ORBIT_VISUAL_AUDIT.md), and [canonical checklist](ORBIT_PROJECT_CHECKLIST.md).

| Check | Command / method | Real result | Scope |
|---|---|---|---|
| Full Python regression | `python -m pytest -q` in project CPython3.10venv | **180passed,1warning in136.97s** |160existing tests +20new; Starlette testclient/httpx deprecation warning. |
| New signal/session tests | `python -m pytest tests/test_sensing_studio.py -q` | **20passed** | Determinism, parameter effects, loss/jitter, same-input SciPy/NumPy filtering/FFT, source flags, imports, bounds, hashes, segment/trajectory/calibration roundtrip, Library and analysis save. |
| Frontend cursor contracts | `npm --prefix frontend run test:timeline` | **5passed,0failed** | Finite-buffer playback, clamp/end bounds, held-out-only lookup with capture identity, quality states and decision-grounded avatar visibility. |
| Frontend TypeScript/production | `npm --prefix frontend run build` | **PASS** | Three/R3F actual renderer bundled locally; large-chunk advisory remains.3Dchunk lazy-loaded. |
| Python lint | `python -m ruff check orbit tests tools desktop.py build_desktop.py launch_orbit.py` | **All checks passed** | No new Python runtime dependency. |
| Frozen Windows HTTP | Installed Orbit.exe, isolated data directory,2authenticated clients | **PASS** | SciPy-matched FIR; saved trace/trajectory/calibration;3generic NPZuploads routed to3D; enforced Simulationmetadata; both clients saw same original hashes/Library; download catalog and assets checked. |
| Existing encrypted sound software | Generated encrypted WAV → native receiver API | **PASS: exact transmitted text reconstructed** | Generated-WAV codec roundtrip, not speaker-to-microphone delivery. |
| Android build5.0 | Official AAPT2/javac/D8/zipalign/apksigner | **PASS** | VersionCode10; v2/v3signatures,16KBalignment and default-deny HTTP policy verified;13private-address parser checks passed. Same existing test signing identity. |
| Current network compatibility | OSIPv4 inventory and generated APKpolicy | **Current Wi-Fi address changed; new APK permits it** |10.179.100.79and hotspot192.168.137.1plus prior private addresses. This does not prove handset reachability or bypass AP isolation. |
| Visual/control checks | Actual browser390×844and1440×1000; native window startup | **PASS within visual audit** | Actual WebGLrender, scene controls, sync, source flags,18palettes, real graphs, save/reopen, compatibility mode and exports. Native Windows window loaded menus; native GPUbenchmark not claimed. |
| Package integrity | ZIPCRC + per-fileSHA-256, canonicalSHA256SUMS verification | See release manifest / terminal log | No GitblobIDs substituted for SHA-256. |

## Negative findings and fixes

Initial targeted collection caught a Python3.10-incompatible unpacked slice expression; corrected to column_stack. A Hann FIR endpoint-zero test initially assumed the wrong polynomial degree; the unreduced z-plane now includes delay poles, while group delay matches the linear-phase reference. Reset initially recreated the Canvas and triggered context-loss fallback; fixed to retain the renderer. Start/Stop initially omitted the last cursor tick; corrected and visually rechecked. Narrow portrait view initially clipped RX; camera aspect fitting corrected it. Host-native fullscreen was refused; expanded-view fallback works. Filtered FFT magnitude can exceed raw magnitude because causal startup effects remain; smoother is not proof of better detection.

## NOT EXECUTED / blocked acceptance

- Physical phone pairing/QR, upload/download, native microphone/camera, touch/GPUperformance.
- Physical normal/encrypted phone speaker → laptop microphone and reverse. Earlier user reports of0CRC-valid microphone packets are not disproved by clean-WAV success.
- Verified live Wi-Fi6CSI, through-wall localization, native802.11bf, live SDRradio comparison.
- New MATLAB/Simulink end-to-end run on these new session exports. Earlier documented MATLAB/Simulink software checks are historical and retained.
- Original trained SmartCSI inference without its original artifacts; imported research scores are not a retrained pipeline.
- New clinical/retinal/rPPGreference validation, diagnosis or webcamBP. None claimed.
- Every reference-video detail fully accepted. Continuous acquisition UX, persisted comparison-overlay gallery, full cross-page timeline sharing and exhaustive device/accessibility acceptance remain PARTIAL in the matrix.
- A newly provisioned clean Windows machine and remote GitHubCI run. Current host's frozen/offline runtime checks are narrower evidence.

Packet/motion metrics are explicitly exploratory:16contiguous valid samples; normalized rolling variation; paired same-seed empty-simulation mean+kSDthreshold. They are not accuracy/confidence. Recorded model predictions use existing saved outer-fold artifacts and their original preprocessing, capture/date split and scaling/GA safeguards. Filter exploration does not retrain or alter those saved predictions. Display interpolation changes only avatar transforms; packet gaps and signal/model inputs are never filled to improve a plot.
