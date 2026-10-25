# Orbit presentation runbook
## Before class
1. Start **Orbit/Start-Orbit-Server.cmd** on the laptop. Keep its terminal running. If Orbit is already running, use that copy.
2. Open **http://127.0.0.1:8765/#/overview** and enter the terminal code. A normal restart prints a new code.
3. Select Google Light (or another theme) and Presentation mode.
4. Put phone and laptop on the same trusted Wi-Fi. In Server & settings, check that sharing is on and read the LAN address. Use the address displayed by Orbit for the current network.
5. On the phone, open that LAN address and enter the same code. **localhost/127.0.0.1 on the phone refers to the phone, not the laptop.**
6. Rehearse one upload tonight. If it fails, check Wi-Fi isolation, server sharing, address, laptop sleep and Windows private-network permission for Python. A trusted home network or phone hotspot with the laptop joined can avoid guest-network client isolation. Do not set up public port forwarding.

## A 10–12 minute demonstration
### 1. Introduce Orbit — 40 seconds
**Click:** Overview and point to the circular hub.
**Say:** “Orbit is a local Wi-Fi sensing research lab. It processes recorded channel-state information, extracts features, and compares learning methods. The phone transfers files and accesses the laptop workspace.”
Point around Receive → Window → Filter → Spectrum → Features → Reason → Model → Verdict. Each stage leads to a usable lab or view.

### 2. Show saved data — one minute
**Click:** Data & captures → Saved datasets → 20MHz.zip → Select dataset.
**Show:** 15 captures, 1,920 accepted windows, labels and quality metadata. The 40 MHz library adds 11 captures and 382 accepted windows.
**Say:** “I import once and store the recordings locally. I inspect packet counts, subcarriers and data quality before analysis. Saved data remains available after restarting.”
Positive example: **20MHz/1people/2024-07-12/capture1.mat**.
Absence example: **20MHz/0people/2024-07-12/capture0.mat**.
The small repository ZIP is a source-code reference, not a CSI recording.

### 3. Explain DSP — 90 seconds
**Click:** Signal Studio → Recorded CSI → Moving-average FIR → 15 taps → Recalculate experiment.
**Show:** Raw/processed traces, spectrum, statistics and coefficients. Optionally run Filter shootout or Direct DFT vs radix-2 FFT.
**Say:** “A moving average smooths neighbouring samples. The 15-tap causal filter introduces seven packets of group delay. The spectrum helps inspect variation in normalized frequency. Smoothing does not automatically improve classification.”
Axes use packets and cycles per packet. Do not call the frequency axis Hz without a verified packet rate. The graphs are computed from the selected capture.

### 4. Compare models — two minutes
**Click:** Detect & replay. Choose the saved dataset/capture. Try Raw CSI, Random Forest, Logistic Regression or ANN / MLP. Then choose Compare all available classifiers → Run all classifiers.
**Show:** Comparison cards, a chosen model's timeline, Play/Pause and the window slider. Repeat with the absence example.
**Say:** “Logistic Regression is a linear baseline, Random Forest combines decision trees, and the ANN learns a nonlinear mapping. GA-assisted RF uses selected features. The app validates the recording/model contract.”
**Explain the score:** “P(presence) is an uncalibrated model output, not the model's overall accuracy. A training recording is marked. Independent evaluation is in Learning Lab.”
Playback is recorded-data replay; its display speed is not the original acquisition clock.

### 5. Make Learning Lab the main syllabus section — three minutes
**ANN/model bench:** Show architecture, actual training loss, held-out metrics and confusion matrix.
**Say:** “Each subcarrier contributes mean, standard deviation, mean absolute adjacent difference and p90-minus-p10 range. At 20 MHz, 256 subcarriers give 1,024 features per window. The ANN has hidden layers of 64 and 32 units. Scaling is fitted inside each training fold.”

**Genetic Algorithms:** Open the saved GA result; show feature count/indices, convergence and random-feature baseline.
**Say:** “Candidates represent feature subsets. Selection, crossover and mutation search for useful subsets. Fitness is evaluated inside training data; the outer held-out recordings stay outside the search. I compare all features, GA selection and matched random features.”
The prepared local GA run uses population 4 and 2 generations. Show saved results rather than retraining during the presentation.

**Fuzzy Logic:** Start with variation 0.40/motion 0.60, then move variation to 1.00. The centroid changes from about 0.510 to 0.828. Show fired rules; edit a rule if useful.
**Say:** “Low/medium/high memberships determine rule strengths. AND uses minimum, aggregation uses maximum, and centroid defuzzification gives a score.”
This is an educational rule-system example, separate from trained presence classifiers.

### 6. Send data live from the phone — two minutes
**Prepare on phone:** Open the laptop LAN URL, log in, then Server & settings → Phone & laptop downloads → download **Phone-Upload-Demo.zip**. It is about 5.2 MiB and contains one actual supplied 20 MHz capture and its configuration.
**Laptop:** Leave Data & captures → Saved datasets visible.
**Phone browser or APK:** Open New data, choose Phone-Upload-Demo.zip from Downloads and upload. Do not unzip it first. Wait for transfer/import to finish.
**Laptop:** The shared library normally refreshes within four seconds. Select the new Phone-Upload-Demo.zip, open its recording in Replay and run a model.
**Say:** “This file has just travelled over local Wi-Fi from phone to laptop. The laptop validated and stored it. Both screens share the same library, and a compatible saved model can analyse it.”
The transfer happens now; the CSI itself is recorded data. This demo recording was also used in training, so replay is a functional example, not held-out accuracy or a fresh radio measurement.

For new CSI, upload the supported MATLAB v7.3/HDF5 structure. A standalone MAT without config can use its actual AX/20 or AX/40 profile. Leave labels unlabelled for inference unless ground truth is known. Unsupported formats should report an error.

### 7. Store a photo/video — 30 seconds
Take a photo or short video with the phone camera first. In Recordings & media, choose it, add title/notes, optionally link a capture, then save. Show it appearing on the laptop.
**Say:** “This stores experiment context. Images and video are not CSI measurements.”
A video made today is illustrative unless actually recorded alongside the original CSI. Do not call it synchronized evidence for a 2024 recording.

### 8. Close with measured evidence — 40 seconds
Use **Learning Lab** for current local held-out metrics. **Results & evidence** preserves the earlier historical runs; do not mix configurations or confuse replay probability with accuracy.
**Say:** “The 20 MHz evaluation holds out recording dates, but only two dates are available. The 40 MHz subset has date/class confounding. These are exploratory estimates. BF results are network-simulator measurements, not physical BF presence detection.”
Close with: “The working system demonstrates storage, DSP, learning-method comparison, recorded replay and phone-to-laptop transfer. Continuous live radio capture is the next hardware integration.”

## What is live?
- A phone can transfer a file now and the laptop can receive, validate, store and display it.
- Models can compute real outputs on the selected recorded CSI.
- Continuous collection of new CSI from a compatible adapter/driver is separate hardware work. The current APK does not acquire CSI directly from a phone's Wi-Fi chipset. Installing an APK or uploading a video does not enable that capture capability.

## APK installation and use
1. Start the laptop server. First open its LAN URL in the phone browser and log in.
2. Download **Orbit-Phone-Companion.apk** from Server & settings. Install/open it using Android's installer. It is a locally signed classroom test build, not a Play Store release.
3. Enter the laptop LAN URL, connect and enter the terminal code again inside the APK.
4. Use Upload/mobile navigation. Android's document picker selects MAT/ZIP/media. Downloads can be saved to a folder you choose.
5. Keep the laptop running: the APK is a companion; Python models and the library stay on the laptop.

Intended minimum: Android 8.0/API 26 with current Android System WebView/Chrome. The package was compiled, signed, checked for alignment/package metadata, and address validation tested. It was not installed on a physical phone in this session. Rehearse tonight; the ordinary phone browser is also supported.

## Download and run on a Windows laptop
- **This laptop:** already installed. Use its current Orbit folder and Start-Orbit-Server.cmd; dependencies are installed.
- **Another Windows laptop:** download **Orbit-Laptop-Windows-Demo.zip**, extract to a writable folder, install Python 3.11 if absent, then double-click Start-Orbit-Server.cmd. First start downloads scientific dependencies into .venv; later starts reuse them.
- The full demo bundle includes MATLAB captures, caches, trained artifacts and a consistent database snapshot. The large original 20MHz.zip/40MHz.zip archives are omitted because their captures are already in the library. Original archives remain in this computer's Downloads folder.
- **Orbit-App.zip** is the small source/interface package and excludes runtime data. Keep orbit-data to preserve the saved library. Do not transfer .venv between computers; the launcher creates it locally.

## Short answers
**Is playback live sensing?** It is recorded CSI replay. File transfer occurs live; continuous radio capture is not integrated.
**Why can a replay show 100%?** That is a particular model output, possibly on training data. Use held-out metrics for accuracy.
**Is GA always best?** No; inspect this run and its baselines. Small datasets limit conclusions.
**Does BF detect people here?** That area shows network simulation evidence. Physical BF sensing is unverified.
**Can any phone file be classified?** Compatible CSI needs a matching model/profile. Photos/video/audio are stored as context, not classified as CSI.
