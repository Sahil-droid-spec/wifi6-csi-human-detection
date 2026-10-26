# Orbit — Wi-Fi Sensing Lab

A local lab for recorded Wi-Fi CSI, DSP, model comparison and clearly separated simulation experiments. The phone and laptop share the same local server and saved library.

## Windows application

Extract the Windows download fully, then open **Orbit.exe**. It includes Python and the scientific runtime. The native window uses Microsoft Edge WebView2. Keep the app open while using your phone.

For a server without the desktop window, run **Start-Orbit-Server.cmd**, or:

    Orbit.exe --server

Use --port 8766 for another port, or --local-only to disable LAN binding. The app does not change firewall rules; allow the private-network prompt yourself when appropriate.

## Phone

Install the APK, then create a one-use QR in **Connect** on the laptop. Scan/open the link on the phone; pairing avoids entering the session code. The app reconnects while its session remains valid. Android Share → Orbit accepts files; choose them in Import wizard. Offline examples can be saved from the app connection screen.

The APK permits HTTP only to its build-time private laptop IPs. If an IP changes, rebuild with --lan-host or use the phone browser. orbit.local discovery depends on mDNS; numeric LAN URLs remain available. The phone scientific workspace requires the laptop server.

## Source / offline Python launch

Windows x64 CPython 3.10:

    python tools/prepare_offline.py
    python launch_orbit.py --offline --lan

The first command prepares wheels online; the downloadable source bundle already includes them. Add --check-install to verify dependencies without starting the server. Other Python versions need matching wheels. The frontend is prebuilt; development uses npm ci and npm run build in frontend/.

## Workflow

Home → Library (files, folders, ZIP, MAT, numeric CSV/NPY/NPZ) → Signal Studio → Learning Lab → Replay. Use Import wizard for missing metadata. Uploads resume by hash/offset; duplicates are detected. Inbox collects phone imports and manual tap labels. Removed datasets can be restored from Inbox.

Simulation contains generated empty/still/moving/two-person channels. It has a separate library/models and a visible Simulation chip. Generated outputs always retain synthetic=true; they are excluded from Evidence. Recording plan prepares balanced real-lab sessions with consent and metadata checks.

DSP & SC tools extends filters, FFT, aliasing, pole-zero views, convolution, spectrograms, the ANN ladder, SOM, fuzzy defuzzification, quality gating, nested GA DSP search and heuristic model fusion. Orbit guide is offline rule-based help, not an external AI model.

## Validation and limits

Replay defaults to saved outer-fold predictions. Scaling, GA feature selection and tuning exclude held-out recordings/dates. Final-model inference is explicitly labelled. Metrics carry validation protocols; small datasets and date/class confounding remain limitations. Simulated results do not establish real-world accuracy. No verified live CSI, through-wall detection or native 802.11bf support is claimed.

Run python -m pytest tests -q and python -m ruff check orbit tests tools desktop.py build_desktop.py launch_orbit.py. Verify file bytes with python tools/checksums.py --verify. See CHANGELOG.md, docs/step1_audit.md and [the preserved research history](docs/research_history.md).
