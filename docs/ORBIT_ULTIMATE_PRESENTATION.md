# A practical faculty demo

Start in Connect. Explain that the laptop hosts the shared workspace and phone is a client. Pair with a fresh QR; the server remains local.

Open Transfer & chat. Send a small real file from phone, receive/verify on laptop, then reverse. Point to matching SHA-256 and client-reported accepted-payload time/rate. Re-upload a saved download to check actual saved bytes. Say: hashing detects changed bytes; it is not encryption. Show pause/resume and duplicates without inventing speed results.

Chat tab: send text each way and attach a verified file. Explain loaded-session acknowledgements. Do not say calls or video conferencing are implemented.

Acoustic modem: run short text through simulated loopback. Explain UTF-8, frame length, preamble/sync, 1200/2200 Hz tones at 100 bit/s, noncoherent energy comparison, timing-phase search and CRC32. Show transmitted/recovered bits, waveform, FFT and spectrogram. Simulation is not proof of a physical acoustic link. Generate speaker WAV and perform actual microphone capture only when hardware/secure-context conditions allow. No autonomous AI or encrypted sound claim.

Use existing SDR & spectrum for AM/FM computed audio, or Signal Studio / DSP & SC tools for stored CSI DSP. Use Research Journey for archived SAGE/SmartCSI figures and printing. The new communication tools do not reproduce or change archived research metrics. MATLAB R2026b exists but Engine/license execution remains pending; use Python DSP as the honest current fallback.

Questions: What does SHA-256 prove? Equality of received bytes against original digest, not confidentiality. What is CRC? Frame error detection, not cryptographic authentication. Is this live CSI? No; network file transport/acoustic data and CSI sensing are different tasks. Is the throughput Wi-Fi PHY speed? No; accepted application payload divided by measured client wall time. Does CRC-valid imply zero errors on all tests? No; failed frames remain failures and CRC is finite error detection. What remains? Physical-device acceptance, calls, AgentLink, live SDR and MATLAB/Simulink integration.
