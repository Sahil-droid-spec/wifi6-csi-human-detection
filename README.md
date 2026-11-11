# ORBIT — Wi-Fi Sensing & Signal Processing Lab

**Recorded CSI research · shared phone/laptop 3D workspace · DSP · soft computing**

Import a signal, inspect its quality, process it, evaluate a model and preserve the
evidence. A Windows laptop hosts ORBIT; a paired phone sends files and controls the
same experiment. Recorded research, generated examples and network simulations
remain distinct throughout the workflow.

[All features](docs/FEATURE_CATALOG.md) · [Image & graph gallery](docs/IMAGE_GALLERY.md) ·
[Phone demo](docs/ORBIT_SHARED_DATA_DEMO.md) · [Research history](docs/research_history.md) ·
[Checklist](docs/ORBIT_PROJECT_CHECKLIST.md)

![Actual shared-room browser render with two supplied simulated people](docs/images/orbit-shared-data-room.png)

*Actual browser render. People follow supplied Simulation paths; their positions
are not reconstructed from measured Wi-Fi. This scene does not establish live CSI,
physical acoustic delivery or through-wall localization.*

## Latest progress · 5.1

The shared **Command Centre** adds explicit controller handoff, rigged humans,
standing/walking/multi-person scenarios, a numerical room editor and one server
timeline. Send/Receive stays inside the room workspace: the receiver verifies
SHA-256, saves the input in Library and opens shared replay. FIR, Butterworth and
notch processing use the selected input; both screens receive the same result.

The latest shared-data workflow passed **16 focused backend tests**, **6 frontend
command/timeline tests**, a production build and frozen-Windows two-client checks.
The preceding 5.1 full-suite checkpoint passed **193 Python tests**. These are
distinct scopes, not added together. [Acceptance records](docs/ORBIT_ULTIMATE_TEST_RESULTS.md).
The user confirmed phone **Take control** works; complete handset/ESP acceptance is
still a separate physical test.

## From signal to evidence

![Original CSI processing and evaluation pipeline](assets/assets/project_pipeline.svg)

| Workspace | Features | Evidence boundary |
|---|---|---|
| **Command center / 3D Sensing Studio** | Shared scenarios, Send/Receive, replay, TX/RX markers, furniture, cameras, ten signal views, scene recording | Supplied paths; no recovered human pose |
| **Library / Lab notebook** | MAT/ZIP/CSV/NPY/NPZ, metadata wizard, media, notes, original/derived links and lifecycle controls | CSI/media registries retain their contracts |
| **Signal Studio / DSP & SC tools** | FIR/IIR/notch, windows, FFT/DFT, convolution, sampling, quantisation, Hilbert, Laplace, spectra and spectrograms | Numerical practicals and recordings are labelled |
| **Learning Lab / Replay / Evidence** | LR, RF, ANN, GA and fuzzy experiments; held-out replay; quality gates; confusion matrices | Dataset restrictions and explicit validation protocols |
| **Connect / Transfer / Inbox** | Local server, one-time QR, resumable chunks, SHA-256, chat, receipts and transfer graphs | Application traffic, not Wi-Fi PHY throughput |
| **AcousticLink / Acoustic modem** | Text/binary-to-BFSK, AES-GCM, CRC, SECDED, ACK/retries and reconstructed inbox | Codec tested; physical sound delivery unverified |
| **Audio Studio / Connected workbench** | WAV analysis, filtering, known-track mixing, bounded two-channel ICA, optional local speech and workflows | Fixture results do not establish arbitrary voice recognition/separation |
| **MATLAB Studio / SDR & spectrum** | Optional MATLAB comparisons, fixed Simulink fixture, recorded/generated I/Q and hardware adapters | License/toolbox/device dependent |
| **Camera / Retinal Image Lab** | Capture paths, QR/motion/face-eye candidates, pulse experiments, fundus enhancement and vessel candidates | Research tools; no diagnosis or webcam BP |
| **Research Journey / SmartCSI** | Original figures, SAGE/AX-BF history, GA-RF/fuzzy prototype and score imports | Archived simulation and exploratory detection stay distinct |

The [full catalog](docs/FEATURE_CATALOG.md) lists **31 screens and 57 feature groups**,
including partial/blocked requests, 18 themes, search/Ctrl+K, presentation mode,
reduced motion/effects, the offline guide and recording plan.

## Phone → laptop → shared processing

1. Run **Start-Orbit-Server.cmd**. Put both devices on the same reachable router or
   hotspot and pair the phone using a fresh QR in **Connect**.
2. Open **Command center** on both. On the phone: **Take control → Phone to Laptop →
   One walking → Send selected Simulation data**.
3. On the laptop: **Receive & open shared data**. Bytes are checked and saved before
   replay. Samples include one standing/walking, two standing/walking and mixed.
4. Take control on the phone again. Change a scenario or select **FIR → Hamming →
   7 taps**. Both screens update. Scenario changes create a new Simulation; DSP
   changes process the current input without resending it.
5. Reverse direction for laptop-to-phone receipt. Expand the transfer graph for
   actual accepted bytes; a tiny upload may finish before the next refresh.

![Actual selected-input waveform and computed FIR output](docs/images/orbit-shared-data-dsp.png)

*Computed graphs from a selected Simulation file. Filtering can change a waveform
without improving detection. Camera angles remain local to each screen.*

An **ESP32-S3** needs compatible capture firmware and a receiver protocol; USB power
or phone pairing alone does not provide CSI. The map does not invent ESP/router/RF
telemetry. [Equipment and demo steps](docs/ORBIT_SHARED_DATA_DEMO.md).

## Recorded CSI: results and limitations

![Archived recorded 20 MHz amplitude examples](assets/assets/csi_20mhz_examples.webp)

The archived 20 MHz bandwidth-comparison run used **15 recordings, two dates,
leave-one-recording-date-out and capture-level majority voting over accepted
windows**. Both RF and ANN obtained **10/15 capture accuracy, 0.6786 balanced
accuracy and 0.7059 presence F1** under that protocol. ANN did not improve over RF.
These small-cohort results do not establish general live-sensing performance.
[Metrics, folds and limitations](docs/model_comparison_20mhz_40mhz.md).

![RF confusion matrix: archived 20 MHz date-held-out evaluation](results/figures/confusion_matrix_20mhz_random_forest.png)

The 40 MHz run instead used exploratory **leave-one-MAT-capture-out on 11 recordings**.
Class and date are confounded; its perfect capture scores are not independent
date-held-out generalization or evidence that 40 MHz is better.

<details>
<summary>Original FIR, DFT, 40 MHz and validation-protocol graphs</summary>

![Archived raw versus moving-average FIR](assets/assets/fir_filter_comparison.webp)
![Archived raw versus filtered DFT magnitude](assets/assets/dft_spectrum_comparison.webp)
![Archived recorded 40 MHz amplitudes](assets/assets/csi_40mhz_examples.webp)
![Archived validation-protocol comparison](assets/assets/validation_protocol_comparison.png)

The original moving-average experiment, later matched Hamming experiment and
SmartCSI exploratory fusion are different experiments; their scores are not interchangeable.

</details>

## SAGE V3: gains and negative results

The Research Journey preserves **19 original figures**, with PDF page provenance
and SHA-256 hashes: early AX/BF trade-offs, failed optimization, SARA V1/V2, SAGE
and BF reliability. These outputs were archived, not rerun for this README.

![Original SAGE V3 gains from the archived 12-seed ns-3 comparison](docs/research-figures/graph-13.png)

The reported **51.86% relative throughput improvement** belongs to **AX-only severe
fading in the archived 12-seed ns-3 comparison against IdealWifiManager**, seeds
1101–1112. It is not detection accuracy, a percentage-point gain or a measured
ESP/phone radio improvement. Stable-channel tests showed essentially no benefit;
channel-event traces may differ between controllers.

![Original BF successful reports from the archived 12-seed study](docs/research-figures/graph-14.png)

Under that archived **12-seed mixed-mode ns-3 protocol**, successful BF reports
declined: Rayleigh **2.958 → 2.667 reports/s**; severe **2.492 → 1.933 reports/s**.
Communication gains therefore do not establish sensing-reliability gains.
[All figures and captions](docs/IMAGE_GALLERY.md).

SmartCSI combines a GA-selected RF score with optional fuzzy fusion. Its historical
15-capture fusion result is **exploratory**: the final rule was studied using
available results, so independent validation is needed. Exact original trained
RF/mask/fuzzy artifacts are missing; separate app retraining is not an exact reproduction.
[SmartCSI explanation](docs/smartcsi_presentation.md) · [Journey provenance](docs/research_journey.md).

## Run ORBIT

**Existing packaged Windows install:** copy an extracted update into the folder
containing `Orbit.exe`, merge and replace files. Keep `_internal` and `orbit-data`.
An update overlay is not a standalone fresh installation. The native window uses
WebView2; the laptop server stays running while the phone is connected.

```powershell
Orbit.exe
Orbit.exe --server       # LAN server without desktop window
Orbit.exe --port 8766    # alternate port
Orbit.exe --local-only   # disable LAN binding
```

**Source, Windows x64 CPython 3.10:**

```powershell
python launch_orbit.py --lan
# Prepare matching wheels online, then launch offline:
python tools/prepare_offline.py
python launch_orbit.py --offline --lan
```

Raw datasets, the speech model, private signing material and a complete native
runtime are not in the source repo. Optional speech, vision, MATLAB and SDR require
their documented dependencies. [Run guide](docs/orbit_run_guide.md).

APK **5.1** uses the laptop **LAN address**, not phone `localhost`. Its HTTP allowlist
is restricted to configured private hosts; a changed laptop address can need a
rebuilt allowlist or the paired browser. Media access needs permission and a
supported secure/native context. [Android](android/README.md) · [Hardware](docs/ORBIT_ULTIMATE_HARDWARE_SETUP.md).

## Checks and remaining work

```powershell
python -m pytest tests -q
python -m ruff check orbit tests tools desktop.py build_desktop.py launch_orbit.py
python tools/checksums.py --verify
npm --prefix frontend ci
npm --prefix frontend run test:command
npm --prefix frontend run test:timeline
npm --prefix frontend run build
```

Replay defaults to held-out predictions. Outer test groups are excluded from app
training/scaling/feature selection/tuning. Quality-skipped windows are distinct
from predictions, and Simulation stays out of recorded Evidence.

Remaining boundaries: physical sound delivery; complete handset/ESP/SDR acceptance;
native 802.11bf; through-wall pose reconstruction; original SmartCSI artifacts;
independent clinical validation. Full landmark/gesture/object models, furniture
drag/IK/collision solving, universal version/revert UI and fully shared image jobs
remain partial. No 100% completion claim is made.

## Gallery and credits

- [All images](docs/IMAGE_GALLERY.md) · [Original-figure manifest](docs/research-figures/manifest.json)
- [Actual rendered scenario-tour video](docs/media/orbit-5.1-scenario-tour.mp4): supplied scenarios, variable-timestamp recorded frames; not a fixed-FPS benchmark
- [Original research history](docs/research_history.md) · [Colab notebook](https://colab.research.google.com/drive/1iFoaTazemwuRKRnVC7APWzceNzxh0OiK?usp=sharing)
- [Changelog](CHANGELOG.md) · [Checklist](docs/ORBIT_PROJECT_CHECKLIST.md) · [Reference parity](docs/ORBIT_SHARED_V2_PARITY.md)

Quaternius human mesh/animations are **CC0**, with ORBIT materials and supplied-path
control. Three.js, React Three Fiber and supporting notices are preserved in
[licenses](docs/licenses/README.md). ORBIT's layout/assets are not copied from the
reference app. MATLAB remains optional proprietary software.
