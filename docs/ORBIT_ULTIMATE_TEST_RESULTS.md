# Retinal image checks · 2026-11-07

- Full suite: 117 passed, one upstream Starlette deprecation warning, 137.51 s. Scoped Ruff passed. TypeScript/Vite production build passed with the existing chunk-size advisory.
- Test images: generated geometry only. Checked binary output, excluded dark border, source labels, consent, authentication, file bounds, saved-byte identity, idempotent saves, repair after deleting one derivative, and dependency checks for deletion.
- Windows native runtime passed preview, four-image save, cross-session retrieval and delete. Python first-run processing for the generated 256 × 256 input measured 867.53 ms.
- Actual MATLAB R2026b image functions ran on that generated input, including CLAHE, median filtering, bottom-hat enhancement, adaptive binarization and morphological opening. The batch measured 103,949.69 ms including startup.
- Physical Android, genuine fundus accuracy, clinical validation and continuous retinal imaging: **NOT EXECUTED**.
- Browser check: uploaded the generated geometry fixture, selected the Simulation source, processed a preview, inspected the mask and saved four Library entries. The input could be selected again from the saved list.

---

# Integrated transfer, WAV and CSI checks · 2026-11-05

- Baseline: `python -m pytest -q tests` → 112 passed. Updated suite → 115 passed. Both runs reported one upstream Starlette TestClient deprecation warning.
- `npm --prefix frontend run build` → TypeScript and production Vite build passed, with the existing large-chunk advisory.
- Scoped Ruff → passed for the changed DSP, transport and test code.
- Two software clients: measured accepted offsets through interrupted/resumed upload, exact SHA-256, original and filtered WAV comparison, Library versioning, and Trash/restore/permanent deletion.
- Recorded CSI: 15 labelled 20 MHz AX captures, two leave-one-date-out folds, same four feature groups and Random Forest parameters, fixed 15-tap Hamming FIR at 0.08 cycles/packet. Baseline 10/15 correct (balanced accuracy 0.6786); Hamming 11/15 correct (balanced accuracy 0.7500). Both had four false alarms; misses 1 → 0. This is a single recorded cohort.
- Physical Android, acoustics, live CSI, live SDR and calls: **NOT EXECUTED**.
- Final scoped rerun after switching WAV I/O to the already-bundled SciPy runtime: 6 passed. The first native launch failed because the standard-library wave module was absent in the older frozen runtime; the corrected launch passed.
- Native Windows LAN test: 64,044-byte generated WAV, observed accepted offsets 0 → 16,000 → 64,044, exact roundtrip, analysis, filtered output, Trash, restore and permanent deletion. Licensed MATLAB matched SciPy on the first 2,048 samples of the same saved WAV (maximum absolute difference 2.22045e-16; same 63-tap Hamming FIR at 1,200 Hz).
- Isolated browser: uploaded the generated WAV, inspected the SHA-verified graph, opened Audio Studio and saved a filtered copy with independent playback and spectrogram.

---

# Executed verification - 2026-11-04

- Full application regression: python -m pytest tests -q -> 108 passed, one upstream Starlette TestClient deprecation warning, 148.64 seconds.
- Final focused acoustic/transfer checks after provenance and media-policy changes: python -m pytest tests/test_acoustic.py tests/test_communication.py -q -> 8 passed (see output log for duration). Includes authentication, hash identity, interrupted upload, persisted offset after restart, duplicate/cancel/error paths, message acknowledgements, session expiry, BFSK timing/noise/CRC corruption, stereo 44.1 kHz WAV resampling and simulation provenance.
- Frontend: npm --prefix frontend run build -> TypeScript/Vite passed. Large-bundle advisory remains. No dependency reinstallation or model retraining.
- Python Ruff checks passed for changed backend/tests.
- Real loopback TCP HTTP: two cookie-authenticated clients sent/received 9000 bytes with matching SHA-256 and message acknowledgement. This is actual local TCP, not physical phone or radio testing. Detailed measurements: outputs/Orbit-Ultimate-TCP-Check.json.
- Browser: actual file picker upload of 155-byte sample -> server hash matched -> Receive & verify -> saved download. Filesystem SHA-256 matched both original and saved copy: 014405619fd4ef8baeffd9e1b8fe3a3285a25ff7ef8fb5638879778aa72cc4a7. Chat stored a real browser message. Modem UI computed CRC-valid Hello Orbit in a labelled single-frame simulation. Grouped navigation, collapsed receipt/graph panels and numeric axes inspected.
- Windows executable self-test passed. Additional frozen-runtime server test executed the BFSK endpoint and verified a real file download through the packaged scientific runtime. Logs/JSON under outputs/Orbit-Ultimate-Frozen-*.
- Android v4.0, versionCode 6: rebuilt with existing signing identity; signature/alignment and default-deny exact RFC1918 exemptions passed; 13 server-address checks passed. Physical Android install/transfer/microphone: NOT EXECUTED.
- MATLAB R2026b installation and local Engine setup supported-version list inspected. Engine module absent from Orbit environment; license, toolboxes, Engine computation and Simulink execution NOT EXECUTED.
- No live SDR, Wi-Fi PHY metrics, real acoustic channel, AgentLink, WebRTC call, SAGE rerun or independent SmartCSI revalidation was performed. These are not passed acceptance criteria.

Known limits: client payload/time reports are not wire/PHY counters; browser verification buffers files, so memory-limited phones should use direct save and re-upload the saved copy. Browser secure contexts constrain microphones. Audio exports are PCM16 derived from analyzed samples; clipping is counted, and exported WAV should be re-decoded to evaluate that derived signal. These results are software checks, not broad communication reliability or classification accuracy claims.
