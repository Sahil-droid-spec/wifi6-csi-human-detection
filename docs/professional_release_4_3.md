# Orbit 4.3 — install, demonstrate and test

## Install on the laptop

1. Close Orbit and every old Orbit server.
2. Extract **Orbit-4.3-Replace-Files.zip**. Copy **all extracted contents** into the existing folder containing `Orbit.exe`. Choose Replace. Do not copy only the inner `orbit` folder: speech needs the additional folders inside `app-source`.
3. Keep `orbit-data`. This update does not replace your database, saved recordings, CSI datasets or trained models. It reuses your existing EXE and `_internal`; this is an update, not a standalone first installation.
4. Open `Orbit.exe` or `Start-Orbit-Server.cmd`. Refresh an old browser tab. Confirm version **4.3.0** through the app health/status or the new workbench route.
5. Install **Orbit-Phone-Companion-4.3.apk** over the old APK. It uses the same application identity and signing certificate. The laptop must remain running for the shared phone workspace and processing.

The update is larger than 4.2 because offline speech includes a real recognition model and native runtime. It does not duplicate the CSI datasets. The model is Vosk small English, not an original Orbit-trained research model.

## Connect the phone

1. Use the same trusted Wi-Fi. For a more predictable classroom setup, enable the laptop hotspot and connect the phone to it.
2. Open **Connect** on the laptop. Choose the address for the network the phone actually joined and create a fresh QR.
3. Scan the QR. A small webpage opening is normal: choose its browser option or APK handoff. Each token is one-use; make a fresh QR when switching applications.
4. The phone must use the **laptop LAN address**, never `localhost` or `127.0.0.1`. Those addresses mean the phone itself when entered on the phone.
5. This APK allows the current laptop address **10.51.160.79**, the usual Windows hotspot address **192.168.137.1**, and the previous build address **10.107.175.79**. If DHCP changes the laptop IP again, use the phone browser or rebuild the APK for the new address. No promise that the address remains fixed is made.
6. If it cannot connect, check Connection Doctor, private-network Windows Firewall permission, the selected interface and Wi-Fi client isolation. Do not disable the firewall wholesale.

## First complete test: voice becomes text, then encrypted sound

This uses an explicit generated English example so you can test before recording yourself.

1. On the APK's connection page, press **Save files for a transfer test → Generated English speech**. This sample is embedded in the APK and can be saved before pairing. The paired workbench also has **Shared files → Save demo inputs on this device**.
2. On the phone, open **Transfer & chat** and upload `Orbit-Speech-Hello-Generated.wav`. On the laptop, watch the real accepted-byte graph.
3. For that received file, choose **Save to shared Library**. Open **Connected workbench → Shared files** and select it. For this generated example, press **Mark this generated input as Simulation** before processing; its filename also states that it is generated.
4. Confirm local processing permission and press **Transcribe locally**. The checked fixture produced: **“hello orbit this is a local signal processing demonstration”**. This is the observed model output on that generated example, not a claim that every voice is transcribed correctly.
5. Press **Send this text through AcousticLink**. Enter your own shared passphrase of at least 12 characters. Mark generated content as Simulation when appropriate. Press **Create sound transmission**.
6. For a codec check, choose **Test generated WAV · codec only**. The original text must be reconstructed and SHA-256 checked. A generated return ACK is offered.
7. To test real sound, start recording on the receiving device before playing the full modem sound from the other device. Stop and decode. Playback alone is not success. If no complete message is recovered, the application must show failure rather than guess the text.
8. Play the return ACK on the receiver. Capture and decode it **on the original sending session**. Only the matching decoded ACK changes sender state. Re-pairing creates a new session, so start a fresh transmission afterward.
9. Optional: **Replay until decoded ACK** is bounded to three attempts and has a Stop control. It still needs an actual receiver and return-ACK recording. The shared laptop session service remains part of this implementation; do not describe it as an independent offline phone-to-phone modem.

For your own voice, use **Connected workbench → Record & preview → Record microphone**. Stop, listen, then Save to the shared Library. Or record a voice note in Transfer & chat, preview it and press Send explicitly. The microphone never starts from opening the page.

Speak clear English and review the transcript. The model can make mistakes, especially with accents, noise or other languages. A voice recording and its text transcript are separate linked files. Normal voice recordings are much larger than the acoustic payload limit, so send the original voice by Wi-Fi and optionally send its transcript as sound.

## Reliability and transport comparison

- Acoustic payload maximum is 8192 bytes. Slow rates and SECDED add overhead and can exceed the 300-second audio cap sooner. Use Wi-Fi for large originals.
- Reliability settings offer 100/200/400 bit/s and extended Hamming (8,4) SECDED. It corrects a single error per protected codeword and detects double errors; frame sync and timing can still fail.
- The receiver searches supported rates and compares Raw, 800–2800 Hz band-pass, 1700 Hz low-pass and 50 Hz notch on the same received WAV. The low-pass can attenuate a modem tone and harm reception.
- Generated clean/noisy earlier fixtures decoded equally well with all four filters. Do not claim a measured filter improvement from those examples. Real recordings may differ.
- **Compare saved generations of this exact payload** only groups matching hashes. It shows real WAV duration, frames, rate/FEC/encryption and generation computation. This compares generated waveforms, not physical delivery reliability.
- **Suggest a transport** gives understandable size/duration advice. Manual selection remains yours. Acoustic-only preference never silently becomes Wi-Fi.
- AgentLink here means deterministic capability/profile negotiation. It is not an autonomous AI conversation or a controller for Wi-Fi 6 MCS.

## Retinal image: send first, process on the laptop

1. Save the real CC0 example from the APK's sample menu or **Retinal Image Lab → Save the real CC0 sample photo**.
2. On the phone, confirm permission, choose `Orbit-Real-Retina-CC0.jpg`, and press **Send input to laptop**.
3. On the laptop, open Retinal Image Lab, wait for the shared original, and choose **Use this input again**.
4. Confirm permission and choose **Process & save to Library**. Show Input, Enhanced, Vessel response, Binary mask and Overlay. The original is preserved; outputs link to it.
5. White mask pixels are vessel candidates. Thin vessels can be missed and speckles can appear. This real photo has no supplied expert annotation, so do not report segmentation accuracy or diagnosis.

For the new reference-comparison software test, use `Orbit-Retina-Geometry-Simulation.png` and select **Generated test image**, processing size **768**. After saving the candidate mask, open **Connected workbench → Reference studies**, choose that saved mask and upload `Orbit-Retina-Reference-Simulation.png`.

Those two files are generated geometric teaching material, not a clinical fundus dataset. The app computes TP/TN/FP/FN, Dice, IoU and related pixel metrics against the supplied same-size mask. Keep those results separate from real recorded evidence. A genuine clinical study still needs licensed independent expert annotations and a valid held-out protocol.

Photo attribution: Mikael Häggström, CC0 1.0, [Wikimedia source](https://commons.wikimedia.org/wiki/File:Fundus_photograph_of_normal_left_eye.jpg). Normal webcams do not image the retina, and this app does not measure BP from an eye/webcam or diagnose disease.

## Audio filtering and separation

1. Transfer a supported PCM16 WAV, then choose **Save & analyze WAV**.
2. In Audio Studio inspect waveform, power spectrum and spectrogram. Apply low/high/band-pass, notch or Hamming FIR and save a new version.
3. Use the two-track mixer for known A+B/A−B. With the same track on both inputs, gains 1 and subtraction, the output should be silence. This is known-track cancellation.
4. To test blind ICA, import `Orbit-ICA-Mixture-Simulation.wav`, mark it Simulation and select it in the workbench. Confirm permission and choose **Separate independent stereo mixtures · ICA**.
5. Listen to the two component outputs and compare with the supplied generated source A/B WAVs. Component order, sign and scale can change. ICA assumes two independent sources and two instantaneous linear mixtures. It cannot solve arbitrary mono overlapping voices; the app rejects unsuitable mono/dependent input instead of promising success.

## DSP, MATLAB and the experiment notebook

Open **Connected workbench → Workflows & practicals**. Choose a compatible saved input or **Generated DSP / communications practical**.

| Choose | What to demonstrate |
|---|---|
| signals | Sine, cosine, step, ramp and exponential evaluated on a time grid. |
| sampling | Change tone/sample rate, observe alias frequency and finite sinc reconstruction. |
| quantisation | Change bit depth/amplitude; inspect quantised values, error, clipping and measured reference/error SNR. |
| fourier | Magnitude, phase with weak bins withheld, inverse-reconstruction error. |
| hilbert | Analytic-signal envelope and imaginary/quadrature component; finite-record edge effects. |
| fir | LP/HP and Hann/Hamming/Blackman/Kaiser coefficients and frequency response. |
| laplace | Enter proper H(s) numerator/denominator coefficients; inspect poles, impulse and step. This is the continuous s-plane. |
| modulation | ASK/BPSK/DPSK/QPSK/16QAM/generic OFDM under seeded AWGN. Show real bit errors/counts/BER, including bad and zero-error finite runs. |

The modulation study is a generated communications lab, not an IEEE Wi-Fi implementation. Eb/N0, seed and reference bit count accompany its metrics. Generic OFDM has no full Wi-Fi synchronization/pilot/coding chain.

Give a name and notes, then **Run & save experiment**. The notebook retains input hashes, source flags, settings, seed, software version, method and measured results. Use **Reproduce with saved settings**, JSON/CSV export, chart zoom/reset/PNG export, or **Print / save report PDF**. A deleted input cannot be reproduced; the historical checksum/report can remain.

In **MATLAB Studio**, run **Cross-check all DSP practicals** on the laptop. It executes approved same-input MATLAB calculations and compares the returned arrays with NumPy/SciPy. The checked R2026b run returned maximum differences below 7×10⁻¹⁵ across ten outputs. This is numerical agreement on the fixed fixture, not hardware accuracy. Filter coefficients are identical in both languages. The existing Simulink gain-model button also executed on this host: all 64 generated values matched Python exactly. Other machines still need their own working license/toolbox.

## Live camera, calls and screen capture

Ordinary phone LAN HTTP supports normal transfers and the APK's native voice/photo actions. Browser live camera/calls need a trusted secure context.

1. On the laptop use `Start-Orbit-Secure.cmd`, or **Connected workbench → Device diagnostics → Enable HTTPS listener**.
2. Diagnostics shows the secure address and this installation's public CA SHA-256 fingerprint. Private keys are generated locally under `orbit-data/tls`; they are not shipped in the update.
3. If you choose to enable secure media on your own devices, manually install/trust **only this installation's public CA**, after comparing its fingerprint with the laptop. Android settings often call this **Security → Encryption & credentials → Install a certificate → CA certificate**; names vary. Windows uses its certificate manager. This is an explicit trust decision for the device owner. No trust store is changed automatically.
4. Never click through a browser certificate warning. If the certificate is not trusted or the address does not match, fix the trust/address setup. Do not share `.key` files. Remove the test CA afterward if you no longer need it.
5. Open the HTTPS laptop address in both browsers or the new APK. Log in if needed. The native APK still enforces its private-address allowlist.
6. In **Connected workbench → Calls & camera**, create a code on the laptop. Both devices explicitly Join. One starts the call; the other explicitly accepts and grants microphone/camera permissions. The status must actually reach connected and the other device must receive media.
7. Hang up to release devices. Hidden/background pages stop their media. There is no automatic recording of calls. No external STUN/TURN service is configured, so firewall/client isolation can prevent a connection.
8. In **Record & preview**, screen capture uses the browser/OS chooser, with pause/stop/preview/save/discard. If unsupported on the phone, use its own recorder and import the video. Do not claim screen recording was tested on every device.

Camera Studio also supports a secure, consented phone context and saves accepted captures to the shared Library. Its current OpenCV face/eye candidates are not full validated iris, gaze, gesture or object recognition.

## Hardware and research limits

Device diagnostics reports installed dependencies and actual available observations. SoapySDR capture requires a supported receiver and driver. External CSI UDP receive requires a compatible sender with ordered timestamps and real/imaginary subcarrier arrays. Ordinary file transfer from a phone is not live CSI capture. Generated senders must remain labelled Simulation.

Use **Presence Experiment** for the recorded CSI DSP/classifier comparison and its actual date-held-out predictions. Use the archived research pages for SAGE/AX/BF results. The new upload graph and sound modem do not prove Wi-Fi 6 is superior to BF or that native 802.11bf/through-wall detection works.

Original SmartCSI inference remains blocked without its original trained RF, feature mask, fuzzy parameters and preprocessing artifacts. The app's own trained models are not those missing artifacts.

## Short professor narrative

“My core project studies human presence from recorded Wi-Fi CSI. I preprocess the signal, extract features and evaluate on a recording date excluded from training.

“I extended that into a connected DSP lab. The phone supplies an input, the laptop verifies and preserves it, processing produces a linked new version, and the notebook keeps the settings and results.

“Audio, images and CSI are different signal types. The same engineering workflow connects them; it does not mean a retinal image is CSI. Here I can show speech becoming text, encryption and acoustic framing, filtering and spectral analysis, and image segmentation.

“Every graph is computed from the selected data. Generated examples are labelled Simulation. I show failures, reference requirements and physical-device limits instead of inventing measurements.”

## Printable acceptance checklist

- [ ] Updated laptop reports 4.3.0; old server closed; original datasets/models still visible.
- [ ] Fresh QR pairs the actual phone; correct Wi-Fi/hotspot address used.
- [ ] Phone uploads a real file; laptop verifies hash and displays it; reverse download tested.
- [ ] Voice/photo/screen: permission → preview → Save or Discard; stop releases device.
- [ ] Offline English speech test produces a reviewed transcript.
- [ ] Same-payload modem WAV decodes; wrong key and incomplete capture fail honestly.
- [ ] Real speaker → microphone succeeds in each direction; matching return ACK decoded on sender. If it fails, record failure.
- [ ] Library Trash revokes fresh previews/exports; restore works; linked original protected.
- [ ] DSP practical shows parameters/source and a saved reproducible report.
- [ ] Retinal/pulse generated references stay Simulation, and real clinical claims remain withheld.
- [ ] Secure call: CA fingerprint checked, permission granted on both devices, real incoming media seen/heard, Hang up verified.
- [ ] Supported CSI/SDR hardware and independent research references tested separately, or explicitly marked unavailable.

Physical handset/media/room-acoustic acceptance is **NOT EXECUTED** by the software tests. Exact original SmartCSI and independent clinical validation are **BLOCKED** by missing inputs. Use the canonical checklist for all partial scope rather than calling the whole project 100% complete.
