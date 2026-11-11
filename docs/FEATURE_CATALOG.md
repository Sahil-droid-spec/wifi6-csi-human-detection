# ORBIT complete feature guide

Updated 11 November 2026. This catalog covers implemented modules and outstanding requests.
Software verified means real code/tests were executed in the stated scope, not that
all phones, rooms or clinical datasets were validated. Simulation is separate from
recorded experiments. Archived results are preserved research outputs, not new runs.
The user has confirmed phone Take control works; full physical-device acceptance remains incomplete.

## Where to find each module

| Screen | Route | What it does |
|---|---|---|
| Home | `#/overview` | Project entry, saved data and workflow shortcuts |
| Command center | `#/control` | Shared 3D experiment; Send/Receive; phone control; shared DSP and graphs |
| 3D Sensing Studio | `#/studio3d` | Detailed CSI replay, spatial explanation, experiments and exports |
| Library | `#/data` | Import recorded MAT/ZIP/CSV/NPY/NPZ, metadata wizard and dataset selection |
| Lab notebook | `#/media` | Local recordings, media, notes and compatible reuse |
| Signal Studio | `#/dsp` | Selected-data filters, spectra, spectrograms and signal inspection |
| Learning Lab | `#/learning` | Supported LR/RF/ANN/GA/fuzzy experiments and evaluation |
| Replay | `#/replay` | Held-out predictions, quality-skipped windows and labelled seen-in-training mode |
| Evidence | `#/results` | Recorded-cohort metrics, validation protocol and confusion matrices |
| Sensing modes | `#/modes` | AX/BF technology distinctions, readiness and limitations |
| Connect | `#/settings` | Laptop server, LAN addresses, fresh pairing QR and connection diagnostics |
| Transfer & chat | `#/transfer` | General files, resumable chunks, hashes, receipts and acknowledged messages |
| Connected workbench | `#/workbench` | Shared files, recordings, workflows, DSP practicals, diagnostics and notebooks |
| AcousticLink | `#/link` | Encrypted text/binary modem, CRC/hash, FEC, ACK, retries and reconstructed inbox |
| Acoustic modem | `#/acoustic` | Simple BFSK framing, generated WAVs and decoder experiments |
| Camera Studio | `#/camera` | Permission-based input, face/eye candidates, QR, motion and experimental RGB pulse |
| Presence Experiment | `#/presence` | Matched raw-versus-Hamming experiment on recorded CSI |
| Audio Studio | `#/audio` | WAV playback, waveform/PSD/STFT, filtering, mixing and derivative saves |
| Retinal Image Lab | `#/retina` | Fundus enhancement, vessel candidates, masks/overlays and optional reference comparison |
| MATLAB Studio | `#/matlab` | Optional installed MATLAB comparisons and bounded Simulink fixture |
| Simulation | `#/simulation` | Explicit generated CSI library, parameters, source labels and separate models |
| Phone Inbox | `#/inbox` | Incoming data and timestamped markers/labels |
| DSP & SC tools | `#/advanced` | FFT/convolution, sampling, filters, ANN ladder, SOM, fuzzy rules and GA tools |
| Research Journey | `#/journey` | Original 19-figure research gallery, stages, notes and printable exports |
| SDR & spectrum | `#/receiver` | Generated/recorded I/Q and bounded optional hardware adapter |
| SmartCSI | `#/smartcsi` | GA-RF/fuzzy prototype, imported score checks and research separation |
| SC presentation | `#/scshow` | Classroom explanation of ANN, GA and fuzzy stages |
| Saved graphs | `#/graphs` | Archived recorded-data and simulator plots with context |
| Recording plan | `#/plan` | Session/checklist/consent preparation; not itself a CSI recorder |
| Orbit guide | `#/guide` | Offline rule-based help and suggested steps |
| Glossary | `#/glossary` | Plain-language technical definitions |

## Complete implementation and evidence inventory

| Feature | Status | Evidence / practical limit |
|---|---|---|
| Shared Command Centre: controller ownership, live state and timeline | SOFTWARE VERIFIED; USER CONFIRMED TAKE CONTROL | Revisioned authenticated WebSocket/REST, stale-command rejection, deduplication and reconnection. User confirmed phone Take control works; this is not full handset acceptance. |
| Command Centre Send/Receive in both directions | SOFTWARE VERIFIED | Phone-to-laptop and laptop-to-phone file bytes, SHA-256 checks, shared incoming filename, Library import, explicit controller handoff and replay. Two-client API, browser and frozen-Windows checks. |
| Five built-in file-based scenario demonstrations | SOFTWARE VERIFIED / SIMULATION | One standing, one walking, two standing, two walking and mixed. Eight-second exports contain 160 samples, 16 complex subcarriers and supplied paths; never inferred poses. |
| Rigged humans, independent activities and shared furniture | SOFTWARE VERIFIED / SIMULATION | CC0 human mesh and idle/walk/jog/gesture animations, up to four stable person IDs, scenario tour and numerical furniture editor. Foot-locking IK, drag gizmos and avatar/furniture collision solving remain partial. |
| Shared saved-input DSP and ten chart views | SOFTWARE VERIFIED | FIR/window, Butterworth and notch controls; waveform, FFT magnitude/phase, PSD, STFT, amplitude/phase and motion views; background result revisions; original bytes retained. |
| Active browser sessions and ESP32-S3 setup map | SOFTWARE VERIFIED; ESP HARDWARE UNVERIFIED | Server-observed browser/WebSocket heartbeat with 20-second expiry. Device display role is not physical hardware detection; no invented ESP/USB/Wi-Fi association telemetry. |
| Acoustic packing, estimated sample-clock correction and failed-WAV retention | SOFTWARE VERIFIED; PHYSICAL SOUND UNVERIFIED | Packing before AES-GCM, bounded carrier-clock recovery, CRC/authentication/hash checks, automatic original receiver WAV save. A generated file test is not phone-speaker-to-laptop-microphone acceptance. |
| Scene recording saved in shared Library | SOFTWARE VERIFIED | Explicit canvas recording creates a local Library WebM and download/preview. Actual short tour MP4 preserves captured timestamps; not a fixed-FPS benchmark. |
| WebGL3D sensing studio and reference parity | PARTIAL | Genuine WebGL scene and numerical pipeline implemented and software-tested; see docs/REFERENCE_VIDEO_FEATURE_MATRIX.md for per-control acceptance and remaining boundaries. |
| Command center and spatial explainer | VERIFIED WORKING (software) | Actual selected-data graphs, gap-aware contiguous filtering/spectrum, run save/export, desktop/phone-width browser checks. Procedural human scene is illustration, not inferred pose. Physical handset acceptance remains unverified. |
| Existing menus, themes, navigation, interactions and research graphs | VERIFIED WORKING | Existing design retained; additive workbench and Ctrl+K. Browser checked real generated result and search-to-diagnostics navigation. |
| Local server, QR, normal file exchange, SHA-256, resume, duplicates, chat | VERIFIED WORKING (software) | Regression suite and two native Windows HTTP software sessions. Actual handset acceptance remains unverified. |
| APK phone connection/upload/download/microphone | IMPLEMENTED / HARDWARE UNVERIFIED | APK 5.1/code11 build, v2/v3 signing, alignment and 13 address-parser checks; exact allowed LAN hosts. User confirmed controller handoff. Full handset upload/download/microphone acceptance remains unverified. |
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

## DSP and soft-computing detail

- Signals: continuous-time teaching waveforms, sampling/aliasing and sinc reconstruction,
  quantisation/SNR, DFT/inverse/phase, own radix-2 FFT, Hilbert analytic signal,
  linear/circular convolution, rational Laplace impulse/step and poles/zeros.
- Filters: FIR Hann, Hamming, Blackman and Kaiser windows; Butterworth low/high/band
  variants and notch; same-window comparisons, filter response and gap-aware processing.
- Communication practicals: ASK, BPSK, DPSK, QPSK, 16QAM, generic OFDM and seeded AWGN/BER;
  Hamming SECDED coding. Generic OFDM does not establish IEEE 802.11ax implementation.
- Audio: known-track addition/subtraction, gain, resampling, clipping checks;
  bounded two-channel FastICA on supplied mixtures; optional local Vosk speech.
- Learning: Logistic Regression, Random Forest, ReLU MLP, GA feature selection,
  fuzzy quality/fusion experiments; educational perceptron/Adaline/MLP/SOM and fuzzy
  defuzzification tools. Not every model is valid for every dataset/bandwidth.
- GA/scaling/tuning exclude outer held-out groups in app validation. The exact original
  SmartCSI trained artifacts are missing. Historical exploratory fusion scores do not
  become independently validated performance merely by appearing in a chart.

## Themes and everyday controls

Google Light, Soft Sage, Orbit Midnight, Classic Dark, Lavender Mist, Peach Sand,
Powder Blue, Mint Cream, Rose Quartz, Parchment, Paper Mono, Graphite, Dusk, Mocha,
Ocean Deep, Forest Night, Projector and Colour-blind safe. Search/Ctrl+K, favourites,
recents, presentation mode, hover help, reduced motion/effects and local bundled
assets are included. Complete contrast/performance acceptance of every widget on
every theme/device has not been established.

## What to demonstrate first

1. Connect both devices to the same reachable router/hotspot. Start the laptop LAN
   server; pair the phone with a fresh QR. The laptop stays running.
2. Command center: Take control on phone, Phone to Laptop, One walking, Send selected
   Simulation data. Receive & open shared data on laptop. Show the hash and both rooms.
3. Take control on phone again; change One standing / Two walking / mixed. Scenario
   buttons start a new Simulation; they do not relabel or reconstruct a recorded person.
4. FIR, Hamming, 7 taps; show raw/processed waveform, FFT, PSD and spectrogram. Save
   input and derived analysis separately. Reverse direction to test phone receipt.
5. Library, Signal Studio, Learning Lab, Replay and Evidence: use the same recorded
   cohort and its declared held-out protocol. Do not mix it with Simulation results.
6. Research Journey: initial AX/BF, failed SARA optimization, SAGE fading gains, then
   BF report reliability decline. Keep simulator throughput separate from detection accuracy.

## Important limits

ESP32-S3 power/USB alone does not provide CSI; compatible capture firmware/protocol
and validation are needed. Physical encrypted speaker-to-microphone delivery still
has no successful acceptance record. Live SDR, native 802.11bf and through-wall pose
reconstruction are not established. Camera pulse/retinal tools are educational
research; no webcam blood pressure or medical diagnosis. Camera angles remain local;
full presenter-camera synchronization, drag furniture gizmos, foot IK/collision-aware
paths and fully shared image jobs remain partial. A single completion percentage
would hide these distinctions, so none is assigned.

See [easy shared demo](ORBIT_SHARED_DATA_DEMO.md), [canonical checklist](ORBIT_PROJECT_CHECKLIST.md),
[3D parity](ORBIT_SHARED_V2_PARITY.md) and [image gallery](IMAGE_GALLERY.md).
