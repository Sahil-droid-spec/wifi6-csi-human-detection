# Orbit 5.1 — shared Command Centre demo

## Install and connect

Close Orbit and its server. Copy this update ZIP's contents into the EXISTING folder
containing Orbit.exe, replacing files. Keep orbit-data and _internal. Restart
Start-Orbit-Server.cmd. Install Orbit-Phone-Companion-5.1.apk on the phone, connect
both devices to the same reachable LAN/hotspot, and scan a fresh QR in Connect.
Do not type localhost on the phone. The APK adds the laptop's current10.197.120.79
address and keeps192.168.137.1 hotspot allowance; a later IP change can still need
a new exact-host allowance or the paired browser. The phone is not an independent
CSI sensor and the laptop server stays running.

## Shared 3D and processing

1. Open Command center on both screens.
2. On the phone press Take control. The laptop becomes a viewer; it can explicitly
   Take control again. Camera angle and render quality remain local.
3. On the phone choose One standing, Two standing, Two walking, then Standing +
   walking. Check the explicit scenario text, count and per-person activity lists.
4. Press Play shared replay. Both read one server timeline. A selected generated
   scenario supplies its avatars and synthetic signal samples; no pose inference.
   Run 4-scenario tour visits one standing → two standing → two walking → mixed,
   four seconds each. Another scenario/controller choice cancels the tour.
5. Expand Channel experiment settings; change noise/speed and release the slider.
   This restarts a generated experiment, not a physical capture.
6. Open Transfer INSIDE Command Centre. Choose Simulation-Walking-Tiny.npz or a
   larger Simulation-Walking.npz. Both sessions can view the real server byte
   timeline. A tiny local upload may finish before the next graph refresh.
7. After completion choose Save to shared Library in this panel. Compatible data
   opens for shared processing without leaving Command Centre. Unsupported image
   analysis belongs in the existing Image processing/Retinal Lab.
8. In Signals & DSP choose FIR, Hamming and 7 taps (edit a number then tap elsewhere
   to commit). The same saved input is reprocessed. Try Butterworth next. Both
   screens show the committed result revision. No second upload is needed.
9. Inspect raw/processed waveform, FFT magnitude/phase, PSD, spectrogram, CSI
   amplitude/phase where available, and motion proxy. Missing packets stay gaps.
   Hover and zoom line charts; use PNG to export those charts.
10. Save input & derived analysis separately. Open shared Library for export,
    rename/trash/restore and compatible studio/MATLAB routing. Saving an analysis
    does not mean MATLAB has run it.
11. Room editor adds/moves/scales/rotates/removes furniture with numeric controls.
    Changes are shared. Save/reload a room. Furniture does not alter RF physics;
    avoid walking lanes. No drag gizmo or foot-locking IK is claimed.

Record scene captures the rendered canvas with source/scenario labels. It requests
a download AND saves a local Library copy with an inline preview/download link.
The browser may throttle background rendering; exported frame rate is not a
hardware performance benchmark. The supplied proof MP4 preserves its64actually
captured source frames with variable timestamps; no interpolated motion is added.

## Tiny walking via encrypted sound

The sample is1,698bytes,32amplitude packets at20nominal packets/s, one synthetic
subcarrier and a supplied walking path (timestamps0–1.55s). It is a reduced teaching
session, with no complex phase or research classifier result.

1. In Command Centre → Encrypted sound, download the tiny walking NPZ.
2. Select that file as payload. Mark Simulation and Encrypt. Enter the same public
   demonstration passphrase on both devices: orbit-demo-passphrase.
3. Select400bit/s and FEC OFF. Create sound transmission.
4. The updated packing-before-encryption produces42.18seconds /13frames. Read the
   actual duration in your result. Old pre-generated52.18-second WAVs remain old
   transmissions; regenerate to test the new sender.
5. First Test generated WAV · codec only. This is the verified software path.
6. For the physical attempt, start the laptop microphone BEFORE playing the full
   phone audio. Stop about one second after playback finishes; keep the recording
   below60seconds for bounded clock correction.
7. Only Hash-checked content recovered establishes complete recovery. Then find
   the NPZ in Shared reconstructed inbox and choose Save & open Simulation in3D.
   In this embedded panel it selects the dataset in the shared Command Centre;
   controller ownership is required. Press Play shared replay.
8. No recovery: do not present the codec test as physical delivery. The submitted
   microphone WAV is now retained as Orbit-Receiver-Recording.wav in shared Library
   even when decoding fails. Its media/identifier.wav path is shown by the receiver
   panel after a normal failed result. New Orbit.exe enables native save dialogs.

Packing preserves the original file hash; it is not lossy compression of the signal.
Encryption does not correct room noise. The decoder adds carrier-estimated sample
clock correction and retains CRC, authentication and exact-byte checks. Physical
phone→laptop delivery remains unverified without a successful actual recording.

## Short script

“Our main research studies human presence in recorded Wi-Fi channel measurements.
This Command Centre adds one shared experiment that my phone controls and my laptop
displays. Here I select exactly two simulated walkers; these are supplied scenario
paths, not positions inferred from Wi-Fi. I can send a file, verify its bytes and
change DSP processing without uploading it again. The waveforms, spectra and
spectrogram are calculated from the selected input. The tiny walking file can also
be encrypted and encoded into sound. A generated-file test checks the codec;
speaker-to-microphone delivery is a separate physical acceptance test. Our actual
held-out human-detection results remain in Replay and Evidence, with their stated
validation protocol.”

See ORBIT_SHARED_V2_PARITY.md for the complete implemented/partial/unverified matrix.
