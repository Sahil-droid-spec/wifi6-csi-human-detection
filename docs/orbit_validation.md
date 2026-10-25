# Orbit implementation & validation record

Built against repository main commit `40e3f9c9a465d39cd7b53e7907985cf2173c88cd` on 25 October 2026.

The supplied Python export, notebook, research-results archive, both handoff archives, pasted feature brief and two-page PDF were reviewed. The latest complete brief supplies the palette and local application scope; earlier Ripple PDF styling was not reused. Existing research artifacts are preserved.

## Implemented

- React + TypeScript intro, circular 8-stage workspace, desktop rail and phone navigation; opaque midnight/slate palette, accessible focus, reduced-motion behavior and source labels.
- Local FastAPI service, private session code, loopback default, explicit trusted-LAN mode, phone upload page/QR, shared persistent library, upload progress/cancel and validation jobs.
- Bounded multipart uploads, safe ZIP extraction, compound/complex HDF5 parsing, nearest-parent metadata, cache/original separation, quality audit and partial-import reports.
- Genuine CSI traces, selectable subcarriers, packet navigation, heatmaps, inspection-window controls, feature values and correlations.
- Python DSP operations: moving average, FIR windows, Butterworth, filter shootout, direct DFT vs tested radix-2 FFT, convolution, multirate, Hilbert envelope, STFT and coefficient quantization demo. Local saved metrics and PNG exports.
- Date/capture-grouped LR/RF/MLP training, model manifests/artifacts, independent fold evidence, MLP loss, nested GA/RF with matched all-feature and random-feature baselines, editable educational fuzzy rules and centroid defuzzification.
- Offline playback, valid-model inference with schema/bandwidth/modulation checks, window timelines, uncalibrated probability labels and in-training provenance.
- Historical results, confusion matrices, quality audits, fold details, transfer and AX/BF simulator tables loaded from the repository CSVs; CSV/manifest downloads and run history.
- Prebuilt frontend, cross-platform Python bootstrap, Windows launcher, run guide and GitHub Actions checks.

## Checks performed

- `python -m pytest tests -q`: **31 passed** in the local Python 3.10 test environment. One upstream Starlette TestClient deprecation warning; no failing tests.
- `npm run build` in `frontend`: TypeScript and Vite production build passed. The ECharts-containing bundle triggers Vite's size advisory; this is a local served asset, with no CDN dependency.
- `git diff --check`: passed.
- Launcher `--help`: passed; normal application module startup and HTTP service verified.
- Browser: protected pairing, 1440-pixel desktop overview, 390-pixel phone breakpoint, navigation, actual DSP calculation (three canvas charts), and fuzzy input change (centroid 0.510 → 0.828) verified. No browser console errors in checked session. DOM width checks showed no horizontal page overflow. Phone ring bounds were corrected after visual review. Screenshots are supplied with the delivery.
- API tests: valid/invalid imports, source HDF5 links, ZIP traversal/symlinks/duplicates, decoded shape, feature order/adjacency, DSP references, fuzzy outputs, authentication/origin/host/rate checks, upload body bounds, exports, deletion, model fit/predict, 20/40 MHz mismatch, GA inner grouping/random baseline, restart persistence and explicit SQLite handle release.

## What these checks do not establish

No raw MAT recording was included in the attachments or repository. Parser and model tests use generated complex HDF5 fixtures; they do not reproduce the original research's 20/40 MHz scores or establish real-world presence performance. Historical records stay clearly separate from these new local computations.

A physical phone/LAN transfer, live CSI capture, physical 802.11bf hardware and through-wall detection remain unverified. Adaptive hardware selection is proposed. The fuzzy page is an educational system, not recovery/validation of the earlier trained fuzzy detector. PCA/ANOVA/clustering/SOM, physical-rate calibration and GA DSP tuning remain future extensions. See `orbit_run_guide.md` for complete scope and limitations.

The packaged-release HTTP smoke check also passed for HTML, compiled assets, authentication, evidence rows and a clean capture library. A Windows cleanup check exposed unclosed SQLite connections; the final implementation explicitly closes them and a retained-handle regression test covers this lifecycle.


## v1.1 validation and supplied-data run

36 backend tests pass, covering media MIME/extension checks, paired media, file-range playback, optional user-declared MAT profiles, local-only large imports, project references, sharing on/off protection and classifier comparison, in addition to the prior numerical/security tests. TypeScript/Vite build passes.

The newly supplied 20MHz.zip and 40MHz.zip were actually imported: 15/11 captures and 1,920/382 accepted windows respectively. Seven models were fitted locally (20 MHz date-held-out LR/RF/MLP/GA+RF; 40 MHz capture-held-out LR/RF/MLP). Local app results are distinct from the historical CSV records and preserve the small-date/date-class-confounding caveats. Raw recordings, media, session codes and generated models were excluded from GitHub.

Browser QA exercises the saved-data flow, real-model comparison, all four themes and phone-sized saved-data navigation. Physical phone transfer still requires a device/network check. Images/videos are stored as contextual media rather than treated as CSI.
