# Orbit v1.1 update

See [the classroom demo guide](orbit_demo_guide.md) for saved datasets, Learning Lab, themes, media and phone setup. CSI uploads now support up to 2 GiB and safe archive expansion is capped at 4 GiB. Media files support up to 1 GiB. The Windows `Start-Orbit-Server.cmd` launcher enables LAN binding; an authenticated laptop-only Sharing control enables/disables remote requests. Theme and presentation preferences persist in each browser. Raw datasets and generated models remain local and are not in the repository.

The earlier 256 MiB/1 GiB limits and missing-input description below record the v1.0 baseline; these limits and the absence of locally supplied data were superseded by v1.1. Scientific contracts and hardware validation limits still apply.

# Running Orbit

Orbit is a local React/TypeScript application with a Python FastAPI analysis server. The repository includes a prebuilt frontend, so Node.js is needed only when changing the UI. Python 3.10+ is required; Python 3.11 is recommended for a clean installation.

## First launch

From this repository directory:

```powershell
python launch_orbit.py
```

On Windows you can also double-click `Start-Orbit.cmd`. The launcher creates `.venv/`, installs the pinned scientific dependencies from PyPI on first use, and starts Orbit. Installation needs internet access; after setup, analysis does not require cloud services.

Open **http://127.0.0.1:8765** and enter the session access code printed in the terminal. The code is generated afresh at each start. Keep the terminal running; Ctrl+C stops the server.

## Phone upload

```powershell
python launch_orbit.py --lan
```

Connect the phone and laptop to the same trusted Wi-Fi. In **Server & settings**, scan the QR code or open a displayed private LAN address. Enter the same terminal access code, then select a `.mat` recording or supported dataset ZIP. If Windows Firewall prompts, allow Python on private networks only. Some guest networks isolate devices; move both devices to a network that permits local communication. Do not use router port forwarding or public tunnels.

LAN mode binds to available interfaces, but request Host addresses are limited to loopback/private addresses and every data API requires a session cookie. This is basic trusted-LAN protection, not a hardened public server. Plain HTTP does not encrypt trusted-LAN traffic. Live target-hardware CSI capture is not available.

## Supported input and provenance

- MATLAB v7.3 / HDF5 `.mat` with a 2-D `capture` dataset: complex values or compound `real` / `imag` fields.
- 256 subcarriers at 20 MHz or 512 at 40 MHz; the parser checks/transposes known axes rather than guessing based on the shorter dimension.
- A ZIP may contain folders of captures and a nearest parent `config.json`, for example:

```text
20MHz/
  0people/2024-07-12/config.json
  0people/2024-07-12/capture0.mat
  1people/2024-07-12/config.json
  1people/2024-07-12/capture0.mat
```

```json
{"modulation":"ax","bandwidth":20,"people":{"present":true,"num":1}}
```

Use the actual label for each folder. Dates are read from paths or the config `date`. Unlabelled single MAT files are inspectable; training/inference needs verified AX modulation and bandwidth. Uploading data never executes it. Arbitrary MAT schemas, PCAP, external HDF5 storage/links, and external pickle/model uploads are unsupported.

Limits: 256 MiB compressed upload; 1 GiB expanded archive; 2,000 archive entries; 100 captures per import; 256 MiB decoded array per capture. ZIP paths, duplicates, links, expansion ratios and decoded sizes are checked. A partial import reports skipped/rejected members. No capture inventory is registered when every file fails.

## Scientific workflows

**Data:** import, inspect metadata, invalid/all-zero packets, SHA-256, capture labels, selectable subcarriers, trace ranges and sampled heatmaps. The display can be sampled; model calculations use full accepted data.

**Signal Studio:** explicitly choose recorded CSI or a seeded teaching signal. Moving-average FIR, windowed FIR, filter shootout, Butterworth low/high/band-pass, direct DFT/radix-2 FFT comparison, linear/circular convolution, anti-aliased decimation/interpolation, Hilbert amplitude envelope, STFT, Q15 coefficient demonstration. Each control recomputes in Python after pressing Recalculate. Plot axes use packets/normalized frequency; an envelope is not measured CSI phase. Q15 accumulation is floating point. Inspection window/hop controls are separate from model contracts. Save experiment settings/metrics locally; export charts as PNG.

**Soft Computing:** train LR, RF and MLP on compatible labelled datasets. Compare GA + RF against all-feature RF and matched random-feature RF. GA selection uses only inner capture-stratified folds inside each outer training set. Population, generations and mutation are bounded to keep this a laptop lab. The fuzzy system is an editable Mamdani educational sandbox, not a trained presence classifier. Feature-group plots and correlations use actual accepted recording windows.

**Models:** 20 MHz uses 256-packet windows / hop 128 and four feature blocks (mean, std, mean absolute adjacent difference, p90-p10). This retains the original zero-filled nonfinite baseline and explicitly warns about invalid data. 40 MHz uses non-overlapping 512-packet windows, minimum final length 256, >=90% valid columns, and validity-aware adjacent differences, following the latest comparison notebook. The schema is versioned separately by bandwidth. Date-held-out is the default; capture-held-out is exploratory. Training fails if an outer training fold lacks either class. Duplicate capture content is removed by hash. Model manifests preserve contracts, hashes, capture/date split provenance, library versions, losses/selected indices, capture predictions and confusion matrices.

**Replay:** play/pause, step, scrub and change display speed across actual recorded packet windows. This speed is illustrative, not the original sampling clock. Model inference checks the complete feature/bandwidth contract. The capture decision uses majority vote over window labels; mean probability is diagnostic and uncalibrated. A capture used in final fitting is marked in-training. Inference is not held-out evaluation.

**Evidence:** current repository CSVs power the historical metrics, confusion matrices, per-capture predictions, quality audits, split details, domain transfer and AX/BF simulator tables. Earlier DSP/GA/fuzzy summaries remain labelled separately. The 40 MHz date/class confound is explicit. Simulator report latency is never presented as detection accuracy or inference latency.

## Persistence and development

Runtime files live in `orbit-data/` (ignored by Git), separated into originals, parsed sources/caches and internally generated models. SQLite indexes datasets, captures, models, jobs and runs. Failed/interrupted jobs are visible; restart marks unfinished jobs interrupted. Deleting a dataset requires UI confirmation and removes its original/caches; saved model provenance remains. Dataset deletion is permanent. Back up `orbit-data/` if you need it. Do not commit recordings, session codes or generated models.

Manual setup / developer loop:

```powershell
python -m venv .venv
.venv\Scripts\python -m pip install -r requirements-app-dev.txt
.venv\Scripts\python -m pytest tests -q
cd frontend
npm ci
npm run build
cd ..
.venv\Scripts\python -m orbit
```

On macOS/Linux, use `.venv/bin/python` in place of the Windows executable. `python -m orbit --data-dir PATH --port 8765` configures storage and port. Vite's optional dev server proxies to the backend on 8765; the access code is still required. The shipping app is served on one origin with no external font/CDN requests. The ECharts bundle is sizeable but served locally.

## Validation limits and remaining work

Synthetic HDF5 fixtures test the parser, scientific functions, models and security behavior; they are not original research recordings and are not bundled as recorded measurements. The attachments contain research artifacts but no raw MAT dataset. Reproducing historical scores requires obtaining the original data and matching the recorded training configuration. The app uses a new versioned local training implementation and does not claim that reproduction has happened.

Browser checks cover desktop and phone-sized layouts and actual DSP/fuzzy interaction. A physical phone/LAN transfer, intended capture hardware, physical BF operation and through-wall detection have not been verified. Adaptive hardware selection, full-feature PCA/ANOVA/K-means/SOM, physical timestamp calibration, GA tuning of DSP filters and lossless original plot replay remain future work. The fuzzy sandbox does not reproduce the earlier trained fuzzy classifier. Historical CSVs remain the recorded evidence for those original runs.
