# Experiment Log and Research Limitations

This document records the major completed analyses and their evidence status. It does not claim that all experiments were independently reproduced from a clean environment.

## CSI dataset inspection

### 20 MHz

- Source: [Zenodo record 17225694](https://zenodo.org/records/17225694), archive `20MHz.zip`.
- Archive integrity check passed in the recorded workflow; 15 MATLAB capture files and four configuration files were identified.
- Inspected MATLAB v7.3/HDF5 CSI arrays used 256 subcarriers.
- Labels: 8 no-person and 7 person-present captures across two recording dates.
- Example inspected array shape: `(256, 18634)`.

### 40 MHz

- The dataset audit in the latest model comparison contains 11 MATLAB captures with 512 subcarriers: 3 no-person and 8 person-present.
- PCAP/CSI reconciliation and window-quality checks were recorded in the broader notebook.
- **Important:** all 3 no-person captures are dated 2024-07-30, while all 8 person-present captures are dated 2024-08-01 or 2024-08-02. This makes class and date perfectly confounded in this captured subset. Capture-held-out results cannot establish date-independent generalization.

Inspection and plots establish that the files were read; they do not establish reliable sensing by themselves.

## Historical 20 MHz baseline experiments

The saved earlier notebook recorded capture-grouped stratified five-fold results:

| Model | Window accuracy | Capture accuracy | Capture F1 |
|---|---:|---:|---:|
| Logistic Regression | 0.9802 | 1.0000 | 1.0000 |
| Random Forest | 0.9771 | 1.0000 | 1.0000 |

A separate earlier two-fold leave-one-recording-date-out run reported:

| Model | Capture accuracy | Presence precision | Presence recall | Presence F1 |
|---|---:|---:|---:|---:|
| Logistic Regression | 0.4667 | 0.4615 | 0.8571 | 0.6000 |
| Random Forest | 0.7333 | 0.6364 | 1.0000 | 0.7778 |

The capture-grouped folds held out captures but not whole dates, so they are not evidence of date-independent performance. Both protocols are exploratory with only 15 captures over two dates.

## New combined bandwidth model comparison

The newest completed Colab run added an ANN/MLP to Logistic Regression and Random Forest, evaluated separately at 20 MHz and 40 MHz. Details and CSVs are in `model_comparison_20mhz_40mhz.md` and `../results/`.

| Bandwidth | Model | Capture accuracy | Balanced accuracy | Presence F1 | Validation |
|---|---|---:|---:|---:|---|
| 20 MHz | Logistic Regression | 0.4667 | 0.4911 | 0.6000 | Leave-one-date-out, two dates |
| 20 MHz | Random Forest | 0.6667 | 0.6786 | 0.7059 | Leave-one-date-out, two dates |
| 20 MHz | ANN (MLP) | 0.6667 | 0.6786 | 0.7059 | Leave-one-date-out, two dates |
| 40 MHz | Logistic Regression | 1.0000 | 1.0000 | 1.0000 | Leave-one-capture-out; date/class confounded |
| 40 MHz | Random Forest | 1.0000 | 1.0000 | 1.0000 | Leave-one-capture-out; date/class confounded |
| 40 MHz | ANN (MLP) | 1.0000 | 1.0000 | 1.0000 | Leave-one-capture-out; date/class confounded |

The new Random Forest metrics at 20 MHz differ from the historical standalone baseline above. Keep both as separate runs; do not silently replace one result table with the other. The combined comparison reports the exact current configuration/protocol. It does not show ANN outperforming Random Forest on 20 MHz. The 40 MHz 100% capture metrics are confounded and must not be presented as proof of generalization.

## DSP: FIR filtering and DFT

A 15-tap moving-average FIR filter and DFT comparisons were recorded. Earlier date-held-out capture metrics:

| Features | Model | Accuracy | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|
| Raw | Logistic Regression | 0.6667 | 0.6000 | 0.8571 | 0.7059 |
| Raw | Random Forest | 0.7333 | 0.6364 | 1.0000 | 0.7778 |
| FIR filtered | Logistic Regression | 0.6000 | 0.5556 | 0.7143 | 0.6250 |
| FIR filtered | Random Forest | 0.7333 | 0.6364 | 1.0000 | 0.7778 |

In that comparison FIR filtering did not improve Random Forest capture metrics and reduced Logistic Regression metrics.

## Soft computing: genetic algorithm and fuzzy rules

The GA feature-selection experiment selected 8 features in one outer date fold and 12 in the other.

| Method | Capture accuracy | Macro-F1 | Presence F1 | Balanced accuracy |
|---|---:|---:|---:|---:|
| Raw Random Forest | 0.7333 | 0.7222 | 0.7778 | 0.7500 |
| GA + Random Forest | 0.8000 | 0.7964 | 0.8235 | 0.8125 |
| Fuzzy rule system | 0.8000 | 0.7847 | 0.7273 | 0.7857 |

These remain preliminary estimates from 15 captures across two dates; they do not show that GA or fuzzy logic is always better.

## Cross-domain LOS/NLOS transfer

Recorded feature matrix sizes:

- NLOS/BQ: `(452, 208)`
- NLOS/PIFA: `(440, 208)`
- LOS/BQ: `(460, 208)`
- LOS/PIFA: `(465, 208)`

Twelve directional transfers were evaluated for binary presence and three-class activity. Hybrid v1 beat both comparison baselines in 1/12 presence-transfer directions and 4/12 activity-transfer directions. Selected results are in `../results/cross_domain_transfer_metrics.csv`. The hybrid was not a universal improvement, and dataset-domain results are not physical evidence of through-wall detection on consumer hardware.

## Wi-Fi AX/BF simulator measurements

A partial ns-3.40 research implementation was used to compare AX-only, BF-only and mixed AX+BF. Five valid runs were recorded per configuration.

| Configuration | Mean BF sensing latency | Mean AX throughput |
|---|---:|---:|
| AX-only | N/A (BF disabled) | 57.1744 Mbps |
| BF-only | 0.8540 ms | N/A |
| Mixed AX+BF | 8.0313 ms | 56.5456 Mbps |

Mixed AX+BF throughput was about 1.10% lower than AX-only; reported BF sensing latency was about 9.4× BF-only. MAC sensing report counts are not human-presence accuracy. The simulator is partial and does not establish standards compliance or physical 802.11bf operation. See `ax_bf_simulator_evaluation.md`.

## Current limitations and next work

- More 20 MHz recording dates and more balanced 40 MHz captures are needed, with both classes recorded on each date/environment.
- Separate capture-held-out and date/environment-held-out evaluations should be preserved and labelled.
- The notebook should be refactored into reproducible scripts after the experiment choices are finalized.
- The laptop-hosted responsive application remains to be designed and implemented.
- Live CSI capture on target hardware, native 802.11bf hardware support, and real-hardware through-wall detection remain unverified.

## Research references

- CSI dataset: https://zenodo.org/records/17225694
- SHARPax: https://github.com/francescamen/SHARPax
- Meneghello et al., *Toward Integrated Sensing and Communications in IEEE 802.11bf Wi-Fi Networks*, IEEE Communications Magazine (2023), https://doi.org/10.1109/MCOM.001.2200806
- IEEE 802.11ax: https://standards.ieee.org/ieee/802.11ax/7180/
- IEEE 802.11bf: https://standards.ieee.org/ieee/802.11bf/11574/
- ns-3 research simulator: https://github.com/idolumbantobing/IEEE_802.11bf
