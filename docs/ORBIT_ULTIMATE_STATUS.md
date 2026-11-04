# ORBIT Ultimate checkpoint

2026-11-04. Existing app preserved; feature inventory: ORBIT_ULTIMATE_FEATURES.json. Branch checkpoint/ultimate-20261104 preserves baseline. No Downloads installation or archived datasets modified. Runtime database backed up separately before testing new release.

COMPLETED: generic hash-verified resumable file exchange, persistent two-session text/attachments, load acknowledgements, received-byte receipts, RTT probe, server session expiry; BFSK framing/CRC/timing, generated waveform, noisy simulation and PCM WAV decode, explicit secure-browser microphone UI. APK general-transfer workflow and current exact LAN address updated. No generative AI, live calls, RF hardware or MATLAB execution falsely enabled.

VERIFIED: transfer/API regression tests and acoustic codec tests; final aggregate results in ORBIT_ULTIMATE_TEST_RESULTS.md. Physical phone/recording tests require the procedure in ORBIT_ULTIMATE_HARDWARE_SETUP.md. No acceptance based on screenshots alone.

KNOWN ISSUES: browser download buffers up to 256 MiB; memory-limited phones should use direct save and re-upload to verify saved bytes. Resume is per file, at chunk boundaries; folder selection uses ZIP. Native microphone capture requires secure browser context; APK has no mic integration. Audio codec uses simple timing search and CRC, not error-correcting code. Current metrics are client-reported payload statistics; no radio counters/aggregate reliability claim. Server expiry also changes client session identity on re-pair. MATLAB exists but Engine/license execution is pending.

NEXT: perform physical phone roundtrip/CRC acoustic checks, then AgentLink negotiation and remaining milestones from roadmap. Repeat only checks justified by a new change/failure. Resume command: python -m orbit --lan; source frontend npm --prefix frontend run build; tests python -m pytest tests -q. Distributions use external app-source/orbit plus existing native runtime; keep orbit-data. Never place private assets/secrets in remote Git.
