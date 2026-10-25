# Experiment Log and Research Limitations

This document records the major completed analyses and the evidence supplied for this repository. Results are not claimed to have been independently reproduced from a clean environment.

## CSI dataset inspection

### 20 MHz
- Source: [Zenodo record 17225694](https://zenodo.org/records/17225694), archive `20MHz.zip`.
- Recorded inspection found 15 MATLAB captures across two recording dates: eight no-person and seven person-present captures.
- Inspected MATLAB v7.3/HDF5 CSI arrays used 256 subcarriers.
- Example inspected array shape: `(256, 18634)`.

### 40 MHz
- The latest audit has 11 MATLAB captures with 512 subcarriers: three no-person and eight person-present.
- The audit records 382 accepted windows and 20 rejected windows.
- **Critical limitation:** all three no-person captures are dated 2024-07-30; all eight person-present captures are dated 2024-08-01 or 2024-08-02. Presence label and recording date are perfectly associated in this subset. Capture-held-out scores therefore cannot establish date-independent generalization.

Inspection and plots show that files were read; they do not establish reliable sensing by themselves.

## Historical baseline and signal-processing experiments

Earlier runs are preserved as historical experiments and must not be silently merged with the newest combined comparison.

- Earlier capture-grouped five-fold 20 MHz baseline: Logistic Regression and Random Forest each reported 1.0000 capture accuracy, but those folds held out captures, not entire recording dates.
- Earlier leave-one-date-out run: Logistic Regression reported capture accuracy 0.4667 and presence F1 0.6000; Random Forest reported 0.7333 and 0.7778 respectively.
- A 15-tap moving-average FIR filter and DFT comparisons were recorded. In the earlier date-held-out comparison, FIR did not improve Random Forest capture metrics and reduced Logistic Regression metrics.
- Genetic-algorithm feature selection and fuzzy-rule experiments were run on the small 20 MHz dataset; their estimates are preliminary.

## Latest combined bandwidth model comparison

The latest supplied Colab run evaluated Logistic Regression, Random Forest and an ANN implemented as an MLP. See [the detailed report](model_comparison_20mhz_40mhz.md) and [the model metrics CSV](../results/presence_model_comparison_by_bandwidth.csv).

| Bandwidth | Model | Capture accuracy | Balanced accuracy | Presence F1 | Evaluation |
|---|---|---:|---:|---:|---|
| 20 MHz | Logistic Regression | 0.4667 | 0.4911 | 0.6000 | Leave-one-recording-date-out; only two dates |
| 20 MHz | Random Forest | 0.6667 | 0.6786 | 0.7059 | Leave-one-recording-date-out; only two dates |
| 20 MHz | ANN (MLP) | 0.6667 | 0.6786 | 0.7059 | Leave-one-recording-date-out; only two dates |
| 40 MHz | Logistic Regression | 1.0000 | 1.0000 | 1.0000 | Leave-one-capture-out; date/class confounded |
| 40 MHz | Random Forest | 1.0000 | 1.0000 | 1.0000 | Leave-one-capture-out; date/class confounded |
| 40 MHz | ANN (MLP) | 1.0000 | 1.0000 | 1.0000 | Leave-one-capture-out; date/class confounded |

### Interpretation and caution

- In the newest 20 MHz run, ANN ties Random Forest on capture accuracy and the listed presence metrics; it does not demonstrate an improvement over Random Forest.
- The current 20 MHz results differ from earlier standalone baseline results because the configurations and evaluation runs differ. Keep them distinguished by experiment and validation protocol.
- The 40 MHz 100% capture results are **exploratory and confounded**. Other captures from the same date remain in training, so a model can exploit date/environment differences. Do not present the score as robust generalization or a fair bandwidth comparison.
- The 20 MHz split contains only two recording dates; estimates are consequently very uncertain.

## Cross-domain LOS/NLOS transfer

Recorded feature matrix sizes:
- NLOS/BQ: `(452, 208)`
- NLOS/PIFA: `(440, 208)`
- LOS/BQ: `(460, 208)`
- LOS/PIFA: `(465, 208)`

Twelve directional transfers were evaluated for binary presence and three-class activity. The scale-invariant hybrid v1 beat both comparison baselines in 1/12 presence-transfer directions and 4/12 activity-transfer directions. See [selected cross-domain metrics](../results/cross_domain_transfer_metrics.csv). The hybrid was not a universal improvement; these dataset-domain results are not proof of physical through-wall performance on consumer hardware.

## Wi-Fi AX/BF simulator evaluation

A partial ns-3.40 research implementation was used for five runs per configuration. See [the dedicated simulator evaluation](ax_bf_simulator_evaluation.md), [run-level results](../results/ax_bf_simulation_runs.csv), and [summary](../results/ax_bf_simulation_summary.csv).

| Configuration | Mean BF sensing latency | Mean AX throughput |
|---|---:|---:|
| AX-only | N/A (BF disabled) | 57.1744 Mbps |
| BF-only | 0.8540 ms | N/A |
| Mixed AX+BF | 8.0313 ms | 56.5456 Mbps |

Mixed AX+BF throughput was about 1.10% below AX-only; reported BF sensing latency was about 9.4 times the BF-only value in this setup.

Limitations: MAC sensing report counts are not human-presence accuracy; BF report latency is not application inference or end-to-end latency; workloads are not identical; topology positions were not proven identical; five runs are exploratory. The partial simulator does not demonstrate standards conformance, physical 802.11bf operation, or through-wall sensing on real hardware.

## Current engineering status

- A combined analysis notebook and CSV/figure artifacts are stored in `notebooks/` and `results/`.
- The repository is not yet a one-command reproducible project from a clean checkout; data archives and simulator build dependencies remain external.
- The responsive local web app remains to be designed and implemented.
- Live CSI capture on the intended hardware, physical IEEE 802.11bf support, and real-hardware through-wall human detection remain unverified.

## Research references

- Dataset: https://zenodo.org/records/17225694
- SHARPax reference code: https://github.com/francescamen/SHARPax
- Meneghello et al., “Toward Integrated Sensing and Communications in IEEE 802.11bf Wi-Fi Networks,” *IEEE Communications Magazine* (2023), https://doi.org/10.1109/MCOM.001.2200806
- IEEE 802.11ax: https://standards.ieee.org/ieee/802.11ax/7180/
- IEEE 802.11bf: https://standards.ieee.org/ieee/802.11bf/11574/
- ns-3 research implementation: https://github.com/idolumbantobing/IEEE_802.11bf
