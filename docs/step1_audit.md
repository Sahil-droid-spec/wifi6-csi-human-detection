# Step 1 audit and corrections

The historical README reports GA/RF capture accuracy 0.8000 and balanced accuracy 0.8125 using two date-held-out folds; selected feature counts 8 and 12. These remain historical records, not new test results.

The earlier local app run reported 14/15 correct (0.933333...) under date-held-out evaluation. It was a different GA experiment: population 4, generations 2, Bernoulli initialization at 8% of 1024 features, no 8–60 feature repair, capture-stratified inner folds, 35-tree fitness RF, balanced accuracy minus 0.002 times selected fraction, uniform crossover and mutation 0.03. The supplied reconstruction notebook GA cell instead sets population 8, generations 4, subset size 8–60, StratifiedGroupKFold on windows grouped by capture, 50-tree fitness RF, macro-F1 minus 0.05 times selected_count/60, tournament selection, one-point crossover probability 0.8 and mutation 0.002. Selection seeds are 101/102, with a shared initialization RNG seeded 42. Same outer dates do not imply the same selected features. Exact notebook 0.8000 reproduction: NOT EXECUTED. No claim is made that the newer score improves on the historical one.

The source already sliced x[tr], y[tr], g[tr] before GA selection. Step 1 adds capture/date-disjoint assertions, a selector-input regression test, train/test dates and capture provenance, GA parameters, and saved outer-fold window predictions. Final deployment fitting remains separate and is never used for held-out replay. Invalid provenance stops replay.

Quality contract v2 changes both bandwidths to validity-aware features: reject windows below 90% usable columns, compute statistics over usable columns, and compute differences only across adjacent usable pairs. Legacy v1 artifacts are preserved and require retraining. New scores cannot replace historical scores. Per-recording audits count all-zero/nonfinite columns and invalid bursts, with null trace gaps. This is not over-the-air packet-loss measurement: sequence IDs/timestamps are absent.

The real-data audit found 1977 unusable columns across 27 stored recordings (26 originals plus the phone rehearsal copy). New 20 MHz date-held-out capture-majority results, 15 unique captures: LR accuracy 0.4666667 / balanced accuracy 0.4910714; RF and ANN each 0.6666667 / 0.6785714; GA/RF 0.9333333 / 0.9375. GA uses population 4, generations 2, mutation 0.03. These are exploratory results on only two dates. The 40 MHz capture-held-out results each score 1.0 on 11 captures; date/class confounding prevents interpreting this as date-independent generalization. Negative results are retained.

Training eligibility is checked before queueing. Old failed jobs no longer appear against a changed choice. Replay distinguishes no selected model, model ready but not run, quality-skipped windows and actual predictions. Every new prediction carries its validation protocol.

ZIP extraction rejects traversal, absolute/drive/ADS paths, symlinks, case aliases, Windows reserved devices and trailing-space/dot components. Caps: upload 2 GiB, archive 2000 entries / 4 GiB declared expansion / 256 MiB member / compression ratio 1000, plus streaming member limits.

Offline wheelhouse targets Windows x64 CPython 3.10, with 25 resolved dependencies pinned and SHA-256 verified. Run python launch_orbit.py --offline; add --check-install to verify without launching. Python itself is not bundled. A separate clean Windows machine is NOT EXECUTED. Other Python versions/architectures require matching wheels.

APK cleartext defaults off. Build-time --lan-host grants HTTP only to exact RFC1918 addresses; no CIDR wildcard exemption. WebView subresources stay on the paired origin; external links open outside it after user interaction. If the IP changes, rebuild or use the browser. Physical phone verification is NOT EXECUTED.

Step 2 onward remains pending. No simulation datasets were added and no verified live CSI, through-wall or native 802.11bf claim is made.

## Executed verification

- python -m pytest tests -q: 50 passed, 1 upstream Starlette TestClient deprecation warning, 85.78 seconds.
- npm run build: TypeScript and Vite passed; bundle-size advisory remains.
- Fresh Windows x64 CPython 3.10 virtual environment: all 25 packages installed with --no-index from SHA-256 verified wheels; pip check: No broken requirements found; Orbit dependency imports passed. Separate clean machine: NOT EXECUTED.
- Android build: v2/v3 signature verified, zipalign verified, 13 address checks passed; compiled network policy asserted default deny plus exact RFC1918 IP exceptions. Physical phone: NOT EXECUTED.
- Real-data model retraining: seven v2 models and saved outer-fold probabilities generated; legacy artifacts preserved.
- Windows offline CI job added; remote CI execution: NOT EXECUTED at this local checkpoint.
