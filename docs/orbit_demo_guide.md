# Orbit: tomorrow's demo

Open the application at **http://127.0.0.1:8765** after starting the local server. Enter the access code printed in your local terminal. Normal launcher restarts print a new code.

## What is already saved

- **20MHz.zip:** 15 actual captures, 1,920 accepted windows.
- **40MHz.zip:** 11 actual captures, 382 accepted windows.
- **Seven trained models:** Logistic Regression, Random Forest and ANN for both bandwidths, plus GA + Random Forest for 20 MHz.
- The supplied repository ZIP is stored as a downloadable project reference.
- The app's **orbit-data** folder contains the local originals, capture cache, trained artifacts and SQLite library. Leave this folder in place so the saved data remains available after restarting. It is excluded from GitHub and the source-only downloadable app ZIP.

## A simple presentation flow

1. In **Data & captures → Saved datasets**, select 20MHz.zip and click **Run recording**. You can also select the saved dataset and capture directly in Replay.
2. In **Detect & replay**, choose **Raw CSI**, a single classifier, or **Compare all available classifiers**, then press the run button. Comparison cards are clickable; each opens that model's real window timeline.
3. Press **Play recording** or move through the actual packet windows. The P(presence) value is a model output, not evaluation accuracy. A training recording is labelled accordingly; held-out accuracy is in Learning Lab.
4. Open **Learning Lab**. The ANN/model bench has the saved trained models and loss curves. Genetic Algorithms shows the saved GA result and its random-feature baseline. Fuzzy Logic is an interactive educational rule system: change inputs or rules and observe the computed score.
5. Use the top-right theme menu: **Google Light**, **Soft Sage**, **Orbit Midnight**, **Classic Dark**. Presentation mode reduces routine pop-ups and folds long explanations under Method & data notes. Essential mismatch/errors and research caveats remain available.
6. **Recordings & media** stores experiment photos, video and audio. Add a title, notes, and optional links to the dataset/capture. Native playback and opening the original file are available.
7. In **Server & settings**, use the LAN address/QR for a phone on the same Wi-Fi. The same session code works on the phone. A real Sharing switch turns remote access on/off from the laptop.

## Send new data from a phone

- Open a displayed LAN address, enter the session code, then choose **New data**.
- Upload a compatible CSI ZIP with config.json, or a MATLAB v7.3/HDF5 capture. For a single MAT without metadata, explicitly choose its actual AX/20 MHz or AX/40 MHz profile. The unlabelled setting supports inference; known labels can be supplied for training. Unsupported schemas are reported rather than silently interpreted.
- Use **Photos & videos** for experiment media. Images and video are stored as references; they are not converted into Wi-Fi CSI measurements.
- CSI upload limit: 2 GiB; media file limit: 1 GiB.

## Restart later

Double-click **Start-Orbit-Server.cmd** in the Orbit folder for laptop + phone access. Use **Start-Orbit.cmd** for laptop-only mode. Python 3.10+ is required; the launcher installs its private environment on first use. Keep the server terminal running. The session code is printed in that terminal.

## Research context

AX is the recorded CSI analysis mode. BF is the network-simulator research mode, not a physical BF presence detector. The 40 MHz dataset is date/class confounded and evaluated by capture; 20 MHz evaluation holds out recording dates but contains only two dates. New local model scores are kept separate from the original historical CSVs. Hardware/live through-wall claims remain unverified.

Current update: 36 backend tests pass, the production frontend builds, and real recordings were imported and used for training and inference. A physical phone upload still depends on your network/firewall and needs a real-device check.
