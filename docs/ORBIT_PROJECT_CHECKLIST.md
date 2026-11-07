# Orbit project checklist

Build order: **phone transfer and shared Library → Wi-Fi presence pipeline → DSP practicals and audio tools → camera/image extensions → live hardware validation.** Keep one experiment workspace with tabs for input, processing, graphs, and results.

## One project, shared data

The core project is human presence detection from saved Wi-Fi 6 CSI. The DSP question is whether a filter or a new feature helps detect presence on a recording date left out of training.

**Phone or laptop → Library → choose one recording → DSP → features → model → Replay → Evidence.**

The Lab notebook should hold related graphs, camera clips, audio, and screen recordings. Phone transfer is how files arrive. Camera and audio use the same workflow for experiments with different signals. MATLAB compares selected operations against Python on the same input.

## 1. First demo and research pipeline

- [x] Import compatible saved CSI from the laptop. Label generated CSI as Simulation and keep it separate from recorded evidence.
- [x] Pair by QR, transfer ordinary files, check SHA-256, and show byte progress. Verified with two software clients on the laptop.
- [ ] Verify pairing, upload, and receive on a physical Android phone. Repeat on the laptop hotspot.
- [x] Apply a Hamming-window low-pass FIR to a selected recording in Signal Studio and inspect the trace and spectrum.
- [x] Add a **Presence Detection Experiment** page with a fixed-configuration matched run and a held-out window inspector.
- [x] Reset the causal FIR at invalid gaps, carry state within contiguous valid spans, and show nominal filter delay and quality exclusions.
- [x] Compare the current preprocessing baseline with a Hamming FIR variant using the same Random Forest, features, labels, and held-out dates.
- [x] Plot raw and filtered signals on shared axes and report real held-out verdicts, balanced accuracy, false alarms, misses, and skipped windows.
- [ ] Add saved experiment navigation from standard Replay and Evidence and training-only tuning for additional filter candidates.
- [ ] Test one new feature at a time, starting with frequency-band energy. Then compare GA feature selection or ANN separately so each change has a measurable contribution.
- [ ] Capture real lab CSI with a compatible and verified capture setup. Collect empty, still-person, and moving-person recordings in independent sessions. Use empty versus present as the first classifier task. Evaluate still versus moving separately when there are enough labelled sessions.

## 2. One library for recordings and results

- [x] Lab notebook accepts uploaded media. Camera Studio offers an explicit preview, save, or discard workflow for local captures. Phone exchange can receive ordinary files.
- [x] Save a verified transferred WAV to the shared media Library and open it in Audio Studio.
- [ ] Extend **Save to Library** and **Discard** to general transferred files, camera, microphone and screen recording. Show source and related CSI metadata.
- [ ] Add **Open in** actions for Signal Studio, Audio Studio, Camera Studio, MATLAB Studio, Replay, and Lab notebook based on file type. Keep the source bytes and save edits as new versions with settings and a link to the original.
- [ ] Add screen recording with the browser or OS picker, a visible recording indicator, an explicit stop button, and a local save or discard choice. Verify on Windows. Phone screen recordings can be captured with the phone's recorder and then uploaded.
- [x] Add WAV Trash, restore and permanent delete on the laptop. The original cannot be permanently deleted while linked derivatives exist.
- [ ] Extend this lifecycle to other formats and add an explicit transfer-copy retention policy.

## 3. Phone transfer graphs

- [x] Plot cumulative server-accepted bytes and interval/average throughput. Show sender session, offset conflicts and end-of-transfer SHA-256 verification. These are application measurements.
- [x] After verification, offer **Save & analyze WAV**. Show the waveform, spectrum and spectrogram from the selected Library WAV.
- [ ] Add contextual import/analysis for verified CSI, image, video and I/Q transfer items.
- [ ] Optional teaching demo using one audio clip. Transfer the original, filter it, then send the derived file back so the class can hear the difference.

## 4. DSP practicals and MATLAB equivalents

| Practical | In Orbit 4.1 | To add |
|---|---|---|
| 1. Generate basic continuous-time signals | Teaching signal available in DSP. | MATLAB and Python examples for sine, cosine, step, and ramp. Display a dense time grid and the selected sample points. |
| 2. Sampling theorem and aliasing | Naive versus anti-aliased decimation and spectral comparison available. | Adjustable signal and sample frequencies. Plot where the aliased tone lands and show what changes with an anti-alias filter. |
| 3. N-point DFT magnitude and phase | Direct DFT and radix-2 FFT comparison plus magnitude available. | User-selected DFT length and separate magnitude and phase plots. Flag phase where magnitude is near zero. |
| 4. Linear and circular convolution | Both implemented. | User-defined sequences and circular length, plus a short wraparound example and MATLAB comparison. |
| 5. FIR low-pass and high-pass with windows | Windowed low-pass FIR and generated MATLAB FIR comparison available. | Windowed high-pass and matched comparisons for Hamming, Hann, Blackman, and Kaiser. Show impulse and frequency response and use sample rate or cycles per packet as appropriate. |
| 6. Butterworth low-pass and high-pass | Low-pass, high-pass and band-pass available. | Design from passband and stopband specifications, then measure the actual response and compare it with MATLAB on the same input. |
| 7. Hilbert transform and analytic signal | Hilbert envelope available. | Plot the original, Hilbert component, analytic signal envelope, and a known AM teaching example. Keep amplitude-derived plots distinct from measured CSI phase. |

- [x] Compare the first 2,048 samples or fewer of a Library WAV in actual MATLAB and SciPy with identical Hamming FIR coefficients. Local licensed MATLAB is optional.
- [ ] Extend MATLAB support to more Library formats and operations and persist comparison outputs.

## 5. Added DSP and communication tools

| Tool | Current starting point | To build and plot |
|---|---|---|
| Fourier | Direct DFT, radix-2 FFT, magnitude spectrum, and STFT. | Select N, window, and sample rate. Plot the time signal, magnitude, phase, and spectrogram. Add inverse reconstruction and a known-tone check. |
| Laplace | Existing digital pole-zero plots provide a starting point for teaching system response. | Add a continuous-time **s-plane** lab using step and exponential examples, transfer functions, poles and zeros, and step/impulse responses. Label the s-plane separately from the digital z-plane. |
| Sampling | Naive and anti-aliased decimation, plus interpolation. | Plot the teaching signal, sample points, reconstructed waveform, and spectrum. Compare below, at, and above the Nyquist rate with the selected signal and sampling frequencies visible. |
| Quantisation | Q15 FIR coefficient quantisation demonstration. | Add sample quantisation with bit depth and input range controls. Plot original, quantised, and error waveforms, with measured clipping and SNR when the reference and error permit it. |
| Forward error correction (FEC) | Acoustic BFSK modem with CRC error detection. | Add Hamming (7,4) coding and an optional interleaver in a separate simulation. Use extended Hamming (8,4) for a single-error correction and double-error detection demo. Compare uncoded and coded runs on a seeded error channel. Plot transmitted and recovered bits, actual block outcomes against the known input, and BER versus noise or flip rate. Include frame failures and coding overhead. CRC checks integrity. FEC attempts recovery. |
| Audio analyser | Acoustic modem can analyse a supported WAV and plot a waveform, spectrum, and spectrogram. | Open any supported saved WAV in Audio Studio. Plot time signal, magnitude/phase, and spectrogram. Add filter previews, A/B listening, and linked WAV export. |
| Mixer | Planned. | Mix two WAV tracks with independent gain, mute, and alignment. Use a common sample rate and explicit mono/stereo handling. Plot each input, the mixed waveform, its spectrum, and peaks or clipping. Preview and save the mix locally. |

- [ ] Give each graph a title, axis units, and source label. Show before/after on comparable axes and allow local plot and data export. Use seconds and hertz for a known sample rate, or packet index and cycles per packet for CSI without verified timing.
- [ ] Keep transfer graphs in the transfer panel and processing graphs with the experiment. Prefer one useful preview per tool and put extra graphs under **Inspect graphs**.

## 6. Audio and image labs

- [x] **Audio Studio.** Open a supported PCM16 WAV, compare playback, inspect waveform/spectrum/spectrogram, and save linked low-pass, high-pass, band-pass, notch, and Hamming FIR variants.
- [ ] Add opt-in microphone capture and the two-track mixer.
- [ ] **Image Studio.** Open a saved image for contrast, sharpening, smoothing, edge detection, and a simple segmentation exercise. Send the same input to MATLAB and save the result and settings alongside it.
- [x] **Educational pulse-signal lab.** Camera Studio has opt-in facial RGB analysis and quality checks. Live capture and reference validation remain to be done.
- [ ] Add consented recorded-video input and comparison with a user-supplied synchronized reference. Show quality checks, estimates withheld for poor signals, and errors only when a reference was actually provided. Keep this educational.
- [x] Add a consented Retinal Image Lab for uploaded fundus photos, with Python and optional licensed MATLAB processing, enhancement, vessel-candidate masks, overlays and shared media Library outputs. Software checks use generated geometry.
- [ ] Validate retinal segmentation on appropriately licensed fundus photographs and independent expert masks. Add reference-based Dice/sensitivity/specificity and dataset-level comparisons only after collecting suitable annotations.
- [ ] Assess live retinal capture with a compatible fundus camera or phone attachment. The current experiment processes individual uploaded photos through the laptop server.

## 7. Later hardware and communication milestones

- [ ] **Physical AcousticLink.** Verify normal UTF-8 BFSK both directions over speaker and microphone. Then add bounded chunking, actual return-path ACK/NACK, retry, ordering and final hash. Add same-RX filter comparisons and software/device evidence separately.
- [ ] **Encrypted AcousticLink.** Use authenticated pairing and vetted AEAD with nonce uniqueness, tamper and replay checks. Verify sound-only payload delivery with Wi-Fi disconnected after key exchange.
- [ ] **AgentLink.** Add protocol negotiation and real acoustic exchanges; optional AI inference follows deterministic protocol testing. Verify licenses for any third-party modem. Keep transcription and original audio bytes separate.
- [ ] **Digital communication.** Add reproducible ASK, PSK, QAM, DPSK and OFDM labs with channel models, constellation, PSD, pulse shaping, eye patterns, synchronization and BER/SER with reference bits.
- [ ] **SDR and research.** Continue generated and recorded I/Q workflows with Library integration; verify supported receive hardware separately. Keep the SAGE V3 matched ns-3 results, BF report-rate decline, SARA negatives and archived SmartCSI cohorts distinct from app experiments.
- [ ] **Final demo and release.** Add stable experiment IDs, exports with provenance, optional PDF and presentation mode. Run clean Windows/offline and physical Android acceptance before claiming hardware completion.
- [ ] Verify a real CSI capture adapter and driver on a known setup before adding live capture or streaming inference.
- [ ] Validate secure phone audio/video calls and live camera sharing on physical devices, with explicit consent and recording off by default.
- [ ] Keep a short record of the tested dataset, command, output, and limits whenever an item moves to done.
