# Orbit completion verification

This continues the existing Orbit app. Step 1 findings remain in step1_audit.md as historical evidence; steps 2–6 are now implemented.

Executed locally on Windows: 80 pytest tests passed (102.47 s), one upstream Starlette TestClient deprecation warning; TypeScript/Vite build passed (bundle-size advisory); application Ruff scope passed; fresh CPython 3.10 venv installed 27 pinned wheels with --no-index, pip check and scientific imports passed. Native Windows executable self-test passed HTTP health, one-use bootstrap login, NumPy/SciPy/sklearn/HDF5, own FFT and LR/RF/MLP fitting. The native window was opened and inspected. Android compilation, zip alignment, v2/v3 signatures, strict private-IP policy and 13 address checks passed.

Saved demo: 27 recorded captures including the prior upload rehearsal; 24 separately labelled simulation captures across six sessions and three neutral day groups. Seven current recorded models, seven legacy artifacts and four Simulation models preserved. Simulation is excluded from Evidence. Generated activity labels describe channel settings, not a validated activity classifier.

Run: extract the Windows bundle and open Orbit/Orbit.exe. Start-Orbit-Server.cmd or Orbit.exe --server retains the LAN server for paired phones. Python source fallback: python launch_orbit.py --offline. Tests: python -m pytest tests -q.

Limits: physical Android installation, share receiver, phone-to-laptop Wi-Fi/firewall conditions and an independent clean Windows machine are NOT EXECUTED. CI is configured; hosted completion is not assumed. Live CSI capture, through-wall detection and native 802.11bf remain unverified. The phone scientific workspace requires the laptop server. Offline guide is rule-based. Heuristic fuzzy fusion is not calibrated or independently validated. Cancellation waits for the current numerical fit to return. Numeric imports need consistent array layout and explicit labels/session metadata; unsupported layouts are rejected. APK cleartext is pinned to build-time private IP addresses and may require rebuild after network changes. mDNS depends on the local network.

Commit: Complete Orbit imports, Simulation, phone pairing, DSP/SC tools, themes and native Windows packaging.
