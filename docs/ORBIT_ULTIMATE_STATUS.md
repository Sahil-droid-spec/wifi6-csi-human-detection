# ORBIT Ultimate checkpoint

## 2026-11-07 · retinal image experiment

Retinal Image Lab accepts a consented uploaded fundus JPEG/PNG or an explicitly generated test image. Both phone and laptop can request Python or licensed MATLAB processing from the laptop server. The preview includes enhanced contrast, vessel response, a binary candidate mask and an overlay. Users can save the original and derivatives into the existing Lab notebook, reopen them across sessions and delete the saved set from the laptop.

Verification used generated geometric input only. The full suite passed 117 tests. Windows native runtime preview, original-byte preservation, two authenticated software sessions and deletion passed. Python's first 256 × 256 test run measured 867.53 ms, including decoding and PNG encoding. MATLAB R2026b with Image Processing Toolbox completed the generated test in 103,949.69 ms including startup. These are individual observed runs.

Genuine fundus segmentation quality, physical Android use and continuous retinal-camera capture remain unverified. The current mode processes individual images. Clinical assessment and reference-based segmentation metrics require appropriately licensed fundus photos and expert masks. See [Retinal Image Lab](retinal_image_lab.md).

## 2026-11-05 · integrated transfer, audio and CSI experiment

| Workflow | Status | Evidence |
|---|---|---|
| README research gallery and progress | Published on main | Original figures and setup retained, with links to archived protocols. |
| Transfer timeline | Implemented and software-tested | Actual server-accepted chunk offsets and timestamps, visible during upload. Old transfers without observations have no fabricated history. Duration and throughput cover observed chunks. |
| WAV → Library → Audio Studio | Implemented and software-tested | Verified WAV import, reusable media ID, original and derivative playback/export, waveform, PSD, spectrogram, rename, Trash, restore and permanent delete. PCM16 mono/stereo at 8–48 kHz, up to 60 s and 12 MiB. |
| Library WAV → MATLAB | Verified in the Windows build | The first 2,048 samples of a generated transferred WAV passed the same-input comparison (maximum absolute difference 2.22045e-16). Channel 1, 63-tap Hamming FIR at 1,200 Hz. MATLAB is optional. |
| Matched recorded CSI comparison | Verified on a saved cohort | Same Random Forest, amplitude feature contract, validity mask and two leave-one-date-out folds. 15 labelled 20 MHz AX recordings. |
| Physical phone and acoustics | Needs physical devices | Android pairing, bidirectional transfer on a handset, phone microphones, secure calls and physical sound delivery remain unverified. |

The recorded Hamming run fixed 15 taps and a cutoff of 0.08 cycles per packet before training. Baseline: 10/15 accuracy, 0.6786 balanced accuracy, presence F1 0.7059, four false alarms and one miss. Hamming: 11/15 accuracy, 0.7500 balanced accuracy, presence F1 0.7778, four false alarms and zero misses. The difference is one recording in this two-date cohort. Replay uses this experiment's own held-out window predictions. The older notebook's moving-average and SmartCSI results, and the SAGE ns-3 experiments, remain separate.

The new WAV lifecycle operates on saved Library entries. Any copy in Transfer & chat is independent. Broader multi-format routing and recording lifecycle, encrypted acoustic transport and AgentLink, seven fully connected DSP/MATLAB practicals, live SDR, live CSI, calls and advanced camera research remain tracked in [the checklist](ORBIT_PROJECT_CHECKLIST.md).

### Earlier checkpoint

2026-11-04. Existing app preserved; feature inventory: ORBIT_ULTIMATE_FEATURES.json. Branch checkpoint/ultimate-20261104 preserves baseline. No Downloads installation or archived datasets modified. Runtime database backed up separately before testing new release.

COMPLETED: generic hash-verified resumable file exchange, persistent two-session text/attachments, load acknowledgements, received-byte receipts, RTT probe, server session expiry; BFSK framing/CRC/timing, generated waveform, noisy simulation and PCM WAV decode, explicit secure-browser microphone UI. APK general-transfer workflow and current exact LAN address updated. No generative AI, live calls, RF hardware or MATLAB execution falsely enabled.

VERIFIED: transfer/API regression tests and acoustic codec tests; final aggregate results in ORBIT_ULTIMATE_TEST_RESULTS.md. Physical phone/recording tests require the procedure in ORBIT_ULTIMATE_HARDWARE_SETUP.md. No acceptance based on screenshots alone.

KNOWN ISSUES: browser download buffers up to 256 MiB; memory-limited phones should use direct save and re-upload to verify saved bytes. Resume is per file, at chunk boundaries; folder selection uses ZIP. Native microphone capture requires secure browser context; APK has no mic integration. Audio codec uses simple timing search and CRC, not error-correcting code. Current metrics are client-reported payload statistics; no radio counters/aggregate reliability claim. Server expiry also changes client session identity on re-pair. MATLAB exists but Engine/license execution is pending.

NEXT: perform physical phone roundtrip/CRC acoustic checks, then AgentLink negotiation and remaining milestones from roadmap. Repeat only checks justified by a new change/failure. Resume command: python -m orbit --lan; source frontend npm --prefix frontend run build; tests python -m pytest tests -q. Distributions use external app-source/orbit plus existing native runtime; keep orbit-data. Never place private assets/secrets in remote Git.
