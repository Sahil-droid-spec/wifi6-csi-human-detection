# Research Progress: Wi-Fi CSI Presence and Activity Sensing

## Completed workstreams

| Workstream | Recorded status | Evidence and caveat |
|---|---|---|
| CSI dataset inspection | Completed for the inspected 20 MHz and 40 MHz archives | 20 MHz: 15 captures over two dates; 40 MHz: 11 captures over three dates, with date/class confounding |
| Baseline presence classification | Multiple model runs recorded | Scores depend on validation protocol; the newest three-model comparison is documented separately from historical baselines |
| DSP preprocessing | FIR filtering and DFT comparisons recorded | Filtering did not consistently improve metrics |
| Soft computing | GA feature selection and fuzzy-rule experiment recorded | Preliminary small-data estimates |
| Cross-domain transfer | LOS/NLOS and BQ/PIFA transfer evaluations recorded | Hybrid v1 is not a universal improvement |
| AX/BF simulator study | 15 valid runs, five per configuration | Partial ns-3.40 research implementation; simulator counters are not human-detection accuracy |
| Three-model bandwidth comparison | Logistic Regression, Random Forest and ANN/MLP run on 20 MHz and 40 MHz | 20 MHz: RF and ANN tie in this run; 40 MHz perfect capture scores are confounded by recording date |

## Current model comparison

See [`model_comparison_20mhz_40mhz.md`](model_comparison_20mhz_40mhz.md) and `../results/presence_model_comparison_by_bandwidth.csv` for exact metrics. The 20 MHz leave-one-date-out test has only two dates. In the 40 MHz subset, all no-person captures are dated 2024-07-30 and all person-present captures are dated 2024-08-01/02. The 40 MHz scores must be treated as exploratory and confounded.

## Planned engineering work

1. Collect more 40 MHz data so person-present and no-person cases are present across dates and environments.
2. Refactor notebook logic into reusable, documented scripts after the model and split protocol are fixed.
3. Design the responsive local web app for recorded CSI import, trace inspection, model selection and results presentation.
4. Keep recorded-data predictions, simulator output, proposed architecture and unimplemented live sensing clearly separated.
5. Verify live CSI capture and hardware compatibility independently before claiming live or through-wall sensing.
6. Prepare final report and presentation only after results and validation caveats are consolidated.

## Status that must not be overstated

- Live CSI capture using intended physical hardware is not verified.
- Physical IEEE 802.11bf operation on consumer hardware is not verified.
- Actual real-hardware through-wall human detection is not established.
- The current notebook is a research experiment, not a one-click end-to-end app.
