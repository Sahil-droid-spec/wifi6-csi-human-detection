# Shared Command Centre V2 — source audit and acceptance

The supplied specification is preserved in specifications/ORBIT_SHARED_COMMAND_V2_2026_11_10.md.
The external reference is inspected as data, not executed or imported. Its archive
SHA-256 is `7838d94f7beb6d7b2f0d69b819289485e5e4bfb6e13b8353682728a42b7a5c25`.
All 25 source/document/manifest files are indexed in reference-audit/wi-sense-source-index.json.
The earlier full-timeline video audit remains in ORBIT_REFERENCE_VIDEO_AUDIT.json.
This milestone does not claim the entire master specification is complete.

| Reference / requested feature | Previous ORBIT | Upgrade / status | Test evidence or limit |
|---|---|---|---|
| Command Center, real 3D viewer | Independent local viewer | Shared Command centre, original ORBIT layout; implemented | Authenticated state/command/WS tests and rendered evidence |
| Primitive illustrative human | Procedural capsule body | Detailed skinned human mesh with fingers/face and licensed rig, idle/walk/jog/gesture clips | Quaternius CC0 source licenses bundled; original materials replaced; not photoreal |
| 0/1-person presets | Empty/still/walking | Exact empty, one standing/walking | Deterministic count and path tests |
| Multi-person | Two walkers only | Two standing, two independent walkers, mixed activities | Both standing roots stationary; both moving roots vary; disjoint lanes |
| Custom activity | No independent activities | Stable IDs, up to four; independent activity selectors and visibility in backend | Unique ID / bound tests; no trained people counting |
| Entering/leaving/fast/hand | Limited presets | Additional explicit scenario paths/clips | Simulation only; hand clip is illustrative; no reconstructed pose |
| Animation transitions | Limb interpolation | Mixer idle/walk/jog/gesture crossfades and path interpolation | Rendered inspection required; foot locking/IK not implemented |
| Room furniture | Two fixed layouts | Shared furniture list, six labelled presets, numerical position/rotation/scale, snapping, save/reload/remove/reset | Bounds and furniture-overlap validation; no 3D drag gizmo or avatar/furniture collision solver |
| Rendering | Themes and 3 styles | Theme-linked PBR surfaces, shadows, skeleton overlay, local assets | Actual frame counter; no fixed-FPS or photoreal claim |
| Camera | Orbit/zoom/pan/basic presets | Adds back, TX/RX focus and first-person-path follow | Local per-client camera; presenter-camera synchronization remains pending |
| Phone controller | Separate simulations | One server-owned session, explicit Take control, authenticated WS, revisioned commands | Two-client tests; physical handset acceptance not performed |
| Reconnection | Page-local replay | Current server snapshot on WS reconnect; local cameras retained | Stale revisions rejected; event IDs deduplicated |
| Playback | Independent packet cursor | Shared server clock, timestamp-based packet lookup and cancellable four-scenario tour | Actual input timestamps; untimed generic files use a display convention |
| CSI Explorer | Existing full studio | Shared channel amplitude, phase, selected subcarrier and heatmap | No phase fabricated for amplitude-only files |
| DSP Laboratory | Existing gap-safe filters | Shared FIR/Butterworth/notch, windows/order/cutoffs/time window and result revision | SciPy reference tests; original bytes retained |
| FFT analyzer | Existing magnitude/STFT | Shared magnitude, phase, Welch PSD, spectrogram | Same stated contiguous segment; no stitching across gaps |
| Motion analytics | Existing proxy | Shared proxy/threshold charts | Simulation calibration separate; no classifier probability |
| Experiment settings | Existing seeded controls | Shared noise/speed/loss/gain/rate/subcarriers/seed etc. | Controls create a new deterministic simulation buffer |
| Noisy / through-wall reference scenario | Existing simulation | Explicit noise and attenuated-path presets | Gain/noise illustration, not a physical wall-material solver |
| Dataset recordings | Library and NPZ exports | Compatible Library input selected in shared session; original and derived analysis saved separately | JSON/NPZ save/reopen; derived analysis is JSON, not a MATLAB execution claim |
| File transfer inside scene | Separate Transfer page | Reuses actual exchange UI below persistent 3D view; inline save/analyze | Hash checks and chunk timelines; transfer continues across scenario change in software test |
| Two-way file/text | Existing exchange | Retained in shared workspace | Authenticated LAN HTTP, not Wi-Fi PHY measurement |
| Post-transfer processing | Local studio only | Phone/controller reprocesses saved NPZ, single-column CSV/NPY or PCM WAV | No resend; superseded jobs cannot commit old results |
| Image processing | Existing image/retinal tools | Preserved, accessible from shared Library | Fully shared image jobs in Command Centre remain pending |
| Versioning | Original + derived Library | Saved shared analysis and source parent link | Universal graph/gallery/revert interface remains partial |
| Diagnostics, theory/viva | Existing full studio and help | Preserved through 3D Sensing Studio / existing menus | No duplicate fake hardware or theory cards |
| Acoustic transfer | Generated-WAV codec; handset fails | Bounded carrier-estimated clock correction; compression before encryption; microphone originals automatically retained locally | Generated clock-drift/echo/noise tests pass. Actual phone speaker→laptop microphone success NOT VERIFIED |
| Acoustic → tiny walking → 3D | Tiny NPZ replay | Direct received-file action inside shared workspace | Original 1,698 bytes; 400 bit/s no FEC now 42.18 s / 13 frames after packing |
| Charts | Existing plots | Cursor inspection, data zoom, same-window comparisons, PNG on line plots | Heatmap CSV/PNG controls, plot configuration persistence and full linked-range selection remain partial |
| Archived research / held-out results | Existing Replay/Evidence | Preserved | Shared recorded signal view withholds avatar unless supplied Simulation trajectory; use original Replay/Evidence for evaluated models |
| Live hardware | Unverified | No invented live source | CSI/SDR/802.11bf/through-wall localization and clinical outputs remain unverified |

The reference README explicitly states all its measurements are simulated and its
human/room are illustrative. No source code, layout or models from the reference
were copied. Reference tests were inspected as source, not run as ORBIT acceptance.

## Asset provenance

Quaternius Universal Base Characters, standard free Superhero Male mesh, and
Universal Animation Library, standard non-root-motion clips, CC0:

- https://quaternius.itch.io/universal-base-characters
- https://quaternius.itch.io/universal-animation-library
- docs/licenses/Quaternius-Base-License.txt
- docs/licenses/Quaternius-UAL-License.txt

ORBIT converts the original glTF buffer to GLB, removes external texture dependencies,
applies theme-linked research-mannequin materials and drives translation using
supplied paths. This is an anatomical rigged illustration, not a camera scan.

## Remaining acceptance

Final software verification:193Python tests pass,5frontend timeline tests pass,
ruff and the frontend build pass. The frozen Windows executable with the existing
runtime passed an encrypted generated-PCM → exact tiny NPZ → Library → shared
walking replay data and Hamming FIR workflow. Two authenticated HTTP clients saw
the same scenario and selected dataset. APK v2/v3 signatures verify against the
existing signing certificate; the builder's13address checks pass.

Browser UI acceptance: separate-origin clients share scenario/activity changes;
the second client uploads the actual tiny NPZ through the embedded transfer panel,
saves/selects it without leaving Command Centre and changes FIR/window/taps without
a resend. Dark-theme plots were inspected with actual hover values; the room
preset adds a sofa/chair and saves. Phone-width layout is browser emulation, not
an Android handset test. A UI-highlight mismatch after selecting an imported file
was corrected to use the active dataset's scenario.

Video proof: actual browser canvas recording, all64source frames sequentially
decoded. One-standing, two-standing, two-walking and mixed sections and transitions
were inspected (the sparse contact sheet skips some brief walking frames; separate
transition frames were checked). MP4 conversion preserves64frames/timestamps;
there is no synthetic frame interpolation. Background throttling makes this a
functional visual proof, not a smoothness/FPS benchmark. The earlier longer clip
was replaced after it hit the60-second recording limit before the final state.

Physical phone QR/upload/download/WebGL/microphone acceptance and both physical
acoustic directions require the actual devices. The user's failed receiver WAV
has not been supplied/found. No claim that carrier correction fixes that specific
recording is made. A new native wrapper enables downloads; submitted receiver WAVs
are also retained in the shared Library independently of download dialogs.
