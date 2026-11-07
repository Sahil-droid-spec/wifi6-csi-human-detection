# Orbit 4.2: phone, laptop and signal-processing demo

## Install the replacement

Close every Orbit window/server. Extract `Orbit-4.2-Replace-Files.zip` and copy **its contents** into the existing folder containing `Orbit.exe`. Replace matching files. Keep `orbit-data`; this update does not contain or replace your database, recordings or models. This is an update for the existing Windows installation, not a standalone installation.

The ZIP includes the complete current `app-source/orbit`, the additional cryptography runtime, the updated APK, demo files, updated dependency locks and the additional offline wheels. The existing `Orbit.exe`, `_internal` and other dependencies remain necessary. Do not copy the inner `orbit` folder beside the EXE: it belongs inside `app-source`.

Install `Orbit-Phone-Companion-4.2.apk` over the old phone app. It uses the same package and signing certificate. Android 8 or later is required. The APK allows HTTP only to the laptop addresses used for this build: **10.107.175.79** and **192.168.137.1**. If the laptop address changes, use a fresh QR in the phone browser, or rebuild for the new address. This APK is a companion to the running laptop server.

## 1. Connect the two screens

1. Start `Orbit.exe` or `Start-Orbit-Server.cmd` on the laptop. The local server remains available.
2. Put both devices on the same trusted Wi-Fi or connect the phone to the laptop hotspot.
3. On the laptop open **Connect**, choose the active Wi-Fi/hotspot address and create a fresh one-time QR.
4. Scan on the phone. Continue in the phone browser, or use the APK's Connect page with the full pairing URL. The phone must use the laptop's LAN address, never `127.0.0.1` or `localhost`.
5. Keep the laptop server running. If the connection fails, use Connection Doctor; check the Windows private-network firewall and access-point client isolation. Do not disable the firewall wholesale. A QR authorizes pairing; it cannot make an unreachable laptop reachable.

## 2. Send a real retinal original, then process on the laptop

1. Save `Orbit-Real-Retina-CC0.jpg` on the phone. In the updated Retinal Image Lab, use Save the real CC0 sample photo when the supplied samples are in the app folder.
2. On the phone open **Retinal Image Lab**, confirm permission, choose the JPEG, then press **Send input to laptop**. You do not need to process it on the phone first.
3. Open the same page on the laptop. Within about four seconds, **Saved fundus images** lists the original. Choose **Use this input again**.
4. Confirm permission on the laptop, then choose **Process & save to Library**. Inspect Input, Enhanced, Vessel response, Binary mask and Overlay. Original bytes are retained and results are linked to that original.
5. The white mask pixels are vessel candidates. Speckles and missed thin vessels are possible. No reference mask was supplied, so accuracy/Dice are unavailable. This is image processing, not BP measurement or diagnosis. A webcam cannot capture a true fundus photograph.

Photo: Mikael Häggström, CC0 1.0; [source and license](https://commons.wikimedia.org/wiki/File:Fundus_photograph_of_normal_left_eye.jpg). Original SHA-256: `38a07f36f27f095e818aea7b96d34202c05176d30253c66733f2e00379e9e0e6`.

## 3. Send Hello as encrypted sound

1. Open **AcousticLink** on either device. Leave the text as `Hello Orbit`.
2. Enter a shared passphrase of at least 12 characters; enter the same passphrase at the receiving end. For the supplied demonstration WAVs only, the public test key is **`orbit-demo-passphrase`**. Do not use that public key for private information.
3. Press **Create sound transmission**. Play or save the generated modem WAV. The waveform encodes file bytes using 1200/2400 Hz BFSK at 400 bit/s. Frames include sequence numbers and CRC32. Encrypted mode uses PBKDF2-SHA256 (600,000 iterations), fresh salt/nonce and AES-256-GCM authentication. SHA-256 checks the reconstructed content.
4. First press **Test generated WAV · codec only**. Expected for this Hello example: `Hello Orbit` is recovered with two CRC-valid packets. This is a software codec test, not a physical sound-transfer result.
5. For a physical attempt, start **Record microphone** on the receiver, allow access, then play the complete modem WAV on the other device. Stop the recording and inspect the result. Keep sound at a comfortable volume. Use a separate phone recorder exported to PCM WAV if browser microphone access is blocked.
6. The new APK has a native permission-based PCM recorder for ordinary LAN HTTP. Recording stops/discards when the app leaves the foreground. Desktop microphone use requires a supported secure context such as localhost. Physical Android and room-acoustic success still require your device test.
7. If a complete message is not recovered, the app says so. It does not display a guessed message. Try Raw, move the devices closer, reduce competing sound and capture the entire transmission. There is no automatic acoustic ACK/retry or error-correcting code yet.

The trusted laptop performs encoding/decoding and receives the passphrase over the local HTTP session. Encryption protects the acoustic payload; this is not an end-to-end encrypted Wi-Fi connection. Do not expose the service to the public internet.

## 4. Send an image or audio through either path

**Wi-Fi:** In AcousticLink choose a file and **Send original by Wi-Fi**, or use **Transfer & chat**. On the other screen the shared file appears. Use **Receive & verify bytes**. WAV files offer **Save & analyze WAV**. File exchange is bidirectional through laptop storage; it is not a direct phone-to-phone service.

**Sound:** Choose a file no larger than **8192 bytes**. Generate its encrypted sound, then decode the received WAV. The shared reconstructed inbox shows the original hash, downloadable bytes and supported image/audio previews. Reconstructed PCM WAV offers **Save & analyze in Audio Studio**. A received fundus image can be saved to Retinal Image Lab after confirming permission.

Large retinal photos and normal voice notes take too long for this teaching modem. Use Wi-Fi for the full original. **Create small teaching image copy** explicitly selects a resized 64 × 64 JPEG without modifying the original. It demonstrates byte reconstruction only and is unsuitable for retinal analysis. The included 1175-byte teaching image generated 36.100 seconds of modem audio in the checked run.

Recording spoken “hello” transfers a voice recording. It does **not** automatically turn speech into the written word “hello”; speech recognition is not installed. Typed text reconstructs as text. Audio files reconstruct as audio. The new native recorder saves 16 kHz mono PCM; normal voice notes should use Wi-Fi because they quickly exceed the acoustic payload limit.

## 5. Compare filters on exactly the same received samples

Upload `Orbit-Link-Hello-Encrypted.wav` or `Orbit-Link-Hello-Noisy.wav`, enter the public test key above, and select Raw. Then change the filter and choose **Re-run same receiver WAV**.

- Band-pass: fourth-order Butterworth, 800–2800 Hz, retaining both modem tones.
- Low-pass: fourth-order Butterworth at 1700 Hz; it attenuates the 2400 Hz symbol and can hurt reception.
- Notch: 50 Hz, Q = 30, for mains hum.

Raw and filtered CRC-valid packet counts are measured on the same supplied WAV. Both clean and simulated-noisy supplied examples recovered 2/2 packets for all four choices in the native check; **no decoding improvement was demonstrated**. A truncated recording and silence do not recover a complete message in automated tests.

The noisy sample adds generated 50 Hz hum and seeded Gaussian noise. This is a **simulated audio impairment**, not a measured physical channel. Digital RMS/peak are in dBFS; they are not Wi-Fi RSSI. FFT plots show audio spectral energy. BER is withheld without aligned reference bits.

For a timing comparison, send the **same selected payload** by Wi-Fi and generate sound without changing it. The app compares hashes and shows browser wall time versus generated audio duration. A duplicate-file receipt is not a new transfer measurement. Localhost is not a radio measurement, and this comparison does not establish 802.11ax or AX+BF superiority.

## 6. Audio filtering and mixing

1. Send `Orbit-Audio-Demo-Generated.wav` through Transfer & chat. Choose **Save & analyze WAV** on the laptop. It contains generated 350 Hz and 3600 Hz tones, 2 seconds, 16 kHz.
2. Inspect the waveform, Welch power spectrum and spectrogram. Apply Butterworth low-pass at 900 Hz and save a copy. The high tone should be attenuated; listen to both versions and inspect their actual spectra.
3. Select the original as A, choose another saved recording as B in **Two-track mixer**, set gains and choose A+B or A−B. Save the mix and inspect/play it.
4. For a deterministic demonstration choose the same input as A and B, gains 1 and 1, subtract. The saved result is silence. This is known-track cancellation, not blind separation of unknown voices.
5. B is resampled to A's sample rate, starts align, mono is duplicated for stereo and shorter tails are zero-padded. Clipped PCM16 samples are counted. Input files are preserved, and both parents block permanent deletion while linked mixtures exist.
6. Optional **Compare in MATLAB** uses the existing documented same-input FIR comparison when licensed MATLAB is available. This release does not add a new Simulink model.

## What to tell your professor

“My original project uses saved Wi-Fi 6 CSI to study human presence. DSP conditions the CSI before feature extraction and classification, and I evaluate on held-out recording dates. That remains the core sensing experiment.

“I added a connected signal laboratory around it. The phone sends original data to the laptop, the shared Library preserves it, and each processing step saves a new result. Audio filtering operates on sound samples; retinal segmentation operates on image pixels. These are DSP extensions, not CSI measurements.

“AcousticLink lets me inspect a communication chain: bytes, encryption, framing, modulation, received samples, filtering, demodulation, authentication and reconstruction. I compare the exact file hashes. A failed decode remains a failed decode.

“Wi-Fi is the practical transport for larger files; this simple sound modem is a low-rate educational channel. Our upload graphs measure accepted bytes, not radio signal strength. I keep recorded CSI evidence and archived SAGE simulation results separate from this file-transfer demonstration.”

## Verification and remaining work

`python -m pytest tests -q`: **122 passed**, one upstream Starlette TestClient deprecation warning, 122.94 s. TypeScript/Vite production build passed with the existing large-chunk advisory. Scoped Ruff passed. Native Windows tests used two authenticated HTTP clients and an isolated temporary database; generated text/image WAVs were reconstructed and hashes checked. APK 4.2 compiled, signed, aligned and passed 13 server-address checks. See `Orbit-4.2-Native-Test-Output.txt` for observed run values.

**NOT EXECUTED:** installation/recording on a physical Android phone, speaker-to-microphone acceptance in your room, Wi-Fi 6 PHY comparison, speech transcription, arbitrary-source separation, live CSI capture and clinical validation. These must not be described as completed measurements. Live calls, AgentLink, acoustic FEC/automatic retransmission and broader DSP practicals remain separate roadmap work.

Source run: `python launch_orbit.py --lan`; existing Windows run: `Start-Orbit-Server.cmd`. Developer build: `npm --prefix frontend run build`. Preserve source labels, held-out validation and local-server access when extending the app.
